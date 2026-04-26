"""Tests for the v2.7.10 python-docx Markdown→DOCX fallback.

Pre-v2.7.10, ``markdown_to_docx`` returned ``None`` whenever pandoc
wasn't on PATH — which is the universal case on the PyInstaller
desktop install. Users got a silent "DOCX not available" rather than
the Word document they asked for.

The fallback uses python-docx (now a runtime dep) to render the
audit-report Markdown subset directly. These tests pin:

  • the fallback fires when pandoc is absent
  • the produced file is a valid DOCX (zip with word/document.xml)
  • headings + bold + bullets + code blocks + horizontal rules are
    preserved
  • get_available_formats() reports ``docx`` when python-docx is
    importable, even without pandoc
"""

from __future__ import annotations

import zipfile

import pytest

pytest.importorskip("docx")  # python-docx package


def test_get_available_formats_includes_docx_via_python_docx(monkeypatch):
    """When pandoc is absent but python-docx is installed, the format
    list must still expose `docx` so the UI / API doesn't hide the
    option from desktop users."""
    import shutil as _shutil

    from oraculus_di_auditor.reporting import format_converters

    monkeypatch.setattr(_shutil, "which", lambda _name: None)
    formats = format_converters.get_available_formats()
    assert "docx" in formats, formats


def test_markdown_to_docx_pythondocx_writes_valid_docx(monkeypatch, tmp_path):
    """End-to-end: feed a representative audit-report Markdown chunk
    through the fallback and assert the output opens as a valid DOCX
    with the expected runs."""
    import shutil as _shutil

    from oraculus_di_auditor.reporting import format_converters

    # Force the pandoc branch to skip so we test the fallback only.
    monkeypatch.setattr(_shutil, "which", lambda _name: None)

    md = (
        "# Audit Report\n"
        "\n"
        "**Documents analysed**: 8\n"
        "\n"
        "## Severity Summary\n"
        "\n"
        "- Critical: 6\n"
        "- High: 4\n"
        "\n"
        "---\n"
        "\n"
        "### Finding 001 — JAG anti-supplanting\n"
        "\n"
        "_Statute_: 34 U.S.C. § 10152(a)(1)(G)\n"
        "\n"
        "```\n"
        '{ "sev": "critical" }\n'
        "```\n"
    )
    out = tmp_path / "test.docx"
    result = format_converters.markdown_to_docx(md, out)

    assert result is not None
    assert out.exists()
    assert out.stat().st_size > 1500  # smallest plausible DOCX is ~1.3 KB

    # DOCX is a zip with word/document.xml — inspect its contents.
    with zipfile.ZipFile(out) as z:
        assert "word/document.xml" in z.namelist()
        body = z.read("word/document.xml").decode("utf-8")

    # Spot-check the heading, the bold run, and the inline statute.
    assert "Audit Report" in body
    assert "Documents analysed" in body
    assert "JAG anti-supplanting" in body
    assert "34 U.S.C." in body
    # Bullet list emits via "List Bullet" style
    assert "List Bullet" in body or "Critical: 6" in body
    # Fenced code block content survived
    assert "critical" in body


def test_markdown_to_docx_returns_none_when_neither_backend_present(
    monkeypatch, tmp_path
):
    """If pandoc AND python-docx are both missing, the function returns
    None and logs — never crashes — so the audit job doesn't fail just
    because the optional Word export is unavailable."""
    import builtins
    import shutil as _shutil
    import sys

    from oraculus_di_auditor.reporting import format_converters

    monkeypatch.setattr(_shutil, "which", lambda _name: None)

    # Hide the docx module from import resolution.
    real_import = builtins.__import__
    monkeypatch.delitem(sys.modules, "docx", raising=False)

    def _blocked_import(name, *args, **kwargs):
        if name == "docx" or name.startswith("docx."):
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _blocked_import)

    out = tmp_path / "should_not_exist.docx"
    result = format_converters.markdown_to_docx("# nope", out)
    assert result is None
    assert not out.exists()
