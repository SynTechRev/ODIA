#!/usr/bin/env python3
"""A.R.C.A.D.E. Layer 13 -- AI Defense (Garak red-team probes).

Runs Garak adversarial probes against the odia-v1 model to audit for
OWASP LLM Top 10 vulnerabilities before odia-v2 training begins.

Probes run (garak 0.17.0 module names):
  - promptinject    (LLM01) -- direct prompt injection hijack
  - latentinjection (LLM01) -- indirect injection via retrieved RAG context
  - leakreplay      (LLM06) -- training data replay / PII leakage
  - packagehallucination (LLM09) -- fabricated package/reference names
  - web_injection   (LLM02) -- XSS / markdown exfiltration payloads
  - dan             (LLM01 variant) -- DAN jailbreak attempts

Results saved to: data/saber/ai-defense/garak-odia-v1-{date}.json

Usage:
    # Install (run once):
    .venv\\Scripts\\pip install garak

    # Run probes (requires Ollama running with odia-v1 loaded):
    python scripts/arcade_l13_garak.py

    # Quick smoke-test (1 probe only, fast):
    python scripts/arcade_l13_garak.py --quick
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

_OUT_DIR = Path(__file__).parent.parent / "data" / "saber" / "ai-defense"
_MODEL = "odia-v1"
_PROVIDER = "ollama"

# Ordered by OWASP LLM Top 10 risk priority for a civic RAG pipeline.
# Names are garak 0.17.0 module names (verified with --list_probes 2026-10-04).
_PROBE_SETS = [
    "promptinject",  # LLM01 -- direct hijack at a RAG query endpoint
    "latentinjection",  # LLM01 -- indirect injection via retrieved documents
    "leakreplay",  # LLM06 -- training-data replay / PII leakage
    "packagehallucination",  # LLM09 -- hallucinated legal references / fabrication
    "web_injection",  # LLM02 -- XSS / markdown exfil payloads in frontend
    "dan",  # LLM01 variant -- DAN jailbreak attempts
]

_QUICK_PROBE = ["promptinject"]


def run_garak(probes: list[str], out_path: Path) -> int:
    cmd = [
        sys.executable,
        "-m",
        "garak",
        "--model_type",
        _PROVIDER,
        "--model_name",
        _MODEL,
        "--probes",
        ",".join(probes),
        "--report_prefix",
        str(out_path),
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="A.R.C.A.D.E. Layer 13 Garak probes")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run prompt injection probe only (fast smoke test)",
    )
    args = parser.parse_args()

    # Verify garak is installed
    try:
        import importlib.util

        if importlib.util.find_spec("garak") is None:
            raise ImportError
    except ImportError:
        print("garak not installed. Run: .venv\\Scripts\\pip install garak")
        sys.exit(1)

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d")
    out_path = _OUT_DIR / f"garak-odia-v1-{ts}"

    probes = _QUICK_PROBE if args.quick else _PROBE_SETS
    print(f"Probes: {probes}")
    print(f"Output: {out_path}.*")

    rc = run_garak(probes, out_path)

    # Write a summary record
    summary = {
        "run_at": datetime.now(UTC).isoformat(),
        "model": _MODEL,
        "provider": _PROVIDER,
        "probes": probes,
        "exit_code": rc,
        "output_prefix": str(out_path),
    }
    summary_path = _OUT_DIR / f"garak-summary-{ts}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Summary written: {summary_path}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
