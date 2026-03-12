"""
JIM Core - Main orchestration engine for Judicial Interpretive Matrix.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.jim.jim_case_loader import JIMCaseLoader
from scripts.jim.jim_correlation_engine import JIMCorrelationEngine
from scripts.jim.jim_risk_scoring import JIMRiskScoring


class JIMCore:
    """
    Main Judicial Interpretive Matrix engine.

    Orchestrates legal analysis by:
    1. Loading case law and doctrinal frameworks
    2. Correlating anomalies to legal precedents
    3. Scoring constitutional and administrative risks
    4. Generating comprehensive legal reports
    """

    VERSION = "1.0.0"

    def __init__(self, cases_dir: Path | None = None, output_dir: Path | None = None):
        """
        Initialize JIM core engine.

        Args:
            cases_dir: Directory containing case law JSON files
            output_dir: Directory for JIM output artifacts
        """
        # Initialize components
        self.case_loader = JIMCaseLoader(cases_dir)
        self.correlation_engine = None  # Initialized after case loading
        self.risk_scorer = JIMRiskScoring()

        # Set output directory
        if output_dir is None:
            repo_root = Path(__file__).parent.parent.parent
            output_dir = repo_root / "analysis" / "jim"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # State
        self.case_index_loaded = False
        self.harmonization_matrix: dict[str, Any] = {}  # MSH-v1 integration
        self.current_era: int | None = None  # MSH-v1: era-specific analysis
        self.anomalies: list[dict[str, Any]] = []
        self.correlations: list[dict[str, Any]] = []
        self.risk_assessments: list[dict[str, Any]] = []

    def initialize(self) -> dict[str, Any]:
        """
        Initialize JIM engine by loading case law database.

        Returns:
            Initialization report with status and metadata.
        """
        try:
            # Load SCOTUS case index
            self.case_loader.load_scotus_index()

            # Validate loaded cases
            validation = self.case_loader.validate_index()

            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "Case index validation failed",
                    "validation_errors": validation["errors"],
                }

            # Initialize correlation engine with loaded cases
            self.correlation_engine = JIMCorrelationEngine(self.case_loader)

            self.case_index_loaded = True

            metadata = self.case_loader.get_metadata()

            return {
                "success": True,
                "version": self.VERSION,
                "cases_loaded": metadata["total_cases_loaded"],
                "doctrines": metadata["doctrines"],
                "year_range": metadata["year_range"],
                "validation": validation,
            }

        except FileNotFoundError as e:
            return {
                "success": False,
                "error": f"Case law file not found: {e}",
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in case law file: {e}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Initialization error: {e}",
            }

    def load_harmonization_matrix(
        self, harmonization_matrix: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Load semantic harmonization matrix for era-specific analysis.

        MSH-v1 Integration: Loads harmonized legal definitions from semantic
        harmonization engine to enable era-specific doctrinal analysis.

        Args:
            harmonization_matrix: Dictionary mapping terms to harmonized meanings

        Returns:
            Status report with loaded term count
        """
        self.harmonization_matrix = harmonization_matrix

        return {
            "success": True,
            "terms_loaded": len(harmonization_matrix),
            "era": self.current_era,
        }

    def set_era(self, era: int) -> dict[str, Any]:
        """
        Set analysis era for temporal legal interpretation.

        MSH-v1 Integration: Sets the era year for applying era-specific
        definitions from harmonization matrix (e.g., 1791 for Constitutional
        Founding era, 2024 for contemporary era).

        Args:
            era: Year representing the era (e.g., 1791, 1868, 2024)

        Returns:
            Status report confirming era setting
        """
        self.current_era = era

        return {
            "success": True,
            "era": era,
            "harmonization_loaded": len(self.harmonization_matrix) > 0,
        }

    def analyze_anomalies(self, anomalies: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze anomalies through JIM legal framework.

        Args:
            anomalies: List of anomalies from audit systems (ACE, VICFM, CAIM, PDF)

        Returns:
            Analysis report with correlations and risk scores.
        """
        if not self.case_index_loaded:
            raise RuntimeError("JIM not initialized. Call initialize() first.")

        self.anomalies = anomalies

        # Correlate anomalies to legal doctrines and cases
        correlation_result = self.correlation_engine.correlate_multiple_anomalies(
            anomalies
        )
        self.correlations = correlation_result["individual_correlations"]

        # Score each correlated anomaly
        self.risk_assessments = []
        for anomaly, correlation in zip(anomalies, self.correlations, strict=True):
            risk_assessment = self.risk_scorer.score_anomaly(anomaly, correlation)
            risk_assessment["anomaly_id"] = correlation["anomaly_id"]
            risk_assessment["correlation"] = correlation
            self.risk_assessments.append(risk_assessment)

        # Generate aggregate risk report
        aggregate_risk = self.risk_scorer.aggregate_risk_report(self.risk_assessments)

        return {
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "total_anomalies_analyzed": len(anomalies),
            "correlation_summary": {
                "doctrine_frequency": correlation_result["doctrine_frequency"],
                "dominant_doctrines": correlation_result["dominant_doctrines"],
                "dominant_cases": correlation_result["dominant_cases"],
                "systemic_patterns": correlation_result["systemic_patterns"],
            },
            "risk_summary": aggregate_risk,
            "individual_assessments": self.risk_assessments,
        }

    def generate_reports(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """
        Generate JIM output reports.

        Args:
            analysis_result: Result from analyze_anomalies()

        Returns:
            Report generation status with file paths.
        """
        generated_files = {}

        try:
            # Generate JIM_REPORT.json
            jim_report = self._create_jim_report(analysis_result)
            report_path = self.output_dir / "JIM_REPORT.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(jim_report, f, indent=2, ensure_ascii=False)
            generated_files["JIM_REPORT.json"] = str(report_path)

            # Generate JIM_SUMMARY.md
            summary_md = self._create_summary_markdown(analysis_result)
            summary_path = self.output_dir / "JIM_SUMMARY.md"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary_md)
            generated_files["JIM_SUMMARY.md"] = str(summary_path)

            # Generate CASE_LINKAGE_GRAPH.json
            linkage_graph = self._create_linkage_graph(analysis_result)
            graph_path = self.output_dir / "CASE_LINKAGE_GRAPH.json"
            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(linkage_graph, f, indent=2, ensure_ascii=False)
            generated_files["CASE_LINKAGE_GRAPH.json"] = str(graph_path)

            return {
                "success": True,
                "generated_files": generated_files,
                "output_directory": str(self.output_dir),
            }

        except (FileNotFoundError, PermissionError) as e:
            return {
                "success": False,
                "error": f"File I/O error: {e}",
                "generated_files": generated_files,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Report generation error: {e}",
                "generated_files": generated_files,
            }

    def _create_jim_report(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """Create comprehensive JIM report JSON."""
        return {
            "version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "metadata": {
                "total_anomalies": analysis_result["total_anomalies_analyzed"],
                "case_law_version": self.case_loader.scotus_index.get("version"),
            },
            "executive_summary": {
                "risk_distribution": analysis_result["risk_summary"][
                    "risk_distribution"
                ],
                "high_priority_count": analysis_result["risk_summary"][
                    "high_priority_count"
                ],
                "requires_immediate_review": analysis_result["risk_summary"][
                    "requires_immediate_review"
                ],
                "average_risk_score": analysis_result["risk_summary"]["average_score"],
            },
            "doctrinal_analysis": {
                "doctrine_frequency": analysis_result["correlation_summary"][
                    "doctrine_frequency"
                ],
                "dominant_doctrines": analysis_result["correlation_summary"][
                    "dominant_doctrines"
                ],
                "systemic_patterns": analysis_result["correlation_summary"][
                    "systemic_patterns"
                ],
            },
            "case_law_citations": {
                "dominant_cases": analysis_result["correlation_summary"][
                    "dominant_cases"
                ],
            },
            "individual_findings": analysis_result["individual_assessments"],
            "critical_findings": analysis_result["risk_summary"]["critical_findings"],
        }

    def _create_summary_markdown(  # noqa: C901
        self, analysis_result: dict[str, Any]
    ) -> str:
        """Create executive summary markdown."""
        risk_summary = analysis_result["risk_summary"]
        correlation_summary = analysis_result["correlation_summary"]

        md = (
            f"""# Judicial Interpretive Matrix (JIM) - Executive Summary

**Generated:** {analysis_result['analysis_timestamp']}
**JIM Version:** {self.VERSION}

---

## Overview

This report presents the legal analysis of """
            f"""{analysis_result['total_anomalies_analyzed']} anomalies detected by """
            """the Oraculus-DI-Auditor system, evaluated against constitutional """
            """doctrines, Supreme Court precedents, and administrative law """
            """principles.

---

## Risk Assessment

### Overall Statistics

"""
            f"""- **Total Anomalies Analyzed:** """
            f"""{analysis_result['total_anomalies_analyzed']}
- **Average Risk Score:** {risk_summary['average_score']:.3f}
- **High Priority Issues:** {risk_summary['high_priority_count']}
- **Requires Immediate Review:** {
    'Yes' if risk_summary['requires_immediate_review'] else 'No'
}

### Risk Distribution

| Severity | Count |
|----------|-------|
"""
        )

        for severity in ["critical", "high", "medium", "low", "minimal"]:
            count = risk_summary["risk_distribution"].get(severity, 0)
            md += f"| {severity.capitalize()} | {count} |\n"

        md += (
            "\n---\n\n## Doctrinal Analysis\n\n"
            "### Most Frequently Implicated Doctrines\n\n"
        )

        for doctrine, count in correlation_summary["dominant_doctrines"]:
            md += f"- **{doctrine.replace('_', ' ').title()}**: {count} instances\n"

        md += "\n### Systemic Patterns Identified\n\n"

        if correlation_summary["systemic_patterns"]:
            for pattern in correlation_summary["systemic_patterns"]:
                md += f"- {pattern}\n"
        else:
            md += "No systemic patterns identified.\n"

        md += (
            "\n---\n\n## Case Law Citations\n\n"
            "### Most Relevant Supreme Court Cases\n\n"
        )

        # Get top cases
        case_ids = [case_id for case_id, _ in correlation_summary["dominant_cases"]]
        for case_id in case_ids[:5]:
            case = self.case_loader.get_case_by_id(case_id)
            if case:
                md += f"- **{case['name']}**, {case['citation']}\n"
                md += f"  - {case['holding']}\n\n"

        md += "\n---\n\n## Critical Findings\n\n"

        critical = risk_summary["critical_findings"]
        if critical:
            md += (
                f"**{len(critical)} critical finding(s) require "
                "immediate legal review:**\n\n"
            )
            for idx, finding in enumerate(critical, 1):
                md += f"### {idx}. Anomaly {finding.get('anomaly_id')}\n\n"
                md += f"**Risk Score:** {finding.get('overall_score', 0):.3f}\n\n"
                md += "**Risk Factors:**\n"
                for factor in finding.get("risk_factors", []):
                    md += f"- {factor}\n"
                md += "\n**Recommended Actions:**\n"
                for action in finding.get("recommended_actions", []):
                    md += f"- {action}\n"
                md += "\n"
        else:
            md += "No critical findings identified.\n"

        md += "\n---\n\n## Recommendations\n\n"

        if risk_summary["requires_immediate_review"]:
            md += (
                "**IMMEDIATE ACTION REQUIRED:** This analysis identified "
                "high-priority legal concerns requiring review by qualified "
                "counsel.\n\n"
            )

        md += (
            """### Next Steps

1. Review all critical and high-severity findings with legal counsel
2. Verify statutory authorization for flagged administrative actions
3. Assess procedural safeguards for due process compliance
4. Evaluate chain of custody for evidentiary materials
5. Document all findings with proper legal citations

---

## Methodology

This analysis applies the Judicial Interpretive Matrix (JIM) framework, which:

1. **Correlates** audit anomalies to constitutional doctrines and precedents
2. **Scores** legal risk across six dimensions:
   - Due Process Conflict (25%)
   - Delegation Issues (20%)
   - Fourth Amendment Concerns (20%)
   - Administrative Overreach (15%)
   - Metadata Integrity (12%)
   - Chain of Custody (8%)
3. **Identifies** systemic patterns requiring institutional response

---

*This report is generated by automated analysis and does not constitute """
            """legal advice. Consult qualified legal counsel for interpretation """
            """and action.*
"""
        )

        return md

    def _create_linkage_graph(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """Create case linkage graph for visualization."""
        nodes = []
        edges = []

        # Create nodes for anomalies
        for assessment in analysis_result["individual_assessments"]:
            anomaly_id = assessment.get("anomaly_id")
            nodes.append(
                {
                    "id": f"anomaly_{anomaly_id}",
                    "type": "anomaly",
                    "label": anomaly_id,
                    "severity": assessment.get("severity"),
                    "risk_score": assessment.get("overall_score"),
                }
            )

            correlation = assessment.get("correlation", {})

            # Create nodes for doctrines
            for doctrine in correlation.get("doctrines", []):
                doctrine_node_id = f"doctrine_{doctrine}"
                if not any(n["id"] == doctrine_node_id for n in nodes):
                    nodes.append(
                        {
                            "id": doctrine_node_id,
                            "type": "doctrine",
                            "label": doctrine.replace("_", " ").title(),
                        }
                    )

                # Create edge from anomaly to doctrine
                edges.append(
                    {
                        "source": f"anomaly_{anomaly_id}",
                        "target": doctrine_node_id,
                        "type": "implicates",
                    }
                )

            # Create nodes for cases
            for case in correlation.get("relevant_cases", []):
                case_id = case["case_id"]
                case_node_id = f"case_{case_id}"

                if not any(n["id"] == case_node_id for n in nodes):
                    nodes.append(
                        {
                            "id": case_node_id,
                            "type": "case",
                            "label": case["name"],
                            "citation": case["citation"],
                            "year": case["year"],
                            "relevance_score": case["relevance_score"],
                        }
                    )

                # Create edge from doctrine to case
                doctrine_node_id = f"doctrine_{case['doctrine']}"
                edges.append(
                    {
                        "source": doctrine_node_id,
                        "target": case_node_id,
                        "type": "precedent",
                        "weight": case["relevance_score"],
                    }
                )

        return {
            "version": "1.0.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "graph": {
                "nodes": nodes,
                "edges": edges,
            },
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": {
                    "anomaly": len([n for n in nodes if n["type"] == "anomaly"]),
                    "doctrine": len([n for n in nodes if n["type"] == "doctrine"]),
                    "case": len([n for n in nodes if n["type"] == "case"]),
                },
            },
        }

    def run_full_analysis(self, anomalies: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Run complete JIM analysis pipeline.

        Args:
            anomalies: List of anomalies from audit systems

        Returns:
            Complete analysis result with all reports generated.
        """
        # Initialize if not already done
        if not self.case_index_loaded:
            init_result = self.initialize()
            if not init_result["success"]:
                return init_result

        # Analyze anomalies
        analysis_result = self.analyze_anomalies(anomalies)

        # Generate reports
        report_result = self.generate_reports(analysis_result)

        return {
            "success": report_result["success"],
            "analysis": analysis_result,
            "reports": report_result,
        }
