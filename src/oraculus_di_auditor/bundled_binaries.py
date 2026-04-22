"""Runtime configuration for PyInstaller-bundled external binaries.

Three discovery strategies, tried in order:

1. **PyInstaller bundle (Windows)**: tesseract.exe + DLLs and pdftoppm.exe
   live alongside the frozen executable's _MEIPASS directory. This is the
   shipping mode for Windows — zero user setup required.

2. **Frozen exe on POSIX (mac/linux)**: the spec does NOT bundle OCR tools
   on these platforms (see desktop/odia-backend.spec for rationale). Fall
   through to system-PATH discovery via shutil.which so users with
   `brew install tesseract poppler` or `apt-get install tesseract-ocr
   poppler-utils` get OCR without any further configuration.

3. **Not frozen (regular Python / dev)**: no-op. pytesseract + pdf2image
   will look up `tesseract` / `pdftoppm` via PATH on their own; we don't
   override either.

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
import shutil
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


def _configure_windows_bundled(
    bundle: Path, status: dict[str, bool]
) -> None:
    """Wire pytesseract + pdf2image to binaries packed next to the exe."""
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


def _configure_system_path(status: dict[str, bool]) -> None:
    """Look up tesseract + pdftoppm via PATH and wire pytesseract explicitly.

    pytesseract defaults to calling bare "tesseract", which works if PATH
    is clean but can fail inside packaged Electron apps on macOS (where
    /usr/local/bin and /opt/homebrew/bin are sometimes not on the spawned
    backend's PATH). Resolving via shutil.which once and setting
    tesseract_cmd to an absolute path sidesteps that.
    """
    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        try:
            import pytesseract  # type: ignore

            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            status["tesseract"] = True
            logger.info(
                "Configured system tesseract at %s (via PATH)", tesseract_path
            )
        except ImportError:
            logger.info("pytesseract module not available; system tesseract unused")
    else:
        logger.info(
            "No tesseract found on PATH. Install via system package manager "
            "(brew install tesseract / apt-get install tesseract-ocr) for "
            "scanned-PDF OCR support."
        )

    pdftoppm_path = shutil.which("pdftoppm")
    if pdftoppm_path:
        # pdf2image.convert_from_path accepts an explicit poppler_path; our
        # ingestion engine reads POPPLER_PATH from the environment and passes
        # it through when invoking convert_from_path.
        os.environ["POPPLER_PATH"] = str(Path(pdftoppm_path).parent)
        status["poppler"] = True
        logger.info(
            "Configured system poppler at %s (via PATH)",
            os.environ["POPPLER_PATH"],
        )
    else:
        logger.info(
            "No pdftoppm found on PATH. Install via system package manager "
            "(brew install poppler / apt-get install poppler-utils) for "
            "scanned-PDF OCR support."
        )


def configure_bundled_binaries() -> dict[str, bool]:
    """Wire pytesseract and pdf2image to the best available OCR binaries.

    Returns a status dict reporting which OCR tooling was detected and
    configured. Caller can log this at startup for observability.
    """
    status: dict[str, bool] = {"tesseract": False, "poppler": False, "frozen": False}
    bundle = _bundle_dir()
    if bundle is None:
        logger.debug("Not running under PyInstaller; using system OCR tools")
        return status
    status["frozen"] = True

    # Prefer bundled binaries when they exist (Windows installer path).
    _configure_windows_bundled(bundle, status)

    # On platforms where the spec skipped bundling (macOS / Linux), fall
    # back to PATH-based discovery so users with `brew install tesseract`
    # still get OCR wired up.
    if not status["tesseract"] or not status["poppler"]:
        _configure_system_path(status)

    return status
