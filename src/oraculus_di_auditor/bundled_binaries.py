"""Runtime configuration for PyInstaller-bundled external binaries.

When running under a PyInstaller bundle (Windows desktop installer),
Tesseract OCR and the Poppler PDF utilities are extracted alongside
the executable. This module discovers them at startup and configures
pytesseract + pdf2image to use those bundled copies.

When running under a normal Python install (not frozen), this module
is a no-op and the libraries use whatever is on the system PATH.

Usage:
    from oraculus_di_auditor.bundled_binaries import configure_bundled_binaries
    status = configure_bundled_binaries()
    # status -> {"tesseract": bool, "poppler": bool, "frozen": bool}

Safe to call in every environment; every branch is guarded so startup
never crashes on a missing tool or an unusable import.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _bundle_dir() -> Path | None:
    """Return the PyInstaller extraction directory, or None if not frozen."""
    if not getattr(sys, "frozen", False):
        return None
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(sys.executable).parent


def configure_bundled_binaries() -> dict[str, bool]:
    """Wire pytesseract and pdf2image to the bundled binaries, if any.

    Returns a status dict reporting which OCR tooling was detected and
    configured. Caller can log this at startup for observability.
    """
    status: dict[str, bool] = {"tesseract": False, "poppler": False, "frozen": False}
    bundle = _bundle_dir()
    if bundle is None:
        logger.debug("Not running under PyInstaller; using system OCR tools")
        return status
    status["frozen"] = True

    tesseract_exe = bundle / "tesseract.exe"
    if tesseract_exe.exists():
        try:
            import pytesseract  # type: ignore

            pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
            tessdata = bundle / "tessdata"
            if tessdata.exists():
                os.environ["TESSDATA_PREFIX"] = str(tessdata)
            status["tesseract"] = True
            logger.info("Configured bundled tesseract at %s", tesseract_exe)
        except ImportError:
            logger.info(
                "pytesseract module not available; bundled tesseract.exe unusable"
            )

    pdftoppm = bundle / "pdftoppm.exe"
    if pdftoppm.exists():
        os.environ["POPPLER_PATH"] = str(bundle)
        os.environ["PATH"] = str(bundle) + os.pathsep + os.environ.get("PATH", "")
        status["poppler"] = True
        logger.info("Configured bundled poppler at %s", bundle)

    return status
