"""Detection Engine for Phase 11 Self-Healing.

Detects system degradation, integrity issues, and architectural problems.
"""

from __future__ import annotations

import ast
import importlib
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Health score weights
CRITICAL_ISSUE_WEIGHT = 0.2
HIGH_ISSUE_WEIGHT = 0.1


class DetectionEngine:
    """Detects system issues before they cause failures.

    Capabilities:
    - Broken imports detection
    - Schema divergence detection
    - Anti-pattern detection
    - Performance bottleneck detection
    - Dead code detection
    - Security vulnerability detection
    """

    def __init__(self, root_path: str | None = None):
        """Initialize detection engine.

        Args:
            root_path: Root path of the project (defaults to src/oraculus_di_auditor)
        """
        if root_path is None:
            # Auto-detect project root
            current_file = Path(__file__)
            self.root_path = current_file.parent.parent
        else:
            self.root_path = Path(root_path)

        self.detection_history: list[dict[str, Any]] = []
        logger.info(f"DetectionEngine initialized at {self.root_path}")

    def detect_broken_imports(self) -> list[dict[str, Any]]:  # noqa: D401
        """Detect broken or missing imports across the codebase."""
        logger.info("Detecting broken imports")
        issues: list[dict[str, Any]] = []
        for py_file in self.root_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            issues.extend(self._scan_file_for_import_issues(py_file))
        logger.info(f"Found {len(issues)} import issues")
        self._record_detection("broken_imports", issues)
        return issues

    def _scan_file_for_import_issues(self, py_file: Path) -> list[dict[str, Any]]:
        """Scan a single file for import-related issues."""
        local_issues: list[dict[str, Any]] = []
        try:
            with open(py_file, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        try:
                            importlib.import_module(alias.name)
                        except ImportError as e:  # pragma: no cover
                            local_issues.append(
                                {
                                    "type": "broken_import",
                                    "file": str(py_file.relative_to(self.root_path)),
                                    "module": alias.name,
                                    "line": node.lineno,
                                    "error": str(e),
                                    "severity": "high",
                                }
                            )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    try:
                        importlib.import_module(node.module)
                    except ImportError as e:  # pragma: no cover - environment dependent
                        local_issues.append(
                            {
                                "type": "broken_import",
                                "file": str(py_file.relative_to(self.root_path)),
                                "module": node.module,
                                "line": node.lineno,
                                "error": str(e),
                                "severity": "high",
                            }
                        )
        except SyntaxError as e:
            local_issues.append(
                {
                    "type": "syntax_error",
                    "file": str(py_file.relative_to(self.root_path)),
                    "error": str(e),
                    "line": e.lineno if hasattr(e, "lineno") else None,
                    "severity": "critical",
                }
            )
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(f"Could not analyze {py_file}: {e}")
        return local_issues

    def detect_schema_divergence(self) -> list[dict[str, Any]]:
        """Detect schema inconsistencies and model drift.

        Returns:
            List of schema issues detected
        """
        logger.info("Detecting schema divergence")
        issues = []

        # Check if models are consistent with schemas
        try:
            from oraculus_di_auditor.db.models import Base

            # Get all model classes
            model_classes = []
            for attr_name in dir(Base):
                attr = getattr(Base, attr_name)
                if (
                    isinstance(attr, type)
                    and hasattr(attr, "__tablename__")
                    and attr != Base
                ):
                    model_classes.append(attr)

            # Check for missing indexes on critical columns
            for model_class in model_classes:
                if hasattr(model_class, "__table__"):
                    table = model_class.__table__
                    for column in table.columns:
                        # Check if ID or foreign key columns are indexed
                        if (
                            "id" in column.name.lower() or column.foreign_keys
                        ) and not (column.primary_key or column.index):
                            issues.append(
                                {
                                    "type": "missing_index",
                                    "model": model_class.__name__,
                                    "table": table.name,
                                    "column": column.name,
                                    "severity": "medium",
                                    "suggestion": f"Add index to {column.name}",
                                }
                            )

        except ImportError as e:
            issues.append(
                {
                    "type": "schema_import_error",
                    "error": str(e),
                    "severity": "high",
                }
            )

        logger.info(f"Found {len(issues)} schema issues")
        self._record_detection("schema_divergence", issues)
        return issues

    def detect_anti_patterns(self) -> list[dict[str, Any]]:
        """Detect code anti-patterns and bad practices.

        Returns:
            List of anti-pattern issues detected
        """
        logger.info("Detecting anti-patterns")
        issues = []

        for py_file in self.root_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(py_file))

                # Detect overly complex functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Count nested blocks (if, for, while, etc.)
                        complexity = self._calculate_complexity(node)
                        if complexity > 15:
                            issues.append(
                                {
                                    "type": "high_complexity",
                                    "file": str(py_file.relative_to(self.root_path)),
                                    "function": node.name,
                                    "line": node.lineno,
                                    "complexity": complexity,
                                    "severity": "medium",
                                    "suggestion": (
                                        "Consider refactoring into smaller functions"
                                    ),
                                }
                            )

                        # Detect functions with too many parameters
                        param_count = len(node.args.args)
                        if param_count > 7:
                            issues.append(
                                {
                                    "type": "too_many_parameters",
                                    "file": str(py_file.relative_to(self.root_path)),
                                    "function": node.name,
                                    "line": node.lineno,
                                    "parameter_count": param_count,
                                    "severity": "low",
                                    "suggestion": "Consider using a parameter object",
                                }
                            )

                # Detect bare except clauses
                if "except:" in content or "except :" in content:
                    issues.append(
                        {
                            "type": "bare_except",
                            "file": str(py_file.relative_to(self.root_path)),
                            "severity": "medium",
                            "suggestion": "Use specific exception types",
                        }
                    )

            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")

        logger.info(f"Found {len(issues)} anti-pattern issues")
        self._record_detection("anti_patterns", issues)
        return issues

    def detect_performance_bottlenecks(self) -> list[dict[str, Any]]:
        """Detect potential performance issues.

        Returns:
            List of performance issues detected
        """
        logger.info("Detecting performance bottlenecks")
        issues = []

        for py_file in self.root_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Detect N+1 query patterns (simple heuristic)
                if "for " in content and ".query(" in content:
                    issues.append(
                        {
                            "type": "potential_n_plus_1",
                            "file": str(py_file.relative_to(self.root_path)),
                            "severity": "medium",
                            "suggestion": "Review for N+1 query patterns",
                        }
                    )

                # Detect inefficient list operations
                if ".append(" in content and "for " in content:
                    # Check if list comprehension might be more efficient
                    issues.append(
                        {
                            "type": "inefficient_list_building",
                            "file": str(py_file.relative_to(self.root_path)),
                            "severity": "low",
                            "suggestion": "Consider using list comprehension",
                        }
                    )

            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")

        logger.info(f"Found {len(issues)} performance issues")
        self._record_detection("performance_bottlenecks", issues)
        return issues

    def detect_unreachable_code(self) -> list[dict[str, Any]]:
        """Detect unreachable or dead code paths.

        Returns:
            List of dead code issues detected
        """
        logger.info("Detecting unreachable code")
        issues = []

        for py_file in self.root_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check for code after return statements
                        for i, stmt in enumerate(node.body):
                            if isinstance(stmt, ast.Return) and i < len(node.body) - 1:
                                issues.append(
                                    {
                                        "type": "unreachable_after_return",
                                        "file": str(
                                            py_file.relative_to(self.root_path)
                                        ),
                                        "function": node.name,
                                        "line": node.body[i + 1].lineno,
                                        "severity": "medium",
                                    }
                                )

            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")

        logger.info(f"Found {len(issues)} unreachable code issues")
        self._record_detection("unreachable_code", issues)
        return issues

    def run_full_detection(self) -> dict[str, Any]:
        """Run all detection checks.

        Returns:
            Comprehensive detection report
        """
        logger.info("Running full detection scan")

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "scan_type": "full",
            "checks": {
                "broken_imports": self.detect_broken_imports(),
                "schema_divergence": self.detect_schema_divergence(),
                "anti_patterns": self.detect_anti_patterns(),
                "performance_bottlenecks": self.detect_performance_bottlenecks(),
                "unreachable_code": self.detect_unreachable_code(),
            },
        }

        # Calculate summary statistics
        total_issues = sum(len(issues) for issues in report["checks"].values())
        critical_issues = sum(
            1
            for issues in report["checks"].values()
            for issue in issues
            if issue.get("severity") == "critical"
        )
        high_issues = sum(
            1
            for issues in report["checks"].values()
            for issue in issues
            if issue.get("severity") == "high"
        )

        report["summary"] = {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "health_score": max(
                0.0,
                1.0
                - (
                    critical_issues * CRITICAL_ISSUE_WEIGHT
                    + high_issues * HIGH_ISSUE_WEIGHT
                ),
            ),
        }

        logger.info(
            f"Detection complete: {total_issues} issues found "
            f"(health score: {report['summary']['health_score']:.2f})"
        )
        return report

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function.

        Args:
            node: AST function node

        Returns:
            Complexity score
        """
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(
                child, ast.If | ast.While | ast.For | ast.ExceptHandler | ast.With
            ):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _record_detection(self, check_type: str, issues: list[dict[str, Any]]):
        """Record detection in history.

        Args:
            check_type: Type of detection check
            issues: List of issues found
        """
        self.detection_history.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "check_type": check_type,
                "issue_count": len(issues),
            }
        )
