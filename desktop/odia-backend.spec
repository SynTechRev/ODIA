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

a = Analysis(
    [os.path.join(SPECPATH, "scripts", "backend_entry.py")],
    pathex=[src_path, project_root],
    binaries=[],
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
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "PIL",
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
