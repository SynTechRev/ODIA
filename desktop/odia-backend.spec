# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for ODIA Desktop backend.

Bundles the FastAPI backend into a single executable for distribution.
The resulting binary starts the uvicorn server with the ODIA API.

Usage:
    pyinstaller desktop/odia-backend.spec --distpath desktop/build/backend
"""

import os
import sys

block_cipher = None

# Path to the project root (one level up from desktop/)
project_root = os.path.abspath(os.path.join(SPECPATH, ".."))
src_path = os.path.join(project_root, "src")

# ---------------------------------------------------------------------------
# Optional OCR tooling: Tesseract + Poppler binaries.
#
# We bundle them when they are present on the build machine, so the
# resulting installer can OCR scanned PDFs out of the box. When they
# are absent the build still succeeds but the installer degrades to
# text-layer PDFs only; src/oraculus_di_auditor/ingestion/engine.py
# detects this and logs gracefully rather than crashing.
#
# Default paths match the standard Windows installers:
#   - Tesseract:  winget install UB-Mannheim.TesseractOCR
#   - Poppler:    https://github.com/oschwartz10612/poppler-windows/releases
# Override by setting TESSERACT_ROOT / POPPLER_ROOT in the build env.
# ---------------------------------------------------------------------------
TESSERACT_ROOT = os.environ.get(
    "TESSERACT_ROOT", r"C:\Program Files\Tesseract-OCR"
)
POPPLER_ROOT = os.environ.get(
    "POPPLER_ROOT", r"C:\Program Files\poppler\Library\bin"
)

_ocr_binaries = []
_ocr_datas = []

_tesseract_exe = os.path.join(TESSERACT_ROOT, "tesseract.exe")
if os.path.isfile(_tesseract_exe):
    _ocr_binaries.append((_tesseract_exe, "."))
    _tessdata = os.path.join(TESSERACT_ROOT, "tessdata")
    if os.path.isdir(_tessdata):
        _ocr_datas.append((_tessdata, "tessdata"))
    # Tesseract's DLL dependencies live alongside the exe.
    for _dll in os.listdir(TESSERACT_ROOT):
        if _dll.lower().endswith(".dll"):
            _ocr_binaries.append((os.path.join(TESSERACT_ROOT, _dll), "."))
else:
    print("[odia-backend.spec] Tesseract not found at %s; OCR support will "
          "be missing from this build. Set TESSERACT_ROOT to override."
          % TESSERACT_ROOT)

if os.path.isdir(POPPLER_ROOT):
    for _name in os.listdir(POPPLER_ROOT):
        _path = os.path.join(POPPLER_ROOT, _name)
        if os.path.isfile(_path) and _name.lower().endswith((".exe", ".dll")):
            _ocr_binaries.append((_path, "."))
else:
    print("[odia-backend.spec] Poppler not found at %s; OCR support will "
          "be missing from this build. Set POPPLER_ROOT to override."
          % POPPLER_ROOT)

a = Analysis(
    [os.path.join(SPECPATH, "scripts", "backend_entry.py")],
    pathex=[src_path, project_root],
    binaries=list(_ocr_binaries),
    datas=[
        # Include config files
        (os.path.join(project_root, "config"), "config"),
        # Include legal reference data
        (os.path.join(project_root, "legal"), "legal"),
        # Include constitutional frameworks
        (os.path.join(project_root, "constitutional"), "constitutional"),
        # Include schemas
        (os.path.join(project_root, "schemas"), "schemas"),
        # Include templates
        (os.path.join(project_root, "templates"), "templates"),
        # Tesseract language data (if bundled above)
        *_ocr_datas,
    ],
    hiddenimports=[
        "oraculus_di_auditor",
        "oraculus_di_auditor.interface.api",
        "oraculus_di_auditor.analysis",
        "oraculus_di_auditor.ingestion",
        "oraculus_di_auditor.orchestrator",
        "oraculus_di_auditor.governor",
        "oraculus_di_auditor.normalize",
        "oraculus_di_auditor.embeddings",
        "oraculus_di_auditor.provenance",
        "oraculus_di_auditor.config",
        # Route modules — imported lazily inside create_app(), so
        # PyInstaller's static analysis will miss them without hints.
        "oraculus_di_auditor.interface.routes.orchestrator",
        "oraculus_di_auditor.interface.routes.governor",
        "oraculus_di_auditor.interface.routes.gcn",
        "oraculus_di_auditor.interface.routes.mesh",
        "oraculus_di_auditor.interface.routes.multi_jurisdiction",
        "oraculus_di_auditor.interface.routes.reports",
        "oraculus_di_auditor.interface.routes.rag",
        "oraculus_di_auditor.interface.routes.compliance",
        "oraculus_di_auditor.interface.routes.temporal",
        "oraculus_di_auditor.interface.routes.upload",
        "oraculus_di_auditor.interface.routes.retrieval",
        "oraculus_di_auditor.interface.routes.auth_routes",
        "oraculus_di_auditor.interface.routes.workspace_routes",
        "oraculus_di_auditor.interface.routes.detectors",
        "oraculus_di_auditor.auth.auth_service",
        "oraculus_di_auditor.auth.auth_middleware",
        "oraculus_di_auditor.auth.auth_models",
        "oraculus_di_auditor.db.session",
        "oraculus_di_auditor.db.models",
        "oraculus_di_auditor.rag",
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "pydantic",
        "starlette",
        # Auth stack — jose + bcrypt are imported lazily inside auth_service.py.
        # passlib is still declared in pyproject.toml runtime deps; include
        # its bcrypt handler so it is available if any code path falls back to it.
        "jose",
        "jose.jwt",
        "jose.backends",
        "jose.backends.cryptography_backend",
        "bcrypt",
        "passlib",
        "passlib.handlers",
        "passlib.handlers.bcrypt",
        "cryptography",
        "cryptography.hazmat.backends.openssl",
        # FastAPI form/file upload support and email validation.
        "python_multipart",
        "multipart",
        "email_validator",
        # SQLAlchemy SQLite dialect — needed by db/session.py at runtime.
        "sqlalchemy",
        "sqlalchemy.dialects.sqlite",
        "sqlalchemy.ext.declarative",
        "sklearn",
        "sklearn.feature_extraction.text",
        "sklearn.utils._typedefs",
        "sklearn.utils._heap",
        "sklearn.utils._sorting",
        "sklearn.utils._vector_sentinel",
        "sklearn.neighbors._partition_nodes",
        "numpy",
        "httpx",
        "jinja2",
        "markdown",
        # PDF ingestion stack. pypdf is imported inside a try/except guard
        # in ingestion/engine.py; without an explicit hint PyInstaller's
        # static analyser can still find it, but we list it to be safe.
        # pdf2image + pytesseract + PIL are the OCR fallback path and
        # MUST be listed explicitly because they only appear in a
        # conditional branch that the analyser can skip.
        "pypdf",
        "pdf2image",
        "pytesseract",
        "PIL",
        "PIL.Image",
        "PIL._imaging",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        # Bundled-binaries runtime shim.
        "oraculus_di_auditor.bundled_binaries",
        # ODIA AI subsystem (odia_ai package at repo root) - imported
        # lazily inside create_app()'s guarded try/except, so the
        # analyser will not see it without explicit hints.
        "odia_ai",
        "odia_ai.backref",
        "odia_ai.backref.extractor",
        "odia_ai.configs",
        "odia_ai.configs.config",
        "odia_ai.continual",
        "odia_ai.continual.feedback_store",
        "odia_ai.extraction",
        "odia_ai.extraction.extractor",
        "odia_ai.registry",
        "odia_ai.registry.registry",
        "odia_ai.server_routes",
        "odia_ai.server_routes.routes",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        # PIL / Pillow intentionally NOT excluded - pdf2image and
        # pytesseract require it for the OCR fallback on scanned PDFs.
        "IPython",
        "notebook",
        "pytest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="odia-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
