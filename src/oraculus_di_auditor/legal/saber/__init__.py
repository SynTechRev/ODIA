# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 SynTechRev / Mars (Marco Anthony Ramon Sanchez)
# This subpackage is licensed under the Apache License, Version 2.0.
# See LICENSE-Apache-2.0 in this directory for full terms.
# ELECT-6 final election: Apache-2.0 for saber/ (elected 2026-10-04).
# Rationale: explicit patent grant protects vulnerable populations who cannot
# litigate patent claims against a cryptographic integrity platform.
"""S.A.B.E.R. -- Security Asymmetry Balance Equalization Record.

Corpus integrity infrastructure for the O.D.I.A. platform.
Implements the Four Pillars of Integrity:

  Pillar 1: Content-addressed immutable storage  (content_store.py)
  Pillar 2: Reproducible loader manifest         (manifest.py)
  Pillar 3: Append-only Merkle audit log         (audit_log.py)
  Pillar 4: Crypto-agile hybrid signatures       (signing.py)

ELECT-1: S.A.B.E.R. (Security Asymmetry Balance Equalization Record)
ELECT-2: Namespace -- oraculus_di_auditor.legal.saber
ELECT-6: Apache-2.0 (saber/ subpackage, elected 2026-10-04)
"""

from .audit_log import AuditLog
from .content_store import ContentAddress, ContentStore
from .manifest import LoaderManifest
from .signing import HybridSignature, SigningKey, VerifyKey

__all__ = [
    "AuditLog",
    "ContentAddress",
    "ContentStore",
    "HybridSignature",
    "LoaderManifest",
    "SigningKey",
    "VerifyKey",
]
