"""Tests for the interactive RAG shell script."""

import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.rag_shell import _load_findings, _load_json_files, build_parser, run

# -- helpers -----------------------------------------------------------------


def _write_docs(tmpdir: Path) -> None:
    """Write sample JSON docs into tmpdir."""
    docs = [
        {"id": "doc-001", "text": "Budget allocates funds for infrastructure."},
        {"id": "doc-002", "text": "Vendor contract for surveillance cameras."},
    ]
    for doc in docs:
        path = tmpdir / f"{doc['id']}.json"
        path.write_text(json.dumps(doc), encoding="utf-8")


def _write_findings(path: Path) -> None:
    """Write sample findings file."""
    findings = [
        {
            "id": "fiscal:hash-001",
            "issue": "Missing hash",
            "severity": "high",
            "layer": "fiscal",
            "details": {},
        }
    ]
    path.write_text(json.dumps(findings), encoding="utf-8")


# -- test: shell loads documents ---------------------------------------------


def test_shell_loads_documents():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        _write_docs(tmpdir)

        docs = _load_json_files(tmpdir)
        assert len(docs) == 2
        assert docs[0]["id"] == "doc-001"


# -- test: shell loads findings ----------------------------------------------


def test_shell_loads_findings():
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = Path(tmpdir) / "report.json"
        _write_findings(fpath)

        findings = _load_findings(fpath)
        assert len(findings) == 1
        assert findings[0]["id"] == "fiscal:hash-001"


# -- test: shell handles 'status' command ------------------------------------


def test_shell_handles_status(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        _write_docs(tmpdir)

        args = argparse.Namespace(
            source=str(tmpdir),
            findings=None,
            provider="ollama",
            model=None,
            no_llm=True,
        )

        # Feed "status" then "quit" to stdin
        with patch("builtins.input", side_effect=["status", "quit"]):
            run(args)

        out = capsys.readouterr().out
        assert "indexed" in out or "llm_available" in out


# -- test: shell handles 'quit' command --------------------------------------


def test_shell_handles_quit(capsys):
    args = argparse.Namespace(
        source=None,
        findings=None,
        provider="ollama",
        model=None,
        no_llm=True,
    )

    with patch("builtins.input", side_effect=["quit"]):
        run(args)

    out = capsys.readouterr().out
    assert "ODIA RAG Shell" in out


# -- test: shell handles EOF -------------------------------------------------


def test_shell_handles_eof(capsys):
    args = argparse.Namespace(
        source=None,
        findings=None,
        provider="ollama",
        model=None,
        no_llm=True,
    )

    with patch("builtins.input", side_effect=EOFError):
        run(args)

    out = capsys.readouterr().out
    assert "ODIA RAG Shell" in out


# -- test: parser builds correctly -------------------------------------------


def test_build_parser():
    parser = build_parser()
    args = parser.parse_args(["--source", "data/", "--provider", "openai", "--no-llm"])
    assert args.source == "data/"
    assert args.provider == "openai"
    assert args.no_llm is True
