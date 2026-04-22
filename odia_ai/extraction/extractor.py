"""Layer 2 NER + Relational Extraction service.

Given a document passage, produces structured extraction output conforming
to the ODIA Layer 2 schema (vendors, persons, dollar_amounts, statutes,
procurement_instruments, governance_bodies, anomaly_candidates).

Backend selection:
1. Fine-tuned model (preferred; produced by odia_ai.training.lora_runner)
2. RAG with general LLM (fallback; uses existing oraculus_di_auditor.rag)
3. Pattern-matching extractor (no-LLM fallback; uses odia_ai.backref heuristics)

The service is designed so that the same function signature works regardless
of which backend is active. This allows the desktop application, CLI, and
server routes to invoke extraction uniformly.

Author: ODIA AI Team
License: MIT
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

from odia_ai.backref.extractor import (
    detect_finding_category,
    detect_severity,
    extract_dollars,
    extract_resolutions,
    extract_statutes,
    extract_vendors,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractionOutput:
    """Structured extraction result. Matches the Layer 2 schema."""

    vendors: list[str] = field(default_factory=list)
    persons: list[dict] = field(default_factory=list)
    dollar_amounts: list[dict] = field(default_factory=list)
    statutes_cited: list[str] = field(default_factory=list)
    procurement_instruments: list[dict] = field(default_factory=list)
    governance_bodies: list[dict] = field(default_factory=list)
    anomaly_candidates: list[dict] = field(default_factory=list)
    backend_used: str = ""  # "finetuned" | "rag_llm" | "pattern" | "stub"
    raw_llm_output: str | None = None

    def to_dict(self) -> dict:
        d = {
            "vendors": self.vendors,
            "persons": self.persons,
            "dollar_amounts": self.dollar_amounts,
            "statutes_cited": self.statutes_cited,
            "procurement_instruments": self.procurement_instruments,
            "governance_bodies": self.governance_bodies,
            "anomaly_candidates": self.anomaly_candidates,
        }
        if self.backend_used:
            d["_backend"] = self.backend_used
        return d


class ExtractionBackend(Protocol):
    """Protocol for Layer 2 extraction backends."""

    name: str

    def is_available(self) -> bool: ...

    def extract(self, document_text: str) -> ExtractionOutput: ...


# ------------------------------------------------------------------
# Backend 1: Pattern-based extractor (always available, no LLM required)
# ------------------------------------------------------------------

class PatternExtractionBackend:
    """Pattern-matching extractor that requires no LLM.

    Uses regex-based extraction from odia_ai.backref. Provides a baseline
    that always works, suitable for CI/testing and for running on systems
    without LLM access. Not as accurate as fine-tuned or RAG backends.
    """

    name = "pattern"

    def is_available(self) -> bool:
        return True

    def extract(self, document_text: str) -> ExtractionOutput:
        vendors = extract_vendors(document_text)
        statutes = extract_statutes(document_text)
        resolutions = extract_resolutions(document_text)
        dollars = extract_dollars(document_text)

        procurement_instruments = [
            {"type": "resolution_or_agreement", "number": r, "date": None}
            for r in resolutions
        ]
        dollar_amounts = [
            {"amount_raw": d, "vendor": vendors[0] if vendors else None, "context": ""}
            for d in dollars
        ]

        anomaly_candidates: list[dict] = []
        severity = detect_severity(document_text)
        category = detect_finding_category(document_text)
        if severity or category:
            anomaly_candidates.append({
                "category": category or "unspecified",
                "severity": severity or "MEDIUM",
                "reasoning": "Pattern-matched from document text",
            })

        # Simple anomaly heuristics:
        # - Flock mentioned but no SB 524 reference -> candidate F-3
        if any("flock" in v.lower() for v in vendors):
            has_sb524 = any("524" in s for s in statutes)
            if not has_sb524:
                anomaly_candidates.append({
                    "category": "F-3",
                    "severity": "HIGH",
                    "reasoning": "Flock ALPR mentioned without SB 524 AI disclosure reference",
                })

        # - Axon mentioned without CJIS reference -> candidate F-5
        if any("axon" in v.lower() for v in vendors):
            has_cjis = any("cjis" in s.lower() for s in statutes)
            if not has_cjis:
                anomaly_candidates.append({
                    "category": "F-5",
                    "severity": "HIGH",
                    "reasoning": "Axon mentioned without CJIS Security Addendum reference",
                })

        return ExtractionOutput(
            vendors=vendors,
            persons=[],  # pattern backend does not do person NER
            dollar_amounts=dollar_amounts,
            statutes_cited=statutes,
            procurement_instruments=procurement_instruments,
            governance_bodies=[],  # requires F-11 committee detector; not in pattern backend
            anomaly_candidates=anomaly_candidates,
            backend_used=self.name,
        )


# ------------------------------------------------------------------
# Backend 2: RAG / general-LLM extractor
# ------------------------------------------------------------------

class RAGExtractionBackend:
    """Uses a general LLM via the existing oraculus_di_auditor.rag infrastructure.

    Invokes the existing RAGService with a prompt that requests structured
    extraction in the ODIA Layer 2 schema. Works with any LLM provider the
    parent project supports: Ollama (local), OpenAI, Anthropic.
    """

    name = "rag_llm"

    def __init__(self, llm_provider: str = "ollama", llm_model: str | None = None):
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self._provider: Any = None
        self._load_error: str | None = None
        try:
            # Import oraculus_di_auditor only when this backend is instantiated
            from oraculus_di_auditor.llm_providers import get_provider  # type: ignore
            kwargs: dict[str, Any] = {}
            if llm_model:
                kwargs["model"] = llm_model
            self._provider = get_provider(llm_provider, **kwargs)
        except Exception as e:
            self._load_error = str(e)
            logger.info("RAG backend not available: %s", e)

    def is_available(self) -> bool:
        if self._provider is None:
            return False
        try:
            return bool(self._provider.is_available())
        except Exception:
            return False

    def _build_prompt(self, document_text: str) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) for extraction."""
        from odia_ai.training.dataset_builder import SYSTEM_PROMPT, EXTRACTION_INSTRUCTION  # noqa

        system = SYSTEM_PROMPT
        user = f"{EXTRACTION_INSTRUCTION}\n\n---\n{document_text}\n---\n\nJSON:"
        return system, user

    def extract(self, document_text: str) -> ExtractionOutput:
        if not self.is_available():
            # Fall through to pattern backend
            fallback = PatternExtractionBackend().extract(document_text)
            fallback.backend_used = "pattern_after_rag_unavailable"
            return fallback

        system, user = self._build_prompt(document_text)
        try:
            raw = self._provider.generate(user, context=system)
        except Exception as e:
            logger.warning("RAG LLM call failed: %s; falling back to pattern backend", e)
            fallback = PatternExtractionBackend().extract(document_text)
            fallback.backend_used = "pattern_after_rag_error"
            return fallback

        # Try to parse the response as JSON
        try:
            parsed = _extract_first_json(raw)
        except ValueError:
            logger.warning("LLM output did not contain valid JSON; falling back")
            fallback = PatternExtractionBackend().extract(document_text)
            fallback.backend_used = "pattern_after_rag_parse_error"
            fallback.raw_llm_output = raw
            return fallback

        return _parsed_to_output(parsed, backend_used=self.name, raw=raw)


# ------------------------------------------------------------------
# Backend 3: Fine-tuned model backend (preferred once trained)
# ------------------------------------------------------------------

class FinetunedExtractionBackend:
    """Uses a fine-tuned ODIA model via HuggingFace transformers.

    Loads a model previously produced by odia_ai.training.lora_runner.
    Lazy-imports transformers so that the package does not require ML
    dependencies for systems that only need the pattern backend.
    """

    name = "finetuned"

    def __init__(self, model_path: str, device: str = "auto"):
        self.model_path = model_path
        self.device = device
        self._model: Any = None
        self._tokenizer: Any = None
        self._load_error: str | None = None

    def _ensure_loaded(self) -> bool:
        if self._model is not None:
            return True
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_path, device_map=self.device
            )
            return True
        except Exception as e:
            self._load_error = str(e)
            logger.info("Fine-tuned model not loadable: %s", e)
            return False

    def is_available(self) -> bool:
        return self._ensure_loaded()

    def extract(self, document_text: str) -> ExtractionOutput:
        if not self._ensure_loaded():
            fallback = PatternExtractionBackend().extract(document_text)
            fallback.backend_used = "pattern_after_finetuned_unavailable"
            return fallback

        from odia_ai.training.dataset_builder import EXTRACTION_INSTRUCTION, SYSTEM_PROMPT

        prompt = (
            f"### System:\n{SYSTEM_PROMPT}\n\n"
            f"### Instruction:\n{EXTRACTION_INSTRUCTION}\n\n"
            f"### Input:\n{document_text}\n\n"
            f"### Response:\n"
        )
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        output_ids = self._model.generate(
            **inputs, max_new_tokens=2048, do_sample=False, temperature=0.0
        )
        raw = self._tokenizer.decode(
            output_ids[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True
        )

        try:
            parsed = _extract_first_json(raw)
        except ValueError:
            logger.warning("Fine-tuned model output did not contain valid JSON")
            fallback = PatternExtractionBackend().extract(document_text)
            fallback.backend_used = "pattern_after_finetuned_parse_error"
            fallback.raw_llm_output = raw
            return fallback

        return _parsed_to_output(parsed, backend_used=self.name, raw=raw)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _extract_first_json(text: str) -> dict:
    """Extract the first valid JSON object from a string (robust to wrapping prose)."""
    text = text.strip()
    # Fast path: entire string is JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Slow path: find first '{' and match to corresponding '}'
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    raise ValueError("No valid JSON object found in text")


def _parsed_to_output(parsed: dict, backend_used: str, raw: str | None = None) -> ExtractionOutput:
    """Convert a parsed JSON dict into an ExtractionOutput with safe defaults."""
    return ExtractionOutput(
        vendors=parsed.get("vendors") or [],
        persons=parsed.get("persons") or [],
        dollar_amounts=parsed.get("dollar_amounts") or [],
        statutes_cited=parsed.get("statutes_cited") or [],
        procurement_instruments=parsed.get("procurement_instruments") or [],
        governance_bodies=parsed.get("governance_bodies") or [],
        anomaly_candidates=parsed.get("anomaly_candidates") or [],
        backend_used=backend_used,
        raw_llm_output=raw,
    )


# ------------------------------------------------------------------
# ExtractionService (the main entry point)
# ------------------------------------------------------------------

class ExtractionService:
    """Layer 2 extraction service with automatic backend selection.

    Tries backends in order of preference and returns the first successful
    extraction. Order: fine-tuned -> RAG/LLM -> pattern.
    """

    def __init__(
        self,
        finetuned_model_path: str | None = None,
        llm_provider: str = "ollama",
        llm_model: str | None = None,
        force_backend: str | None = None,
    ):
        self._backends: list[ExtractionBackend] = []

        if finetuned_model_path:
            self._backends.append(FinetunedExtractionBackend(finetuned_model_path))
        self._backends.append(RAGExtractionBackend(llm_provider, llm_model))
        self._backends.append(PatternExtractionBackend())

        if force_backend:
            # Filter to only the named backend
            self._backends = [b for b in self._backends if b.name == force_backend]
            if not self._backends:
                raise ValueError(f"Unknown backend: {force_backend}")

    def available_backends(self) -> list[str]:
        return [b.name for b in self._backends if b.is_available()]

    def extract(self, document_text: str) -> ExtractionOutput:
        if not document_text or not document_text.strip():
            return ExtractionOutput(backend_used="stub")

        for backend in self._backends:
            if backend.is_available():
                return backend.extract(document_text)

        # Guaranteed: pattern backend is always available as fallback
        return PatternExtractionBackend().extract(document_text)
