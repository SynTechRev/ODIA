"""Day 10: Evaluation Harness -- 7-metric scorecard + judge model + CI gate.

Computes a standardized scorecard from RAIA trace files (offline) or live RAIA
runs. Applies configurable CI thresholds and emits a PASS/FAIL gate verdict.

Seven metrics:
  1. verify_pass_rate       -- fraction of queries with halt_reason=verify_passed
  2. citation_density_mean  -- mean grounding density (valid / cited) per query
  3. citation_precision_mean-- mean fraction of valid citations in citation_validity dicts
  4. iteration_efficiency   -- 1 - (mean_iterations / max_iterations); higher is fewer iters
  5. answer_adequacy        -- HeuristicJudge (or OllamaJudge) mean answer quality (0-1)
  6. category_balance       -- fraction of query categories with >= 1 verify_passed result
  7. latency_p50_ok         -- 1 if median latency <= SLA seconds, else 0

CI gate: metric.value >= metric.threshold for all gated metrics.
Latency is informational only (gate=False).

Usage:
  from oraculus_di_auditor.eval.harness import EvalHarness
  harness = EvalHarness()
  scorecard = harness.run_from_traces(Path('data/eval/raia_day04_traces.jsonl'))
  print(scorecard.verdict)
"""

from __future__ import annotations

import ast
import json
import logging
import re
import statistics
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default CI gate thresholds
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLDS: dict[str, float] = {
    "verify_pass_rate": 0.75,
    "citation_density_mean": 0.75,
    "citation_precision_mean": 0.80,
    "iteration_efficiency": 0.40,
    "answer_adequacy": 0.50,
    "category_balance": 0.60,
    "latency_p50_ok": 0.0,  # 0.0 = informational only, not a gate
}

DEFAULT_LATENCY_SLA_SECONDS = 300.0

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class ScorecardMetric:
    name: str
    value: float
    threshold: float
    is_gate: bool  # False = informational only
    passed: bool
    unit: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class Scorecard:
    run_date: str
    trace_file: str
    query_count: int
    max_iterations: int
    metrics: list[ScorecardMetric]
    gate_passed: bool
    verdict: str  # "PASS" | "FAIL"
    failed_metrics: list[str]
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ---------------------------------------------------------------------------
# Trace parsing helpers
# ---------------------------------------------------------------------------


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _parse_citation_validity(raw: Any) -> dict[str, bool]:
    """citation_validity may be stored as a string repr of a dict."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip().startswith("{"):
        try:
            return ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            pass
    return {}


def load_traces(traces_path: Path) -> list[dict]:
    """Load RAIA trace JSONL file. Returns list of trace dicts."""
    lines = traces_path.read_text(encoding="utf-8").splitlines()
    traces = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                traces.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("Skipping malformed trace line")
    return traces


# ---------------------------------------------------------------------------
# Metric 1: verify_pass_rate
# ---------------------------------------------------------------------------


def compute_verify_pass_rate(traces: list[dict]) -> tuple[float, dict]:
    passed = sum(1 for t in traces if t.get("halt_reason") == "verify_passed")
    total = len(traces)
    by_category: dict[str, dict] = {}
    for t in traces:
        cat = t.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = {"passed": 0, "total": 0}
        by_category[cat]["total"] += 1
        if t.get("halt_reason") == "verify_passed":
            by_category[cat]["passed"] += 1
    return (passed / total if total else 0.0), {
        "by_category": by_category,
        "passed": passed,
        "total": total,
    }


# ---------------------------------------------------------------------------
# Metric 2: citation_density_mean
# ---------------------------------------------------------------------------


def compute_citation_density_mean(traces: list[dict]) -> tuple[float, dict]:
    densities = [_safe_float(t.get("final_confidence", 0.0)) for t in traces]
    mean_val = statistics.mean(densities) if densities else 0.0
    verify_passed_mean = (
        statistics.mean(
            d
            for t, d in zip(traces, densities, strict=False)
            if t.get("halt_reason") == "verify_passed"
        )
        if any(t.get("halt_reason") == "verify_passed" for t in traces)
        else 0.0
    )
    return mean_val, {
        "all_mean": mean_val,
        "verify_passed_mean": verify_passed_mean,
        "per_query": list(densities),
    }


# ---------------------------------------------------------------------------
# Metric 3: citation_precision_mean
# ---------------------------------------------------------------------------


def compute_citation_precision_mean(traces: list[dict]) -> tuple[float, dict]:
    precisions = []
    per_query = []
    for t in traces:
        cv = _parse_citation_validity(t.get("citation_validity", {}))
        if cv:
            precision = sum(1 for v in cv.values() if v) / len(cv)
        else:
            # No citations: precision is 0 if max_iterations, undefined if verify_passed
            precision = 1.0 if t.get("halt_reason") == "verify_passed" else 0.0
        precisions.append(precision)
        per_query.append(
            {
                "query_id": t.get("query_id"),
                "precision": precision,
                "citation_count": len(cv),
            }
        )
    mean_val = statistics.mean(precisions) if precisions else 0.0
    return mean_val, {"per_query": per_query}


# ---------------------------------------------------------------------------
# Metric 4: iteration_efficiency
# ---------------------------------------------------------------------------


def compute_iteration_efficiency(
    traces: list[dict], max_iterations: int = 3
) -> tuple[float, dict]:
    """1 - (mean_iterations / max_iterations). Higher means fewer iterations needed."""
    iters = [_safe_int(t.get("iterations", max_iterations)) for t in traces]
    mean_iters = statistics.mean(iters) if iters else float(max_iterations)
    efficiency = 1.0 - (mean_iters / max_iterations)
    efficiency = max(0.0, min(1.0, efficiency))
    return efficiency, {
        "mean_iterations": mean_iters,
        "max_iterations": max_iterations,
        "per_query": [
            {"query_id": t.get("query_id"), "iterations": i}
            for t, i in zip(traces, iters, strict=False)
        ],
    }


# ---------------------------------------------------------------------------
# Metric 5: answer_adequacy (judge model)
# ---------------------------------------------------------------------------


class HeuristicJudge:
    """Rule-based answer quality judge. No live model required.

    Scoring rubric (each criterion contributes 0.2):
      - Has at least one (doc_id:...) citation
      - Answer length >= 150 characters
      - No boilerplate refusal phrases
      - Contains at least one legal statute or section reference
      - No leaked prompt artifacts (PASSAGES: / QUERY: / Rules:)
    """

    _CITATION_RE = re.compile(r"\(doc_id:[0-9a-f]{64}\)")
    _BOILERPLATE = re.compile(
        r"\b(I cannot|I don't have|As an AI|I'm unable to|I apologize)\b",
        re.IGNORECASE,
    )
    _STATUTE_RE = re.compile(
        r"\b(Cal\.|42 U\.S\.C\.|34 USC|Gov\. Code|Pen\. Code|CFR|U\.S\.C\.|§)",
        re.IGNORECASE,
    )
    _ARTIFACT_RE = re.compile(r"(PASSAGES:|QUERY:|Rules:\s|FINDING:)", re.IGNORECASE)

    def score(self, query: str, answer: str) -> float:
        score = 0.0
        if self._CITATION_RE.search(answer):
            score += 0.2
        if len(answer) >= 150:
            score += 0.2
        if not self._BOILERPLATE.search(answer):
            score += 0.2
        if self._STATUTE_RE.search(answer):
            score += 0.2
        if not self._ARTIFACT_RE.search(answer):
            score += 0.2
        return round(score, 2)


class OllamaJudge:
    """LLM-as-judge using odia-v2 / Ollama REST API.

    Falls back to HeuristicJudge if Ollama is unavailable or returns an error.
    """

    def __init__(
        self, model: str = "odia-v2", base_url: str = "http://localhost:11434"
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._fallback = HeuristicJudge()

    def _is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self._base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except Exception:
            return False

    def score(self, query: str, answer: str) -> float:
        if not self._is_available():
            return self._fallback.score(query, answer)
        prompt = (
            f"Rate the following answer to an audit query on a scale from 0 to 10.\n\n"
            f"QUERY: {query[:300]}\n\n"
            f"ANSWER: {answer[:600]}\n\n"
            f"Criteria: Does the answer cite specific documents? Is it factual and non-evasive? "
            f"Does it address the audit query directly?\n\n"
            f"Respond with ONLY a single integer from 0 to 10."
        )
        payload = json.dumps(
            {"model": self._model, "prompt": prompt, "stream": False}
        ).encode()
        try:
            req = urllib.request.Request(
                f"{self._base_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
            raw = result.get("response", "").strip()
            match = re.search(r"\b([0-9]|10)\b", raw)
            if match:
                return round(int(match.group(1)) / 10.0, 2)
        except Exception:
            logger.debug("OllamaJudge request failed, using heuristic fallback")
        return self._fallback.score(query, answer)


def compute_answer_adequacy(
    traces: list[dict],
    judge: HeuristicJudge | OllamaJudge | None = None,
) -> tuple[float, dict]:
    if judge is None:
        judge = HeuristicJudge()
    scores = []
    per_query = []
    for t in traces:
        query = t.get("query", "")
        answer = t.get("final_answer", "")
        s = judge.score(query, answer)
        scores.append(s)
        per_query.append(
            {
                "query_id": t.get("query_id"),
                "score": s,
                "halt_reason": t.get("halt_reason"),
            }
        )
    mean_val = statistics.mean(scores) if scores else 0.0
    return mean_val, {
        "judge_type": type(judge).__name__,
        "per_query": per_query,
    }


# ---------------------------------------------------------------------------
# Metric 6: category_balance
# ---------------------------------------------------------------------------


def compute_category_balance(traces: list[dict]) -> tuple[float, dict]:
    """Fraction of query categories with >= 1 verify_passed result."""
    categories = {t.get("category", "unknown") for t in traces}
    passed_categories = {
        t.get("category", "unknown")
        for t in traces
        if t.get("halt_reason") == "verify_passed"
    }
    if not categories:
        return 0.0, {}
    fraction = len(passed_categories) / len(categories)
    return fraction, {
        "total_categories": len(categories),
        "passed_categories": len(passed_categories),
        "categories": sorted(categories),
        "passed_category_names": sorted(passed_categories),
    }


# ---------------------------------------------------------------------------
# Metric 7: latency_p50_ok
# ---------------------------------------------------------------------------


def compute_latency_p50_ok(
    traces: list[dict],
    sla_seconds: float = DEFAULT_LATENCY_SLA_SECONDS,
) -> tuple[float, dict]:
    latencies = [_safe_float(t.get("latency_sec", 0.0)) for t in traces]
    valid = [lat for lat in latencies if lat > 0]
    if not valid:
        return 0.0, {"p50": None, "sla_seconds": sla_seconds}
    p50 = statistics.median(valid)
    ok = 1.0 if p50 <= sla_seconds else 0.0
    return ok, {
        "p50_seconds": round(p50, 1),
        "mean_seconds": round(statistics.mean(valid), 1),
        "sla_seconds": sla_seconds,
        "per_query": [
            {"query_id": t.get("query_id"), "latency_sec": lat}
            for t, lat in zip(traces, latencies, strict=False)
        ],
    }


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------


class EvalHarness:
    """RAIA evaluation harness: 7-metric scorecard + CI gate.

    Supports offline mode (from pre-existing trace JSONL) and live mode (requires
    a running RAIA graph). Day 10 uses offline mode against raia_day04_traces.jsonl.
    """

    def __init__(
        self,
        thresholds: dict[str, float] | None = None,
        latency_sla: float = DEFAULT_LATENCY_SLA_SECONDS,
        judge: HeuristicJudge | OllamaJudge | None = None,
        max_iterations: int = 3,
    ) -> None:
        self._thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
        self._latency_sla = latency_sla
        self._judge = judge or HeuristicJudge()
        self._max_iterations = max_iterations

    def run_from_traces(
        self,
        traces_path: Path,
    ) -> Scorecard:
        """Compute scorecard from a RAIA traces JSONL file."""
        traces = load_traces(traces_path)
        if not traces:
            raise ValueError(f"No traces found in {traces_path}")

        return self._compute_scorecard(traces, str(traces_path))

    def _compute_scorecard(self, traces: list[dict], trace_source: str) -> Scorecard:
        metrics: list[ScorecardMetric] = []

        # 1: verify_pass_rate
        v, d = compute_verify_pass_rate(traces)
        t1 = self._thresholds["verify_pass_rate"]
        metrics.append(
            ScorecardMetric(
                name="verify_pass_rate",
                value=round(v, 4),
                threshold=t1,
                is_gate=True,
                passed=v >= t1,
                unit="fraction",
                details=d,
            )
        )

        # 2: citation_density_mean
        v, d = compute_citation_density_mean(traces)
        t2 = self._thresholds["citation_density_mean"]
        metrics.append(
            ScorecardMetric(
                name="citation_density_mean",
                value=round(v, 4),
                threshold=t2,
                is_gate=True,
                passed=v >= t2,
                unit="fraction",
                details=d,
            )
        )

        # 3: citation_precision_mean
        v, d = compute_citation_precision_mean(traces)
        t3 = self._thresholds["citation_precision_mean"]
        metrics.append(
            ScorecardMetric(
                name="citation_precision_mean",
                value=round(v, 4),
                threshold=t3,
                is_gate=True,
                passed=v >= t3,
                unit="fraction",
                details=d,
            )
        )

        # 4: iteration_efficiency
        v, d = compute_iteration_efficiency(traces, self._max_iterations)
        t4 = self._thresholds["iteration_efficiency"]
        metrics.append(
            ScorecardMetric(
                name="iteration_efficiency",
                value=round(v, 4),
                threshold=t4,
                is_gate=True,
                passed=v >= t4,
                unit="0=worst 1=best",
                details=d,
            )
        )

        # 5: answer_adequacy
        v, d = compute_answer_adequacy(traces, self._judge)
        t5 = self._thresholds["answer_adequacy"]
        metrics.append(
            ScorecardMetric(
                name="answer_adequacy",
                value=round(v, 4),
                threshold=t5,
                is_gate=True,
                passed=v >= t5,
                unit="fraction",
                details=d,
            )
        )

        # 6: category_balance
        v, d = compute_category_balance(traces)
        t6 = self._thresholds["category_balance"]
        metrics.append(
            ScorecardMetric(
                name="category_balance",
                value=round(v, 4),
                threshold=t6,
                is_gate=True,
                passed=v >= t6,
                unit="fraction",
                details=d,
            )
        )

        # 7: latency_p50_ok (informational)
        v, d = compute_latency_p50_ok(traces, self._latency_sla)
        t7 = self._thresholds["latency_p50_ok"]
        metrics.append(
            ScorecardMetric(
                name="latency_p50_ok",
                value=round(v, 4),
                threshold=t7,
                is_gate=False,
                passed=v >= t7,
                unit="1=ok 0=exceeds_sla",
                details=d,
            )
        )

        # Gate: all gated metrics must pass
        failed = [m.name for m in metrics if m.is_gate and not m.passed]
        gate_passed = len(failed) == 0
        verdict = "PASS" if gate_passed else "FAIL"

        return Scorecard(
            run_date=datetime.now(UTC).isoformat(),
            trace_file=trace_source,
            query_count=len(traces),
            max_iterations=self._max_iterations,
            metrics=metrics,
            gate_passed=gate_passed,
            verdict=verdict,
            failed_metrics=failed,
            details={
                "judge_type": type(self._judge).__name__,
                "latency_sla_seconds": self._latency_sla,
                "thresholds_applied": {m.name: m.threshold for m in metrics},
            },
        )

    def save_scorecard(self, scorecard: Scorecard, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(scorecard.to_dict(), fh, indent=2, default=str)
        logger.info(
            "Scorecard saved to %s -- verdict: %s", output_path, scorecard.verdict
        )

    def print_scorecard(self, scorecard: Scorecard) -> None:
        width = 62
        print("=" * width)
        print(f"  ODIA RAIA Evaluation Scorecard  |  {scorecard.verdict}")
        print("=" * width)
        print(f"  Run date   : {scorecard.run_date}")
        print(f"  Traces     : {scorecard.trace_file}")
        print(f"  Queries    : {scorecard.query_count}")
        print(f"  Gate       : {'PASS' if scorecard.gate_passed else 'FAIL'}")
        if scorecard.failed_metrics:
            print(f"  Failed     : {', '.join(scorecard.failed_metrics)}")
        print("-" * width)
        print(f"  {'Metric':<28} {'Value':>8} {'Threshold':>10} {'Gate':>6} {'':>4}")
        print("-" * width)
        for m in scorecard.metrics:
            gate_str = "gate" if m.is_gate else "info"
            status = "OK" if m.passed else "FAIL"
            print(
                f"  {m.name:<28} {m.value:>8.4f} {m.threshold:>10.4f} {gate_str:>6} {status:>4}"
            )
        print("=" * width)
