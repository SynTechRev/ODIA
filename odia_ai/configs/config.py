"""Configuration loading for ODIA AI pipelines.

Central config for dataset construction, training, evaluation, and
deployment. Designed so that a single YAML (or JSON) file fully
specifies a pipeline run — for reproducibility.

Uses stdlib-only parsing (no PyYAML required for JSON); YAML support
is lazy-imported.

Author: ODIA AI Team
License: MIT
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DatasetConfig:
    """Dataset construction configuration."""

    mas_corpus_dir: str = "./data/mas_corpus"
    output_dir: str = "./data/training_splits"
    format: str = "alpaca"  # "alpaca" | "openai" | "raw"
    enable_jurisdiction_transfer: bool = True
    enable_negatives: bool = False
    negative_sources_dir: str | None = None
    holdout_validation_jurisdiction: str = "TCSO"
    holdout_test_jurisdiction: str = "Exeter"
    random_seed: int = 42
    min_alert_body_chars: int = 80


@dataclass
class TrainingRunConfig:
    """Training-run configuration."""

    base_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    output_dir: str = "./models/odia-l2-latest"
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 16
    learning_rate: float = 2e-4
    max_seq_length: int = 4096
    load_in_4bit: bool = True
    bf16: bool = True
    seed: int = 42


@dataclass
class EvaluationRunConfig:
    """Evaluation-run configuration."""

    validation_dataset_path: str = "./data/training_splits/validation.jsonl"
    test_dataset_path: str = "./data/training_splits/test.jsonl"
    report_dir: str = "./reports/eval"
    max_examples: int | None = None
    evaluate_backends: list[str] = field(
        default_factory=lambda: ["pattern", "rag_llm", "finetuned"]
    )


@dataclass
class ContinualLearningConfig:
    """Continual-learning configuration."""

    correction_store_path: str = "./data/corrections.db"
    min_new_corrections: int = 50
    min_days_since_last_training: int = 30
    min_reviewed_fraction: float = 0.8
    regression_f1_threshold: float = 0.02


@dataclass
class DeploymentConfig:
    """Deployment / inference configuration."""

    registry_root: str = "./models/registry"
    default_llm_provider: str = "ollama"
    default_llm_model: str = "llama3.1:8b"
    finetuned_model_path: str | None = None
    force_backend: str | None = None  # None | "pattern" | "rag_llm" | "finetuned"


@dataclass
class ODIAAIConfig:
    """Top-level configuration combining all pipeline stages."""

    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    training: TrainingRunConfig = field(default_factory=TrainingRunConfig)
    evaluation: EvaluationRunConfig = field(default_factory=EvaluationRunConfig)
    continual: ContinualLearningConfig = field(default_factory=ContinualLearningConfig)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)

    def to_dict(self) -> dict:
        return {
            "dataset": asdict(self.dataset),
            "training": asdict(self.training),
            "evaluation": asdict(self.evaluation),
            "continual": asdict(self.continual),
            "deployment": asdict(self.deployment),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


def _read_yaml_or_json(path: Path) -> dict:
    """Read a config file as YAML (if .yaml/.yml) or JSON."""
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except ImportError:
            raise ImportError(
                "YAML config requires PyYAML. Install with: pip install pyyaml"
            )
        return yaml.safe_load(text) or {}
    return json.loads(text) if text.strip() else {}


def load_config(path: Path | str | None = None) -> ODIAAIConfig:
    """Load configuration from file, falling back to defaults.

    Args:
        path: path to YAML/JSON config file. If None, returns default config.

    Returns:
        Fully-populated ODIAAIConfig.
    """
    if path is None:
        return ODIAAIConfig()

    path = Path(path)
    if not path.exists():
        logger.warning("Config file not found: %s; using defaults", path)
        return ODIAAIConfig()

    raw = _read_yaml_or_json(path)
    cfg = ODIAAIConfig()

    for section_name, section_data in raw.items():
        if not hasattr(cfg, section_name) or not isinstance(section_data, dict):
            continue
        section = getattr(cfg, section_name)
        for k, v in section_data.items():
            if hasattr(section, k):
                setattr(section, k, v)
    return cfg


def write_config(cfg: ODIAAIConfig, path: Path) -> None:
    """Write a config to disk as JSON (always-available) or YAML (if requested)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
            path.write_text(
                yaml.safe_dump(cfg.to_dict(), sort_keys=False), encoding="utf-8"
            )
            return
        except ImportError:
            logger.info("PyYAML not installed; falling back to JSON")
    path.write_text(cfg.to_json(), encoding="utf-8")


def default_config_path() -> Path:
    """Return the default location for the config file."""
    return Path.home() / ".odia_ai" / "config.json"
