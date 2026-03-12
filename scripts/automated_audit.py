#!/usr/bin/env python3
"""
Automated Repository Audit Script

This script performs comprehensive automated triage and audit of the entire
repository structure, code quality, configuration, documentation, security,
and compliance aspects.

It generates a detailed plain-text audit report (AUDIT_REPORT.txt) with:
- Repository Overview
- File-by-File Findings
- Global Flags and Issues
- Recommendations

Requirements: Python 3.11+ (uses datetime.UTC)

Author: GitHub Copilot Agent
Date: 2025-01-15
"""

import ast
import json
import os
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RepositoryAuditor:
    """Comprehensive repository auditor."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.findings = []
        self.global_flags = []
        self.stats = {
            "total_files": 0,
            "total_dirs": 0,
            "python_files": 0,
            "test_files": 0,
            "config_files": 0,
            "doc_files": 0,
            "total_lines": 0,
            "code_lines": 0,
        }
        self.file_types = defaultdict(int)

        # Common patterns to skip
        self.skip_patterns = {
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            ".pytest_cache",
            "dist",
            "build",
            "*.egg-info",
            ".mypy_cache",
            ".ruff_cache",
            ".coverage",
            "htmlcov",
        }

        # Specific filenames to skip (generated/runtime artifacts)
        self.skip_filenames = {
            "AUDIT_REPORT.txt",
        }

    def should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        if path.name in self.skip_filenames:
            return True
        path_str = str(path)
        for pattern in self.skip_patterns:
            if pattern.replace("*", "") in path_str:
                return True
        return False

    def scan_repository(self):
        """Scan entire repository structure."""
        print("Scanning repository structure...")

        for root, dirs, files in os.walk(self.repo_root):
            root_path = Path(root)

            # Skip certain directories
            dirs[:] = [d for d in dirs if not self.should_skip(root_path / d)]

            if self.should_skip(root_path):
                continue

            self.stats["total_dirs"] += len(dirs)

            for file in files:
                file_path = root_path / file
                if self.should_skip(file_path):
                    continue

                self.stats["total_files"] += 1
                self.analyze_file(file_path)

    def analyze_file(self, file_path: Path):
        """Analyze individual file."""
        relative_path = file_path.relative_to(self.repo_root)

        # Track file type
        suffix = file_path.suffix.lower()
        self.file_types[suffix if suffix else "no_extension"] += 1

        # Get file size
        try:
            file_size = file_path.stat().st_size
        except Exception:
            file_size = 0

        # Initialize finding
        finding = {
            "path": str(relative_path),
            "type": self.classify_file(file_path),
            "size": file_size,
            "issues": [],
            "warnings": [],
            "notes": [],
        }

        # Analyze based on file type
        if file_path.suffix == ".py":
            self.stats["python_files"] += 1
            self.analyze_python_file(file_path, finding)
        elif file_path.suffix in {".md", ".rst", ".txt"}:
            self.stats["doc_files"] += 1
            self.analyze_documentation(file_path, finding)
        elif file_path.name in {
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "setup.cfg",
            "package.json",
            ".gitignore",
        }:
            self.stats["config_files"] += 1
            self.analyze_config_file(file_path, finding)
        elif file_path.suffix in {".json", ".yaml", ".yml"}:
            self.analyze_data_file(file_path, finding)

        # Security checks for all files
        self.check_security_issues(file_path, finding)

        # Only add finding if there are issues, warnings, or notes
        if finding["issues"] or finding["warnings"] or finding["notes"]:
            self.findings.append(finding)

    def classify_file(self, file_path: Path) -> str:
        """Classify file type."""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        if suffix == ".py":
            if "test_" in name or "_test" in name:
                self.stats["test_files"] += 1
                return "Python Test"
            return "Python Source"
        elif suffix in {".md", ".rst", ".txt"}:
            return "Documentation"
        elif suffix in {".json", ".yaml", ".yml"}:
            return "Configuration/Data"
        elif suffix in {".toml", ".cfg", ".ini"}:
            return "Configuration"
        elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
            return "JavaScript/TypeScript"
        elif suffix in {".html", ".css", ".scss"}:
            return "Web Asset"
        elif suffix in {".sh", ".bash"}:
            return "Shell Script"
        elif suffix == "":
            return "Script/Executable"
        else:
            return f"Other ({suffix})"

    def analyze_python_file(self, file_path: Path, finding: dict):
        """Analyze Python source file."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            finding["issues"].append(f"Cannot read file: {e}")
            return

        lines = content.splitlines()
        self.stats["total_lines"] += len(lines)

        # Count code lines (non-empty, non-comment)
        code_lines = sum(
            1 for line in lines if line.strip() and not line.strip().startswith("#")
        )
        self.stats["code_lines"] += code_lines

        # Check file size
        if len(lines) > 1000:
            finding["warnings"].append(f"Large file: {len(lines)} lines")

        # Parse AST for deeper analysis and accurate docstring detection
        try:
            tree = ast.parse(content)

            # Check for module docstring using AST (handles shebangs correctly)
            module_docstring = ast.get_docstring(tree)
            if not module_docstring:
                finding["warnings"].append("Missing module docstring")

            self.analyze_python_ast(tree, finding)
        except SyntaxError as e:
            finding["issues"].append(f"Syntax error: {e}")
        except Exception as e:
            finding["notes"].append(f"Could not parse AST: {e}")

        # Check for common code quality issues
        self.check_python_patterns(content, finding)

    def analyze_python_ast(self, tree: ast.AST, finding: dict):
        """Analyze Python AST for code quality issues."""
        classes_without_docstrings = 0
        functions_without_docstrings = 0
        complex_functions = 0

        for node in ast.walk(tree):
            # Check class docstrings
            if isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    classes_without_docstrings += 1

            # Check function docstrings and complexity
            elif isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    functions_without_docstrings += 1

                # Simple complexity check (count nested blocks)
                complexity = sum(
                    1
                    for _ in ast.walk(node)
                    if isinstance(_, ast.If | ast.For | ast.While | ast.With)
                )
                if complexity > 10:
                    complex_functions += 1

        if classes_without_docstrings > 0:
            finding["warnings"].append(
                f"{classes_without_docstrings} class(es) missing docstrings"
            )

        if functions_without_docstrings > 0:
            finding["warnings"].append(
                f"{functions_without_docstrings} function(s) missing docstrings"
            )

        if complex_functions > 0:
            finding["warnings"].append(
                f"{complex_functions} complex function(s) (high cyclomatic complexity)"
            )

    def check_python_patterns(self, content: str, finding: dict):
        """Check for common Python patterns and anti-patterns."""
        # Check for bare except
        if re.search(r"except\s*:", content):
            finding["warnings"].append("Bare except clause detected")

        # Check for TODO/FIXME
        todos = len(re.findall(r"#\s*TODO", content, re.IGNORECASE))
        fixmes = len(re.findall(r"#\s*FIXME", content, re.IGNORECASE))

        if todos > 0:
            finding["notes"].append(f"{todos} TODO comment(s)")
        if fixmes > 0:
            finding["notes"].append(f"{fixmes} FIXME comment(s)")

        # Check for print statements (possible debug code)
        print_count = len(re.findall(r"\bprint\s*\(", content))
        if print_count > 5:
            finding["notes"].append(
                f"{print_count} print statements (possible debug code)"
            )

    def analyze_documentation(self, file_path: Path, finding: dict):
        """Analyze documentation files."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            finding["issues"].append(f"Cannot read file: {e}")
            return

        lines = content.splitlines()
        self.stats["total_lines"] += len(lines)

        # Check for empty documentation
        if len(content.strip()) < 100:
            finding["warnings"].append("Very short documentation")

        # Check for broken links (basic check)
        broken_links = re.findall(r"\[.*?\]\(\s*\)", content)
        if broken_links:
            finding["warnings"].append(
                f"{len(broken_links)} potentially broken link(s)"
            )

        # Check for potentially outdated year references in relevant contexts
        current_year = datetime.now(UTC).year
        outdated_context_keywords = (
            "copyright",
            "©",
            "last updated",
            "last modified",
            "updated",
            "since",
        )
        has_potentially_outdated_years = False
        for line in lines:
            lower_line = line.lower()
            if not any(keyword in lower_line for keyword in outdated_context_keywords):
                continue
            years_in_line = re.findall(r"\b20\d{2}\b", line)
            if years_in_line and all(
                int(year) < current_year - 1 for year in years_in_line
            ):
                has_potentially_outdated_years = True
                break
        if has_potentially_outdated_years:
            finding["notes"].append("Contains potentially outdated year references")

    def analyze_config_file(self, file_path: Path, finding: dict):
        """Analyze configuration files."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            finding["issues"].append(f"Cannot read file: {e}")
            return

        # Check for hardcoded sensitive values
        if re.search(
            r"(password|secret|token|api[_-]?key)\s*[:=]", content, re.IGNORECASE
        ):
            finding["warnings"].append("Possible hardcoded credentials or secrets")

        # Check for development/debug settings
        if re.search(r"debug\s*[:=]\s*true", content, re.IGNORECASE):
            finding["notes"].append("Debug mode enabled")

        # JSON/YAML validation
        if file_path.suffix == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                finding["issues"].append(f"Invalid JSON: {e}")

        # Requirements.txt checks
        if file_path.name == "requirements.txt":
            unpinned = [
                line.strip()
                for line in content.splitlines()
                if line.strip()
                and not any(c in line for c in ["==", ">=", "<=", "~="])
                and not line.strip().startswith("#")
            ]
            if unpinned:
                finding["warnings"].append(f"{len(unpinned)} unpinned dependencies")

    def analyze_data_file(self, file_path: Path, finding: dict):
        """Analyze JSON/YAML data files."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            finding["issues"].append(f"Cannot read file: {e}")
            return

        # Check file size for data files
        if len(content) > 1000000:  # 1MB
            finding["warnings"].append(f"Large data file: {len(content)} bytes")

        # Validate JSON
        if file_path.suffix == ".json":
            try:
                data = json.loads(content)
                # Check for PII in JSON
                self.check_json_for_pii(data, finding)
            except json.JSONDecodeError as e:
                finding["issues"].append(f"Invalid JSON: {e}")

    def check_json_for_pii(self, data: Any, finding: dict):
        """Check JSON data for potential PII."""
        pii_keys = {
            "email",
            "phone",
            "ssn",
            "social_security",
            "password",
            "credit_card",
            "address",
            "phone_number",
        }

        def check_dict(d, path=""):
            if isinstance(d, dict):
                for key, value in d.items():
                    new_path = f"{path}.{key}" if path else key
                    if any(pii in key.lower() for pii in pii_keys):
                        finding["warnings"].append(f"Potential PII field: {new_path}")
                    check_dict(value, new_path)
            elif isinstance(d, list):
                for i, item in enumerate(d):
                    check_dict(item, f"{path}[{i}]")

        check_dict(data)

    def check_security_issues(self, file_path: Path, finding: dict):
        """Check for common security issues."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        # Skip security checks on this file itself and in test files
        relative_path = str(file_path.relative_to(self.repo_root))
        if "automated_audit.py" in relative_path:
            return

        # Check for hardcoded secrets patterns
        secret_patterns = [
            (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]([^'\"]+)['\"]", "password"),
            (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]([^'\"]+)['\"]", "API key"),
            (r"(?i)(secret|token)\s*[:=]\s*['\"]([^'\"]+)['\"]", "secret/token"),
            (
                r"(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]\s*['\"]",
                "AWS credentials",
            ),
            (r"(?i)(private[_-]?key|privatekey)\s*[:=]\s*['\"]", "private key"),
        ]

        for pattern, name in secret_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Filter out obvious placeholders, patterns in regex, and docs.
                # Only inspect the actual credential value (last capture group),
                # not the entire match tuple, to avoid over-filtering.
                real_matches = []
                for m in matches:
                    if isinstance(m, tuple):
                        candidate = m[-1] if len(m) > 0 else m
                    else:
                        candidate = m
                    candidate_lower = str(candidate).lower()
                    if not any(
                        p in candidate_lower
                        for p in [
                            "example",
                            "placeholder",
                            "your_",
                            "xxx",
                            "***",
                            "pattern",
                            r"(?i)",
                            "regex",
                            "re.findall",
                            "re.search",
                        ]
                    ):
                        real_matches.append(m)
                if real_matches:
                    finding["issues"].append(f"Possible hardcoded {name} detected")

        # Check for SQL injection vulnerabilities (basic)
        if file_path.suffix == ".py":
            sql_patterns = [
                r"execute\([^)]*%s",
                r"execute\([^)]*\.format\(",
                r"execute\([^)]*\+",
            ]
            for pattern in sql_patterns:
                if re.search(pattern, content):
                    finding["warnings"].append(
                        "Potential SQL injection vulnerability "
                        "(string formatting in execute)"
                    )
                    break

    def generate_global_flags(self):
        """Generate global repository flags."""
        print("Generating global flags...")

        # Check for required files
        required_files = ["README.md", "LICENSE", "requirements.txt", ".gitignore"]
        for req_file in required_files:
            if not (self.repo_root / req_file).exists():
                self.global_flags.append(
                    {
                        "severity": "medium",
                        "category": "documentation",
                        "message": f"Missing {req_file}",
                    }
                )

        # Check test coverage
        if self.stats["python_files"] > 0:
            test_ratio = self.stats["test_files"] / self.stats["python_files"]
            if test_ratio < 0.3:
                self.global_flags.append(
                    {
                        "severity": "medium",
                        "category": "testing",
                        "message": f"Low test coverage ratio: {test_ratio:.2%} "
                        f"({self.stats['test_files']} tests for "
                        f"{self.stats['python_files']} source files)",
                    }
                )

        # Check for large files
        large_files = [f for f in self.findings if f["size"] > 1000000]  # 1MB
        if large_files:
            self.global_flags.append(
                {
                    "severity": "low",
                    "category": "structure",
                    "message": f"{len(large_files)} large files (>1MB) detected",
                }
            )

        # Check for security issues
        security_issues = sum(
            len(f["issues"])
            for f in self.findings
            if any(
                "security" in i.lower() or "credential" in i.lower()
                for i in f["issues"]
            )
        )
        if security_issues > 0:
            self.global_flags.append(
                {
                    "severity": "high",
                    "category": "security",
                    "message": (
                        f"{security_issues} potential security issue(s) detected"
                    ),
                }
            )

        # Count total issues by severity
        total_issues = sum(len(f["issues"]) for f in self.findings)
        total_warnings = sum(len(f["warnings"]) for f in self.findings)

        if total_issues > 0:
            self.global_flags.append(
                {
                    "severity": "info",
                    "category": "summary",
                    "message": f"Total issues: {total_issues}",
                }
            )

        if total_warnings > 0:
            self.global_flags.append(
                {
                    "severity": "info",
                    "category": "summary",
                    "message": f"Total warnings: {total_warnings}",
                }
            )

    def generate_recommendations(self) -> list[str]:
        """Generate audit recommendations."""
        recommendations = []

        # Documentation recommendations
        if not (self.repo_root / "LICENSE").exists():
            recommendations.append(
                "Add a LICENSE file to clarify the legal terms of use"
            )

        # Testing recommendations
        if self.stats["python_files"] > 0:
            test_ratio = self.stats["test_files"] / self.stats["python_files"]
            if test_ratio < 0.5:
                recommendations.append(
                    f"Improve test coverage: current ratio is {test_ratio:.2%}. "
                    "Aim for at least 50% (1 test file per 2 source files)"
                )

        # Code quality recommendations
        missing_docstrings = sum(
            1
            for f in self.findings
            if any("docstring" in w.lower() for w in f.get("warnings", []))
        )
        if missing_docstrings > 5:
            recommendations.append(
                f"{missing_docstrings} files with missing docstrings. "
                "Add docstrings to improve code documentation"
            )

        # Security recommendations
        security_findings = [
            f
            for f in self.findings
            if any(
                "credential" in i.lower() or "secret" in i.lower()
                for i in f.get("issues", []) + f.get("warnings", [])
            )
        ]
        if security_findings:
            recommendations.append(
                f"{len(security_findings)} files with potential security issues. "
                "Review for hardcoded credentials and secrets"
            )

        # Configuration recommendations
        if (self.repo_root / "requirements.txt").exists():
            unpinned_deps = [
                f
                for f in self.findings
                if f["path"] == "requirements.txt"
                and any("unpinned" in w for w in f.get("warnings", []))
            ]
            if unpinned_deps:
                recommendations.append(
                    "Pin dependency versions in requirements.txt "
                    "for reproducible builds"
                )

        # General recommendations
        if self.stats["total_files"] > 1000:
            recommendations.append(
                f"Large repository with {self.stats['total_files']} files. "
                "Consider modularization and cleanup of unused files"
            )

        if not recommendations:
            recommendations.append(
                "No critical recommendations. Repository structure appears healthy."
            )

        return recommendations

    def generate_report(self, output_path: Path):
        """Generate comprehensive audit report."""
        print(f"Generating audit report: {output_path}")

        report_lines = []

        # Header
        report_lines.extend(
            [
                "=" * 80,
                "AUTOMATED REPOSITORY AUDIT REPORT",
                "=" * 80,
                "",
                f"Generated: {datetime.now(UTC).isoformat().replace('+00:00', 'Z')}",
                f"Repository: {self.repo_root.name}",
                f"Repository Path: {self.repo_root}",
                "",
            ]
        )

        # Repository Overview
        report_lines.extend(
            [
                "=" * 80,
                "REPOSITORY OVERVIEW",
                "=" * 80,
                "",
                f"Total Directories: {self.stats['total_dirs']}",
                f"Total Files: {self.stats['total_files']}",
                f"Python Files: {self.stats['python_files']}",
                f"Test Files: {self.stats['test_files']}",
                f"Configuration Files: {self.stats['config_files']}",
                f"Documentation Files: {self.stats['doc_files']}",
                f"Total Lines: {self.stats['total_lines']:,}",
                f"Code Lines: {self.stats['code_lines']:,}",
                "",
                "File Types Distribution:",
            ]
        )

        # Sort file types by count
        sorted_types = sorted(self.file_types.items(), key=lambda x: x[1], reverse=True)
        for ext, count in sorted_types[:15]:  # Top 15
            report_lines.append(f"  {ext:20s}: {count:5d}")

        report_lines.append("")

        # Global Flags
        report_lines.extend(
            [
                "=" * 80,
                "GLOBAL FLAGS AND ISSUES",
                "=" * 80,
                "",
            ]
        )

        if self.global_flags:
            for flag in self.global_flags:
                severity = flag["severity"].upper()
                category = flag["category"].upper()
                message = flag["message"]
                report_lines.append(f"[{severity}] [{category}] {message}")
        else:
            report_lines.append("No global flags detected.")

        report_lines.append("")

        # File-by-File Findings
        report_lines.extend(
            [
                "=" * 80,
                "FILE-BY-FILE FINDINGS",
                "=" * 80,
                "",
                f"Files with findings: {len(self.findings)}",
                "",
            ]
        )

        # Sort findings by severity (issues first, then warnings)
        sorted_findings = sorted(
            self.findings,
            key=lambda f: (-len(f["issues"]), -len(f["warnings"]), f["path"]),
        )

        for finding in sorted_findings:
            report_lines.extend(
                [
                    "-" * 80,
                    f"File: {finding['path']}",
                    f"Type: {finding['type']}",
                    f"Size: {finding['size']:,} bytes",
                    "",
                ]
            )

            if finding["issues"]:
                report_lines.append("ISSUES:")
                for issue in finding["issues"]:
                    report_lines.append(f"  • {issue}")
                report_lines.append("")

            if finding["warnings"]:
                report_lines.append("WARNINGS:")
                for warning in finding["warnings"]:
                    report_lines.append(f"  • {warning}")
                report_lines.append("")

            if finding["notes"]:
                report_lines.append("NOTES:")
                for note in finding["notes"]:
                    report_lines.append(f"  • {note}")
                report_lines.append("")

        # Recommendations
        recommendations = self.generate_recommendations()
        report_lines.extend(
            [
                "=" * 80,
                "RECOMMENDATIONS",
                "=" * 80,
                "",
            ]
        )

        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
            report_lines.append("")

        # Footer
        report_lines.extend(
            [
                "=" * 80,
                "END OF AUDIT REPORT",
                "=" * 80,
                "",
                "This report was generated automatically by the " "Oraculus-DI-Auditor",
                "automated audit script. Manual review is recommended for all "
                "findings.",
                "",
                "Note: This audit tool performs automated static analysis and "
                "triage.",
                "It does not replace manual code review or security audits by "
                "qualified",
                "professionals. Use findings as guidance for deeper " "investigation.",
                "",
            ]
        )

        # Write report
        report_text = "\n".join(report_lines)
        output_path.write_text(report_text, encoding="utf-8")
        print(f"[OK] Audit report generated: {output_path}")
        print(f"  Total findings: {len(self.findings)}")
        print(f"  Global flags: {len(self.global_flags)}")
        print(f"  Recommendations: {len(recommendations)}")


def main():
    """Main entry point."""
    # Determine repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    print("=" * 80)
    print("Oraculus-DI-Auditor - Automated Repository Audit")
    print("=" * 80)
    print()
    print(f"Repository: {repo_root}")
    print(f"Started: {datetime.now(UTC).isoformat().replace('+00:00', 'Z')}")
    print()

    # Create auditor
    auditor = RepositoryAuditor(repo_root)

    # Scan repository
    auditor.scan_repository()

    # Generate global flags
    auditor.generate_global_flags()

    # Generate report
    output_path = repo_root / "AUDIT_REPORT.txt"
    auditor.generate_report(output_path)

    print()
    print("=" * 80)
    print("Audit Complete")
    print("=" * 80)
    print(f"Report location: {output_path}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
