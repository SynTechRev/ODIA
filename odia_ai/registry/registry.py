"""Model version registry for ODIA fine-tuned models.

Tracks model versions, training provenance, evaluation metrics, and
deployment status. Each model version has a unique ID and is stored
on disk with a metadata manifest.

Registry entries include:
- version_id: "odia-l2-v{semver}+{shorthash}"
- base_model: HuggingFace repo ID
- training_config: LoRA + training hyperparameters used
- training_data_hash: SHA-256 of the training JSONL
- evaluation_metrics: output of odia_ai.evaluation.harness
- deployment_status: "experimental" | "staging" | "production" | "archived"
- parent_version: lineage tracking for LoRA-on-LoRA training

Author: ODIA AI Team
License: MIT
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

DeploymentStatus = Literal["experimental", "staging", "production", "archived"]


@dataclass
class ModelVersion:
    """Registry entry for a single model version."""

    version_id: str
    base_model: str
    model_path: str
    training_config: dict = field(default_factory=dict)
    lora_config: dict = field(default_factory=dict)
    training_data_hash: str = ""
    num_training_examples: int = 0
    num_evaluation_examples: int = 0
    evaluation_metrics: dict = field(default_factory=dict)
    deployment_status: DeploymentStatus = "experimental"
    parent_version_id: str | None = None
    created_at: float = field(default_factory=time.time)
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class ModelRegistry:
    """File-system-backed model version registry.

    Layout:
        registry_root/
            manifest.json       (index of all versions)
            v{version_id}/
                metadata.json   (ModelVersion data)
                model/          (LoRA adapter weights + tokenizer)
                evaluation/     (evaluation outputs)
    """

    def __init__(self, registry_root: Path):
        self.root = registry_root
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.json"
        if not self.manifest_path.exists():
            self._write_manifest({"versions": [], "production_version_id": None})

    def _read_manifest(self) -> dict:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, manifest: dict) -> None:
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    def register(self, version: ModelVersion) -> str:
        """Register a new model version. Returns the version_id."""
        version_dir = self.root / f"v_{version.version_id}"
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "metadata.json").write_text(
            json.dumps(version.to_dict(), indent=2), encoding="utf-8"
        )
        manifest = self._read_manifest()
        # Remove any existing entry with same version_id
        manifest["versions"] = [
            v for v in manifest["versions"] if v.get("version_id") != version.version_id
        ]
        manifest["versions"].append(
            {
                "version_id": version.version_id,
                "base_model": version.base_model,
                "deployment_status": version.deployment_status,
                "created_at": version.created_at,
            }
        )
        self._write_manifest(manifest)
        return version.version_id

    def get(self, version_id: str) -> ModelVersion | None:
        version_dir = self.root / f"v_{version_id}"
        metadata_path = version_dir / "metadata.json"
        if not metadata_path.exists():
            return None
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        return ModelVersion(**data)

    def list_versions(self) -> list[dict]:
        return self._read_manifest()["versions"]

    def set_deployment_status(
        self, version_id: str, status: DeploymentStatus
    ) -> bool:
        """Update deployment status of a version.

        When setting 'production', demotes any existing production version
        to 'staging' (only one production version at a time).
        """
        version = self.get(version_id)
        if version is None:
            return False

        manifest = self._read_manifest()
        if status == "production":
            # Demote any existing production version
            for v in manifest["versions"]:
                if v.get("deployment_status") == "production" and v["version_id"] != version_id:
                    v["deployment_status"] = "staging"
                    prior = self.get(v["version_id"])
                    if prior:
                        prior.deployment_status = "staging"
                        self._save_metadata(prior)
            manifest["production_version_id"] = version_id

        # Update this version's status
        version.deployment_status = status
        self._save_metadata(version)
        for v in manifest["versions"]:
            if v["version_id"] == version_id:
                v["deployment_status"] = status
                break
        self._write_manifest(manifest)
        return True

    def _save_metadata(self, version: ModelVersion) -> None:
        version_dir = self.root / f"v_{version.version_id}"
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "metadata.json").write_text(
            json.dumps(version.to_dict(), indent=2), encoding="utf-8"
        )

    def production_version(self) -> ModelVersion | None:
        manifest = self._read_manifest()
        pid = manifest.get("production_version_id")
        return self.get(pid) if pid else None

    def delete(self, version_id: str, archive_instead: bool = True) -> bool:
        """Delete or archive a model version."""
        if archive_instead:
            return self.set_deployment_status(version_id, "archived")
        # Full delete
        version_dir = self.root / f"v_{version_id}"
        if version_dir.exists():
            import shutil
            shutil.rmtree(version_dir)
        manifest = self._read_manifest()
        manifest["versions"] = [
            v for v in manifest["versions"] if v["version_id"] != version_id
        ]
        if manifest.get("production_version_id") == version_id:
            manifest["production_version_id"] = None
        self._write_manifest(manifest)
        return True


def compute_dataset_hash(dataset_path: Path) -> str:
    """Return SHA-256 of the dataset file contents."""
    h = hashlib.sha256()
    with dataset_path.open("rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_version_id(semver: str = "0.1.0", prefix: str = "odia-l2") -> str:
    """Generate a short, unique version ID like 'odia-l2-v0.1.0+a1b2c3d4'."""
    short_hash = str(uuid.uuid4()).replace("-", "")[:8]
    return f"{prefix}-v{semver}+{short_hash}"
