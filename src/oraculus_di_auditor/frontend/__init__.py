"""Phase 6: Front-End System & User Interaction Layer.

This module implements the front-end architecture and human-interface intelligence
layer for the Oraculus-DI-Auditor system.

Core Components:
- Frontend Orchestrator: Coordinates UI generation and integration
- Component Definitions: React/Next.js component specifications
- API Client: Backend integration layer
- Gap Detector: Validates completeness and identifies missing pieces

All outputs are deterministic, structured, and agent-ready for autonomous UI generation.
"""

from .frontend_orchestrator import Phase6Orchestrator

__all__ = ["Phase6Orchestrator"]
