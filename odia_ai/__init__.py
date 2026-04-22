"""O.D.I.A. AI — Fine-tuning and continual-learning infrastructure.

This subsystem operationalizes the fine-tuning vision for ODIA:
converting the ~3,150-document forensic audit corpus (spanning 9
Tulare County jurisdictions and 1,379 labeled alerts) into a
training-data pipeline, a LoRA fine-tuning runner, a continual-learning
feedback loop, and an evaluation harness.

Design principles:
- Integrates with existing oraculus_di_auditor modules (does not replace)
- Local-first: runs on a single workstation with consumer GPU
- Open-source: MIT license consistent with the parent project
- Reproducible: deterministic data splits, pinned model versions, hash-provenance
- Progressive: RAG baseline → LoRA fine-tune → multi-layer extraction stack

Subpackages:
- backref: Alert-to-document back-reference extraction from MAS files
- extraction: Layer 2 NER + relational extraction (pre-fine-tune: spaCy/general LLM)
- training: LoRA fine-tuning runner using PEFT library
- evaluation: Held-out jurisdiction validation + accuracy/recall/F1 metrics
- continual: Human-in-the-loop feedback collection + re-training triggers
- registry: Model version registry with metadata and evaluation results
- configs: YAML configs for model, training, and evaluation settings
- cli: Command-line entry points
- server_routes: FastAPI route additions for desktop app integration

Author: Synthetic Technology Revolution / Mars (Marco Anthony Ramon Sanchez)
License: MIT
"""

__version__ = "0.1.0"
__all__ = [
    "backref",
    "extraction",
    "training",
    "evaluation",
    "continual",
    "registry",
    "configs",
]
