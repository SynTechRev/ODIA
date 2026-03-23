"""odia — Command-line interface for O.D.I.A.

Usage:
    odia --help              Show all commands
    odia demo                Run demo audit on data/demo/
    odia setup               Launch interactive jurisdiction wizard
    odia audit --source DIR  Run audit on documents in DIR
    odia serve               Start API server (+ frontend if available)
    odia fetch               Retrieve documents from Legistar
    odia query TEXT          Natural-language RAG query
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Bootstrap: ensure src/ is on the path when run directly
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

_SCRIPTS = _REPO_ROOT / "scripts"
_DATA_DEMO = _REPO_ROOT / "data" / "demo"


# ---------------------------------------------------------------------------
# Sub-command implementations
# ---------------------------------------------------------------------------


def _cmd_demo(args: argparse.Namespace) -> int:
    """Run audit on the built-in demo dataset."""
    if not _DATA_DEMO.exists():
        print(
            f"[ERROR] Demo dataset not found at {_DATA_DEMO}.\n"
            "Run: git clone https://github.com/SynTechRev/ODIA and ensure data/demo/ exists."
        )
        return 1

    output_dir = _REPO_ROOT / "reports" / "demo"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Running demo audit: {_DATA_DEMO} -> {output_dir}")

    script = _SCRIPTS / "run_audit.py"
    if script.exists():
        return subprocess.call(
            [sys.executable, str(script), "--source", str(_DATA_DEMO), "--output", str(output_dir)],
            cwd=str(_REPO_ROOT),
        )

    # Fallback: inline audit
    try:
        from oraculus_di_auditor.analysis import analyze_document
        from oraculus_di_auditor.ingestion.document_engine import ingest_folder

        docs = ingest_folder(str(_DATA_DEMO))
        total_findings = 0
        for doc in docs:
            result = analyze_document(doc)
            findings = result.get("findings", {})
            count = sum(len(v) for v in findings.values() if isinstance(v, list))
            total_findings += count
            print(f"  {doc.get('document_id', 'unknown')}: {count} findings")
        print(f"\nTotal findings: {total_findings}")
        print(f"Reports written to: {output_dir}")
        return 0
    except Exception as exc:
        print(f"[ERROR] Demo audit failed: {exc}")
        return 1


def _cmd_setup(args: argparse.Namespace) -> int:
    """Launch the interactive jurisdiction configuration wizard."""
    script = _SCRIPTS / "setup_jurisdiction.py"
    if not script.exists():
        print("[ERROR] setup_jurisdiction.py not found.")
        return 1
    return subprocess.call([sys.executable, str(script)], cwd=str(_REPO_ROOT))


def _cmd_audit(args: argparse.Namespace) -> int:
    """Run audit on documents in --source directory."""
    source = Path(args.source)
    if not source.exists():
        print(f"[ERROR] Source directory not found: {source}")
        return 1

    output = Path(args.output) if args.output else _REPO_ROOT / "reports" / source.name
    output.mkdir(parents=True, exist_ok=True)

    script = _SCRIPTS / "run_audit.py"
    if script.exists():
        cmd = [sys.executable, str(script), "--source", str(source), "--output", str(output)]
        if args.config_dir:
            cmd += ["--config-dir", args.config_dir]
        return subprocess.call(cmd, cwd=str(_REPO_ROOT))

    print(f"[ERROR] run_audit.py not found at {script}")
    return 1


def _cmd_serve(args: argparse.Namespace) -> int:
    """Start the API server (and frontend if built)."""
    try:
        import uvicorn  # type: ignore[import]
    except ImportError:
        print("[ERROR] uvicorn not installed. Run: pip install uvicorn")
        return 1

    host = args.host or "127.0.0.1"
    port = int(args.port or 8000)
    print(f"Starting O.D.I.A. API server on http://{host}:{port}")
    print("  API docs: http://{}:{}/docs".format(host, port))
    print("  Press Ctrl+C to stop.")
    uvicorn.run(
        "oraculus_di_auditor.interface.api:app",
        host=host,
        port=port,
        reload=args.reload,
    )
    return 0


def _cmd_fetch(args: argparse.Namespace) -> int:
    """Retrieve documents from Legistar."""
    script = _SCRIPTS / "fetch_documents.py"
    if not script.exists():
        print("[ERROR] fetch_documents.py not found.")
        return 1

    cmd = [sys.executable, str(script)]
    if args.city:
        cmd += ["--city", args.city]
    if args.state:
        cmd += ["--state", args.state]
    if args.start:
        cmd += ["--start", args.start]
    if args.end:
        cmd += ["--end", args.end]
    if args.output:
        cmd += ["--output", args.output]
    return subprocess.call(cmd, cwd=str(_REPO_ROOT))


def _cmd_query(args: argparse.Namespace) -> int:
    """Run a natural-language RAG query."""
    script = _SCRIPTS / "rag_query.py"
    if script.exists():
        cmd = [sys.executable, str(script), "--query", args.query]
        return subprocess.call(cmd, cwd=str(_REPO_ROOT))

    # Fallback: inline query
    try:
        from oraculus_di_auditor.rag import OracRAG

        rag = OracRAG()
        result = rag.query(args.query)
        print(result)
        return 0
    except Exception as exc:
        print(f"[ERROR] RAG query failed: {exc}")
        return 1


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odia",
        description=(
            "O.D.I.A. — Oraculus Decimus Intellect Analyst\n"
            "Civic accountability intelligence platform."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  odia demo                          # Quick demo with built-in dataset\n"
            "  odia audit --source data/docs/     # Audit your own documents\n"
            "  odia serve                         # Start web interface\n"
            "  odia fetch --city visalia --state CA --start 2024-01-01 --end 2024-12-31\n"
            "  odia query \"What contracts exceed 100k?\"\n"
        ),
    )
    parser.add_argument("--version", action="version", version="odia 2.1.0")

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # demo
    sub.add_parser("demo", help="Run demo audit on built-in dataset (data/demo/)")

    # setup
    sub.add_parser("setup", help="Interactive jurisdiction configuration wizard")

    # audit
    audit_p = sub.add_parser("audit", help="Run audit on documents in a directory")
    audit_p.add_argument("--source", required=True, metavar="DIR", help="Directory of documents to audit")
    audit_p.add_argument("--output", metavar="DIR", help="Output directory for reports (default: reports/<source_name>/)")
    audit_p.add_argument("--config-dir", default="config", metavar="DIR", help="Config directory (default: config/)")

    # serve
    serve_p = sub.add_parser("serve", help="Start the O.D.I.A. API server")
    serve_p.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    serve_p.add_argument("--port", default="8000", help="Bind port (default: 8000)")
    serve_p.add_argument("--reload", action="store_true", help="Enable auto-reload (development mode)")

    # fetch
    fetch_p = sub.add_parser("fetch", help="Retrieve documents from Legistar API")
    fetch_p.add_argument("--city", metavar="NAME", help="City name or Legistar client ID")
    fetch_p.add_argument("--state", metavar="ST", help="State abbreviation (e.g. CA)")
    fetch_p.add_argument("--start", metavar="DATE", help="Start date YYYY-MM-DD")
    fetch_p.add_argument("--end", metavar="DATE", help="End date YYYY-MM-DD")
    fetch_p.add_argument("--output", metavar="DIR", default="data/retrieved/", help="Output directory")

    # query
    query_p = sub.add_parser("query", help="Natural-language query over ingested corpus (RAG)")
    query_p.add_argument("query", metavar="QUERY", help="Question to ask")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "demo": _cmd_demo,
        "setup": _cmd_setup,
        "audit": _cmd_audit,
        "serve": _cmd_serve,
        "fetch": _cmd_fetch,
        "query": _cmd_query,
    }

    if args.command is None:
        parser.print_help()
        return 0

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
