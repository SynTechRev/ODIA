"""
JIM Case Loader - Loads and validates Supreme Court case law data.
"""

import json
from pathlib import Path
from typing import Any


class JIMCaseLoader:
    """Loads and manages Supreme Court case law database."""

    def __init__(self, cases_dir: Path | None = None):
        """
        Initialize case loader.

        Args:
            cases_dir: Directory containing case law JSON files.
                      Defaults to /legal/cases/ in repository root.
        """
        if cases_dir is None:
            # Default to repository legal/cases directory
            repo_root = Path(__file__).parent.parent.parent
            cases_dir = repo_root / "legal" / "cases"

        self.cases_dir = Path(cases_dir)
        self.scotus_index: dict[str, Any] = {}
        self.cases_by_doctrine: dict[str, list[dict[str, Any]]] = {}
        self.cases_by_year: dict[int, list[dict[str, Any]]] = {}
        self.interpretive_canons: list[dict[str, Any]] = []

    def load_scotus_index(self) -> dict[str, Any]:
        """
        Load Supreme Court case index.

        Returns:
            Dictionary containing full SCOTUS index with metadata and cases.

        Raises:
            FileNotFoundError: If SCOTUS_INDEX.json not found.
            json.JSONDecodeError: If JSON is malformed.
        """
        index_path = self.cases_dir / "SCOTUS_INDEX.json"

        if not index_path.exists():
            raise FileNotFoundError(f"SCOTUS index not found at {index_path}")

        with open(index_path, encoding="utf-8") as f:
            self.scotus_index = json.load(f)

        self._index_cases()
        return self.scotus_index

    def _index_cases(self) -> None:
        """Build internal indexes for efficient case lookup."""
        if "cases" not in self.scotus_index:
            return

        # Clear existing indexes
        self.cases_by_doctrine.clear()
        self.cases_by_year.clear()

        # Index by doctrine
        for case in self.scotus_index["cases"]:
            doctrine = case.get("doctrine", "unknown")
            if doctrine not in self.cases_by_doctrine:
                self.cases_by_doctrine[doctrine] = []
            self.cases_by_doctrine[doctrine].append(case)

            # Index by year
            year = case.get("year")
            if year:
                if year not in self.cases_by_year:
                    self.cases_by_year[year] = []
                self.cases_by_year[year].append(case)

        # Store interpretive canons
        self.interpretive_canons = self.scotus_index.get("interpretive_canons", [])

    def get_cases_by_doctrine(self, doctrine: str) -> list[dict[str, Any]]:
        """
        Retrieve cases by doctrinal category.

        Args:
            doctrine: Doctrine identifier (e.g., 'due_process', 'fourth_amendment')

        Returns:
            List of case dictionaries matching doctrine.
        """
        return self.cases_by_doctrine.get(doctrine, [])

    def get_cases_by_year_range(
        self, start_year: int, end_year: int
    ) -> list[dict[str, Any]]:
        """
        Retrieve cases within year range.

        Args:
            start_year: Inclusive start year
            end_year: Inclusive end year

        Returns:
            List of cases decided between start_year and end_year.
        """
        cases = []
        for year in range(start_year, end_year + 1):
            cases.extend(self.cases_by_year.get(year, []))
        return cases

    def get_case_by_id(self, case_id: str) -> dict[str, Any] | None:
        """
        Retrieve specific case by ID.

        Args:
            case_id: Unique case identifier

        Returns:
            Case dictionary or None if not found.
        """
        for case in self.scotus_index.get("cases", []):
            if case.get("case_id") == case_id:
                return case
        return None

    def search_cases_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """
        Search cases by issue tag.

        Args:
            tag: Issue tag to search for (e.g., 'procedural_due_process')

        Returns:
            List of cases containing the specified tag.
        """
        matching_cases = []
        for case in self.scotus_index.get("cases", []):
            if tag in case.get("issue_tags", []):
                matching_cases.append(case)
        return matching_cases

    def get_interpretive_canon(self, canon_id: str) -> dict[str, Any] | None:
        """
        Retrieve interpretive canon by ID.

        Args:
            canon_id: Canon identifier (e.g., 'major_questions_doctrine')

        Returns:
            Canon dictionary or None if not found.
        """
        for canon in self.interpretive_canons:
            if canon.get("canon_id") == canon_id:
                return canon
        return None

    def get_all_doctrines(self) -> list[str]:
        """
        Get list of all doctrinal categories.

        Returns:
            List of doctrine identifiers.
        """
        return list(self.cases_by_doctrine.keys())

    def get_metadata(self) -> dict[str, Any]:
        """
        Get index metadata.

        Returns:
            Dictionary containing version, generation time, and statistics.
        """
        return {
            "version": self.scotus_index.get("version"),
            "generated_at": self.scotus_index.get("generated_at"),
            "metadata": self.scotus_index.get("metadata", {}),
            "total_cases_loaded": len(self.scotus_index.get("cases", [])),
            "doctrines": list(self.cases_by_doctrine.keys()),
            "year_range": (
                min(self.cases_by_year.keys()) if self.cases_by_year else None,
                max(self.cases_by_year.keys()) if self.cases_by_year else None,
            ),
        }

    def validate_index(self) -> dict[str, Any]:
        """
        Validate loaded case index for required fields and data integrity.

        Returns:
            Validation report with errors and warnings.
        """
        errors = []
        warnings = []

        # Check required top-level fields
        required_fields = ["version", "cases", "metadata"]
        for field in required_fields:
            if field not in self.scotus_index:
                errors.append(f"Missing required field: {field}")

        # Validate each case
        cases = self.scotus_index.get("cases", [])
        required_case_fields = [
            "case_id",
            "name",
            "citation",
            "year",
            "doctrine",
            "summary",
            "holding",
        ]

        for idx, case in enumerate(cases):
            for field in required_case_fields:
                if field not in case:
                    errors.append(f"Case {idx} missing required field: {field}")

            # Validate doctrinal weight
            if "doctrinal_weight" in case:
                weight = case["doctrinal_weight"]
                if not (0.0 <= weight <= 1.0):
                    warnings.append(
                        f"Case {case.get('case_id', idx)} has invalid weight: {weight}"
                    )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "cases_validated": len(cases),
        }
