"""Interactive RAG query shell for ODIA.

Usage:
    python scripts/rag_shell.py --source data/sources/
    python scripts/rag_shell.py --source data/sources/ --provider ollama
    python scripts/rag_shell.py --source data/sources/ --no-llm
    python scripts/rag_shell.py --findings audit_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))


def _load_json_files(directory: Path) -> list[dict]:
    """Load all .json files from a directory as document dicts."""
    docs: list[dict] = []
    if not directory.is_dir():
        return docs
    for p in sorted(directory.glob("*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                docs.extend(data)
            elif isinstance(data, dict):
                if "id" not in data:
                    data["id"] = p.stem
                docs.append(data)
        except Exception as exc:
            print(f"[WARN] Skipping {p.name}: {exc}")
    return docs


def _load_text_files(directory: Path) -> list[dict]:
    """Load .txt files from a directory as simple document dicts."""
    docs: list[dict] = []
    if not directory.is_dir():
        return docs
    for p in sorted(directory.glob("*.txt")):
        try:
            text = p.read_text(encoding="utf-8")
            docs.append({"id": p.stem, "text": text})
        except Exception as exc:
            print(f"[WARN] Skipping {p.name}: {exc}")
    return docs


def _load_findings(path: Path) -> list[dict]:
    """Load findings from a JSON audit report."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"[WARN] Could not load findings from {path}: {exc}")
        return []

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("findings", data.get("anomalies", []))
    return []


def _print_response(resp, no_llm: bool = False) -> None:
    """Pretty-print a RAGResponse or query_without_llm dict."""
    if isinstance(resp, dict):
        print(f"\nQuery type: {resp.get('query_type', '?')}")
        preview = resp.get("context_preview", "")
        if preview:
            print(f"\nContext preview:\n{preview}")
        sources = resp.get("retrieved_sources", [])
        if sources:
            print(f"\nSources ({len(sources)}):")
            for i, s in enumerate(sources, 1):
                sid = getattr(s, "source_id", s.get("source_id", "?"))
                stype = getattr(s, "source_type", s.get("source_type", "?"))
                score = getattr(s, "score", s.get("score", 0))
                print(f"  [{i}] {sid} ({stype}, score: {score:.2f})")
        print(f"\n{resp.get('message', '')}")
        return

    # RAGResponse object
    print(f"\nAnswer: {resp.answer}\n")
    if resp.sources:
        print(f"Sources ({len(resp.sources)}):")
        for i, s in enumerate(resp.sources, 1):
            print(f"  [{i}] {s.source_id}" f" ({s.source_type}, score: {s.score:.2f})")
    print()


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the RAG shell."""
    parser = argparse.ArgumentParser(
        description="ODIA interactive RAG query shell",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Directory containing source documents (JSON/TXT)",
    )
    parser.add_argument(
        "--findings",
        type=str,
        default=None,
        help="Path to a JSON file containing audit findings",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="ollama",
        help="LLM provider: openai, anthropic, ollama (default: ollama)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM model name",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Retrieval-only mode (no LLM calls)",
    )
    return parser


def _load_data(svc, args):
    """Load documents and findings into the service from CLI args."""
    doc_count = 0
    finding_count = 0

    source_dir = getattr(args, "source", None)
    if source_dir:
        source_path = Path(source_dir)
        docs = _load_json_files(source_path) + _load_text_files(source_path)
        if docs:
            counts = svc.load_corpus(documents=docs)
            doc_count = counts["documents"]

    findings_path = getattr(args, "findings", None)
    if findings_path:
        findings = _load_findings(Path(findings_path))
        if findings:
            counts = svc.load_corpus(findings=findings)
            finding_count = counts["findings"]

    return doc_count, finding_count


def _repl_loop(svc, use_llm: bool) -> None:
    """Run the interactive read-eval-print loop."""
    while True:
        try:
            query = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit"):
            break
        if query.lower() == "status":
            for k, v in svc.get_status().items():
                print(f"  {k}: {v}")
            print()
            continue

        if use_llm:
            _print_response(svc.query(query))
        else:
            _print_response(svc.query_without_llm(query), no_llm=True)


def run(args: argparse.Namespace | None = None) -> None:
    """Main entry point for the RAG shell."""
    from oraculus_di_auditor.rag import RAGService

    if args is None:
        args = build_parser().parse_args()

    svc = RAGService(
        llm_provider=getattr(args, "provider", "ollama"),
        llm_model=getattr(args, "model", None),
    )

    doc_count, finding_count = _load_data(svc, args)

    no_llm = getattr(args, "no_llm", False)
    status = svc.get_status()
    use_llm = not no_llm and status["llm_available"]
    llm_label = status["llm_provider"] if use_llm else "no LLM"

    print(
        f"ODIA RAG Shell"
        f" ({doc_count} documents indexed,"
        f" {finding_count} findings,"
        f" {llm_label} provider)"
    )
    print("Type 'quit' to exit, 'status' for system status.\n")

    _repl_loop(svc, use_llm)


if __name__ == "__main__":
    run()
