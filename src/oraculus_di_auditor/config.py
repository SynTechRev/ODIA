"""Configuration module for Oraculus DI Auditor.

Author: Marcus A. Sanchez
Date: 2025-11-12
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
CASES_DIR = DATA_DIR / "cases"
STATUTES_DIR = DATA_DIR / "statutes"
SOURCES_DIR = DATA_DIR / "sources"
VECTORS_DIR = DATA_DIR / "vectors"
REPORTS_DIR = DATA_DIR / "reports"
INDICES_DIR = DATA_DIR / "indices"

# Phase 7: External data mount points for large-scale corpus integration
# These paths can be configured externally via environment variables
# and should point to locations outside the Git repository
DATA_PATHS = {
    "uscode": os.getenv("ORACULUS_USCODE_PATH", "/data/legal/uscode"),
    "cfr": os.getenv("ORACULUS_CFR_PATH", "/data/legal/cfr"),
    "california": os.getenv("ORACULUS_CA_PATH", "/data/legal/ca"),
}
