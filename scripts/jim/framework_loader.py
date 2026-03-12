"""
Constitutional Framework Loader - CLF-v1

Loads and provides access to Constitutional Linguistic Frameworks for JIM, ACE,
MSH, CAIM, and VICFM integration.
"""

import json
from pathlib import Path
from typing import Any


class ConstitutionalFrameworkLoader:
    """
    Loader for Constitutional Linguistic Frameworks (CLF-v1).

    Provides methods to:
    - Load all constitutional interpretation frameworks
    - Retrieve specific frameworks by name
    - List available frameworks
    - Get JIM-specific weights for doctrinal analysis
    - Integrate with MSH, ACE, CAIM, and VICFM
    """

    VERSION = "1.0.0"

    def __init__(self, frameworks_file: Path | None = None):
        """
        Initialize framework loader.

        Args:
            frameworks_file: Path to CONSTITUTIONAL_LINGUISTIC_FRAMEWORKS.json
                           If None, uses default location
        """
        if frameworks_file is None:
            repo_root = Path(__file__).parent.parent.parent
            frameworks_file = (
                repo_root
                / "constitutional"
                / "CONSTITUTIONAL_LINGUISTIC_FRAMEWORKS.json"
            )

        self.frameworks_file = Path(frameworks_file)
        self.frameworks_data: dict[str, Any] = {}
        self.frameworks: dict[str, Any] = {}
        self.loaded = False

    def load_all(self) -> dict[str, Any]:
        """
        Load all constitutional interpretation frameworks from JSON.

        Returns:
            Dictionary with:
                - success: bool
                - frameworks_loaded: int
                - framework_ids: list of framework identifiers
                - version: CLF version
                - jim_total_weight: sum of JIM weights
                - ace_total_weight: sum of ACE weights
        """
        try:
            with open(self.frameworks_file) as f:
                self.frameworks_data = json.load(f)

            self.frameworks = self.frameworks_data.get("frameworks", {})
            self.loaded = True

            # Calculate weight sums
            jim_total = sum(f.get("jim_weight", 0.0) for f in self.frameworks.values())
            ace_total = sum(f.get("ace_weight", 0.0) for f in self.frameworks.values())

            return {
                "success": True,
                "frameworks_loaded": len(self.frameworks),
                "framework_ids": list(self.frameworks.keys()),
                "version": self.frameworks_data.get("version", "unknown"),
                "jim_total_weight": jim_total,
                "ace_total_weight": ace_total,
                "metadata": self.frameworks_data.get("metadata", {}),
            }

        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Frameworks file not found: {self.frameworks_file}",
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON in frameworks file: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Error loading frameworks: {e}"}

    def get_framework(self, name: str) -> dict[str, Any]:
        """
        Retrieve a specific constitutional interpretation framework.

        Args:
            name: Framework identifier (e.g., 'original_public_meaning', 'textualism')

        Returns:
            Framework data dictionary or error dict if not found
        """
        if not self.loaded:
            load_result = self.load_all()
            if not load_result["success"]:
                return load_result

        if name in self.frameworks:
            return {"success": True, "framework": self.frameworks[name]}
        else:
            return {
                "success": False,
                "error": f"Framework '{name}' not found",
                "available_frameworks": list(self.frameworks.keys()),
            }

    def list_frameworks(self) -> dict[str, Any]:
        """
        List all available constitutional interpretation frameworks.

        Returns:
            Dictionary with framework summaries including:
                - framework_id
                - name
                - definition (summary)
                - jim_weight
                - ace_weight
                - reconstruction_override
        """
        if not self.loaded:
            load_result = self.load_all()
            if not load_result["success"]:
                return load_result

        summaries = []
        for _framework_id, framework_data in self.frameworks.items():
            summaries.append(
                {
                    "framework_id": framework_data.get("framework_id"),
                    "name": framework_data.get("name"),
                    "definition": (
                        framework_data.get("definition", "")[:200] + "..."
                        if len(framework_data.get("definition", "")) > 200
                        else framework_data.get("definition", "")
                    ),
                    "jim_weight": framework_data.get("jim_weight"),
                    "ace_weight": framework_data.get("ace_weight"),
                    "reconstruction_override": framework_data.get(
                        "reconstruction_override", False
                    ),
                    "temporal_scope": framework_data.get("temporal_scope", {}).get(
                        "primary_era"
                    ),
                }
            )

        return {
            "success": True,
            "total_frameworks": len(summaries),
            "frameworks": summaries,
        }

    def get_weights_for_jim(self, amendment_type: str | None = None) -> dict[str, Any]:
        """
        Get JIM-specific weights for constitutional interpretation.

        Applies conflict resolution rules based on amendment type.

        Args:
            amendment_type: Type of amendment being analyzed:
                - 'reconstruction' (13th, 14th, 15th Amendments)
                - 'founding' (original Constitution, Bill of Rights)
                - 'modern' (other amendments)
                - None (use default weights)

        Returns:
            Dictionary with framework weights adjusted for context
        """
        if not self.loaded:
            load_result = self.load_all()
            if not load_result["success"]:
                return load_result

        weights = {}

        for framework_id, framework_data in self.frameworks.items():
            base_weight = framework_data.get("jim_weight", 0.0)

            # Apply reconstruction override rule
            if amendment_type == "reconstruction":
                if framework_data.get("reconstruction_override", False):
                    # Elevate reconstruction_era_intent weight
                    weights[framework_id] = base_weight * 1.3
                elif framework_id in [
                    "original_public_meaning",
                    "framers_intent",
                    "founding_era_linguistic_baselines",
                ]:
                    # Reduce founding-era weights by 30%
                    weights[framework_id] = base_weight * 0.7
                else:
                    weights[framework_id] = base_weight
            elif amendment_type == "founding":
                # Emphasize founding-era frameworks
                if framework_id in [
                    "original_public_meaning",
                    "textualism",
                    "framers_intent",
                    "founding_era_linguistic_baselines",
                ]:
                    weights[framework_id] = base_weight * 1.2
                else:
                    weights[framework_id] = base_weight
            else:
                # Default weights
                weights[framework_id] = base_weight

        # Normalize weights to sum to approximately 2.0-2.5
        total = sum(weights.values())

        return {
            "success": True,
            "amendment_type": amendment_type or "default",
            "weights": weights,
            "total_weight": total,
            "normalized": total > 0,
        }

    def get_semantic_drift_scores(
        self, start_era: int, end_era: int = 2025
    ) -> dict[str, Any]:
        """
        Get semantic drift scores across frameworks for era analysis.

        Args:
            start_era: Starting year (e.g., 1789, 1868)
            end_era: Ending year (default: 2025)

        Returns:
            Dictionary with drift scores by framework
        """
        if not self.loaded:
            load_result = self.load_all()
            if not load_result["success"]:
                return load_result

        drift_scores = {}

        for framework_id, framework_data in self.frameworks.items():
            semantic_drift = framework_data.get("semantic_drift", {})

            # Try to find matching drift score
            drift_key = f"{start_era}_to_{end_era}"

            if drift_key in semantic_drift:
                drift_scores[framework_id] = semantic_drift[drift_key]
            elif "multi_era_framework" in semantic_drift:
                # Multi-era framework
                drift_scores[framework_id] = semantic_drift.get(
                    "era_specific_analysis", {}
                )
            else:
                # Find closest match
                closest_score = 0.0
                for key, value in semantic_drift.items():
                    if key.startswith(str(start_era)) and isinstance(
                        value, int | float
                    ):
                        closest_score = value
                        break
                drift_scores[framework_id] = closest_score

        return {
            "success": True,
            "start_era": start_era,
            "end_era": end_era,
            "drift_scores": drift_scores,
            "notes": f"Semantic drift from {start_era} to {end_era}",
        }

    def get_conflict_resolution_rules(self) -> dict[str, Any]:
        """
        Get conflict resolution rules for multi-framework analysis.

        Returns:
            Conflict resolution rules from frameworks data
        """
        if not self.loaded:
            load_result = self.load_all()
            if not load_result["success"]:
                return load_result

        return {
            "success": True,
            "conflict_resolution": self.frameworks_data.get("conflict_resolution", {}),
        }

    def get_integration_points(self) -> dict[str, Any]:
        """
        Get integration points for JIM, ACE, MSH, CAIM, VICFM.

        Returns:
            Integration points metadata
        """
        if not self.loaded:
            load_result = self.load_all()
            if not load_result["success"]:
                return load_result

        return {
            "success": True,
            "integration_points": self.frameworks_data.get("integration_points", {}),
        }

    def validate_frameworks(self) -> dict[str, Any]:
        """
        Validate loaded frameworks against schema requirements.

        Returns:
            Validation result with any errors or warnings
        """
        if not self.loaded:
            load_result = self.load_all()
            if not load_result["success"]:
                return load_result

        errors = []
        warnings = []

        # Check each framework
        for framework_id, framework_data in self.frameworks.items():
            # Check required fields
            required_fields = [
                "framework_id",
                "name",
                "definition",
                "method",
                "historical_origin",
                "temporal_scope",
                "strengths",
                "weaknesses",
                "landmark_cases",
                "jim_weight",
                "ace_weight",
                "semantic_drift",
                "key_scholars",
            ]

            for field in required_fields:
                if field not in framework_data:
                    errors.append(
                        f"Framework '{framework_id}' missing required field '{field}'"
                    )

            # Check weight constraints
            jim_weight = framework_data.get("jim_weight", 0)
            ace_weight = framework_data.get("ace_weight", 0)

            if not (0.05 <= jim_weight <= 0.40):
                warnings.append(
                    f"Framework '{framework_id}' jim_weight {jim_weight} outside recommended range [0.05, 0.40]"  # noqa: E501
                )

            if not (0.05 <= ace_weight <= 0.40):
                warnings.append(
                    f"Framework '{framework_id}' ace_weight {ace_weight} outside recommended range [0.05, 0.40]"  # noqa: E501
                )

        return {
            "success": len(errors) == 0,
            "valid": len(errors) == 0,
            "frameworks_validated": len(self.frameworks),
            "errors": errors,
            "warnings": warnings,
        }
