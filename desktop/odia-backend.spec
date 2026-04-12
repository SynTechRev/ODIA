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
        "sklearn",
        "sklearn.feature_extraction.text",
        "numpy",
        "httpx",
        "sqlalchemy",
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
