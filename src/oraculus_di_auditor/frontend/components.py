"""Component Library - UI component specifications for Phase 6.

This module defines all UI components needed for the Oraculus-DI-Auditor
front-end system, including:
- Base UI components
- Dashboard components
- Analysis visualizations
- Document management components
- Provenance viewers

All specifications are deterministic and agent-ready for autonomous generation.
"""

from __future__ import annotations

from typing import Any


class ComponentLibrary:
    """Component library generator for Phase 6 front-end system."""

    def generate_component_list(
        self, backend_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate list of required UI components based on backend capabilities.

        Args:
            backend_analysis: Analysis of backend capabilities

        Returns:
            List of component specifications
        """
        components = []

        # Base UI components
        components.extend(self._base_components())

        # Dashboard components
        components.extend(self._dashboard_components())

        # Analysis components
        components.extend(self._analysis_components(backend_analysis))

        # Document components
        components.extend(self._document_components())

        # Visualization components
        components.extend(self._visualization_components(backend_analysis))

        # If Phase 5 orchestration available, add agent monitor
        if backend_analysis.get("orchestration_available"):
            components.extend(self._orchestration_components())

        return components

    def generate_full_specifications(
        self, backend_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate complete component specifications with props and behavior.

        Args:
            backend_analysis: Analysis of backend capabilities

        Returns:
            Detailed component specifications
        """
        return {
            "base": self._detailed_base_components(),
            "dashboard": self._detailed_dashboard_components(),
            "analysis": self._detailed_analysis_components(backend_analysis),
            "document": self._detailed_document_components(),
            "visualization": self._detailed_visualization_components(backend_analysis),
            "orchestration": (
                self._detailed_orchestration_components()
                if backend_analysis.get("orchestration_available")
                else {}
            ),
        }

    def _base_components(self) -> list[dict[str, Any]]:
        """Generate base UI component specifications."""
        return [
            {
                "name": "Button",
                "category": "base",
                "purpose": "Reusable button component with variants",
                "priority": "high",
            },
            {
                "name": "Input",
                "category": "base",
                "purpose": "Text input with validation",
                "priority": "high",
            },
            {
                "name": "Card",
                "category": "base",
                "purpose": "Container component for content grouping",
                "priority": "high",
            },
            {
                "name": "Badge",
                "category": "base",
                "purpose": "Small status/label indicator",
                "priority": "medium",
            },
            {
                "name": "Alert",
                "category": "base",
                "purpose": "Error/warning/info message display",
                "priority": "high",
            },
            {
                "name": "Loading",
                "category": "base",
                "purpose": "Loading spinner/skeleton",
                "priority": "high",
            },
        ]

    def _dashboard_components(self) -> list[dict[str, Any]]:
        """Generate dashboard component specifications."""
        return [
            {
                "name": "DashboardLayout",
                "category": "dashboard",
                "purpose": "Main layout with sidebar and content area",
                "priority": "high",
            },
            {
                "name": "Sidebar",
                "category": "dashboard",
                "purpose": "Navigation sidebar",
                "priority": "high",
            },
            {
                "name": "Header",
                "category": "dashboard",
                "purpose": "Top navigation bar with branding",
                "priority": "high",
            },
            {
                "name": "ThemeToggle",
                "category": "dashboard",
                "purpose": "Light/dark theme switcher",
                "priority": "medium",
            },
        ]

    def _analysis_components(
        self, backend_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate analysis component specifications."""
        components = [
            {
                "name": "AnalysisPanel",
                "category": "analysis",
                "purpose": "Main analysis results display",
                "priority": "critical",
            },
            {
                "name": "AnomalyInspector",
                "category": "analysis",
                "purpose": "Detailed anomaly viewer with highlighting",
                "priority": "critical",
            },
            {
                "name": "ScoreDisplay",
                "category": "analysis",
                "purpose": "Recursive scalar score visualization",
                "priority": "high",
            },
            {
                "name": "FindingsList",
                "category": "analysis",
                "purpose": "List of detected anomalies/findings",
                "priority": "critical",
            },
        ]

        # Add detector-specific components
        detectors = backend_analysis.get("detectors", [])
        for detector in detectors:
            components.append(
                {
                    "name": f"{detector.title()}DetectorView",
                    "category": "analysis",
                    "purpose": f"Display {detector} detector results",
                    "priority": "medium",
                }
            )

        return components

    def _document_components(self) -> list[dict[str, Any]]:
        """Generate document management component specifications."""
        return [
            {
                "name": "DocumentUploader",
                "category": "document",
                "purpose": "File upload with drag-and-drop",
                "priority": "critical",
            },
            {
                "name": "DocumentList",
                "category": "document",
                "purpose": "List of uploaded/analyzed documents",
                "priority": "critical",
            },
            {
                "name": "DocumentViewer",
                "category": "document",
                "purpose": "Display document text with metadata",
                "priority": "high",
            },
            {
                "name": "MetadataEditor",
                "category": "document",
                "purpose": "Edit document metadata",
                "priority": "medium",
            },
        ]

    def _visualization_components(
        self, backend_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate visualization component specifications."""
        return [
            {
                "name": "ScoreGauge",
                "category": "visualization",
                "purpose": "Radial gauge for scalar scores",
                "priority": "high",
            },
            {
                "name": "TimelineChart",
                "category": "visualization",
                "purpose": "Timeline of document analysis",
                "priority": "medium",
            },
            {
                "name": "ProvenanceTree",
                "category": "visualization",
                "purpose": "Visual lineage tree for provenance",
                "priority": "medium",
            },
            {
                "name": "AnomalyHeatmap",
                "category": "visualization",
                "purpose": "Heatmap of anomaly distribution",
                "priority": "low",
            },
        ]

    def _orchestration_components(self) -> list[dict[str, Any]]:
        """Generate Phase 5 orchestration component specifications."""
        return [
            {
                "name": "AgentActivityMonitor",
                "category": "orchestration",
                "purpose": "Real-time agent activity display",
                "priority": "medium",
            },
            {
                "name": "TaskGraphViewer",
                "category": "orchestration",
                "purpose": "Visual representation of task dependencies",
                "priority": "low",
            },
            {
                "name": "OrchestrationDashboard",
                "category": "orchestration",
                "purpose": "Overview of multi-agent execution",
                "priority": "medium",
            },
        ]

    def _detailed_base_components(self) -> dict[str, Any]:
        """Generate detailed base component specifications."""
        return {
            "Button": {
                "props": {
                    "variant": "'primary' | 'secondary' | 'danger' | 'ghost'",
                    "size": "'sm' | 'md' | 'lg'",
                    "disabled": "boolean",
                    "loading": "boolean",
                    "onClick": "() => void",
                    "children": "ReactNode",
                },
                "behavior": "Displays clickable button with variants and loading state",
                "accessibility": "Proper ARIA labels, keyboard navigation",
            },
            "Input": {
                "props": {
                    "value": "string",
                    "onChange": "(value: string) => void",
                    "placeholder": "string",
                    "error": "string | null",
                    "disabled": "boolean",
                    "type": "'text' | 'email' | 'password'",
                },
                "behavior": "Controlled input with validation and error display",
                "accessibility": "Proper labels, error announcements",
            },
            "Card": {
                "props": {
                    "title": "string | null",
                    "children": "ReactNode",
                    "actions": "ReactNode | null",
                    "variant": "'default' | 'bordered' | 'elevated'",
                },
                "behavior": "Container with optional header and actions",
                "accessibility": "Proper semantic HTML (article/section)",
            },
        }

    def _detailed_dashboard_components(self) -> dict[str, Any]:
        """Generate detailed dashboard component specifications."""
        return {
            "DashboardLayout": {
                "props": {
                    "children": "ReactNode",
                    "sidebar": "ReactNode",
                    "header": "ReactNode",
                },
                "behavior": "Responsive layout with collapsible sidebar",
                "accessibility": "Skip to content link, landmark regions",
            },
            "Sidebar": {
                "props": {
                    "items": "NavigationItem[]",
                    "activeItem": "string",
                    "onNavigate": "(item: string) => void",
                    "collapsed": "boolean",
                },
                "behavior": "Navigation sidebar with icons and labels",
                "accessibility": "Navigation landmark, current page indicator",
            },
        }

    def _detailed_analysis_components(
        self, backend_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate detailed analysis component specifications."""
        return {
            "AnalysisPanel": {
                "props": {
                    "result": "AnalysisResult",
                    "onRefresh": "() => void",
                    "loading": "boolean",
                },
                "behavior": "Displays complete analysis results with all findings",
                "accessibility": "Status announcements, keyboard navigation",
            },
            "AnomalyInspector": {
                "props": {
                    "findings": "Finding[]",
                    "selectedFinding": "Finding | null",
                    "onSelectFinding": "(finding: Finding) => void",
                    "documentText": "string",
                },
                "behavior": "Shows findings list and highlights text in document",
                "accessibility": "List navigation, screen reader friendly",
            },
            "ScoreDisplay": {
                "props": {
                    "severityScore": "number",
                    "latticeScore": "number",
                    "labels": "Record<string, string>",
                },
                "behavior": "Displays scores with visual indicators (gauges/bars)",
                "accessibility": "Text alternatives for visual scores",
            },
        }

    def _detailed_document_components(self) -> dict[str, Any]:
        """Generate detailed document component specifications."""
        return {
            "DocumentUploader": {
                "props": {
                    "onUpload": "(file: File, metadata: Record<string, any>) => void",
                    "acceptedFormats": "string[]",
                    "maxSize": "number",
                    "uploading": "boolean",
                },
                "behavior": "Drag-and-drop file upload with metadata input",
                "accessibility": "Keyboard accessible, file input alternative",
            },
            "DocumentList": {
                "props": {
                    "documents": "Document[]",
                    "selectedId": "string | null",
                    "onSelect": "(id: string) => void",
                    "onDelete": "(id: string) => void",
                },
                "behavior": "Lists documents with actions (view, delete)",
                "accessibility": "List semantics, action button labels",
            },
        }

    def _detailed_visualization_components(
        self, backend_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate detailed visualization component specifications."""
        return {
            "ScoreGauge": {
                "props": {
                    "value": "number",
                    "min": "number",
                    "max": "number",
                    "label": "string",
                    "colorScheme": "'default' | 'severity'",
                },
                "behavior": "Radial gauge showing score with color coding",
                "accessibility": "Text value provided, proper ARIA labels",
            },
            "ProvenanceTree": {
                "props": {
                    "lineage": "ProvenanceNode[]",
                    "expandedNodes": "string[]",
                    "onToggleNode": "(nodeId: string) => void",
                },
                "behavior": "Collapsible tree showing data lineage",
                "accessibility": "Tree view ARIA pattern, keyboard navigation",
            },
        }

    def _detailed_orchestration_components(self) -> dict[str, Any]:
        """Generate detailed orchestration component specifications."""
        return {
            "AgentActivityMonitor": {
                "props": {
                    "agents": "AgentStatus[]",
                    "refreshInterval": "number",
                },
                "behavior": "Shows real-time agent status and activity",
                "accessibility": "Live region for updates, status indicators",
            },
            "TaskGraphViewer": {
                "props": {
                    "taskGraph": "TaskNode[]",
                    "executedTasks": "string[]",
                    "onSelectTask": "(taskId: string) => void",
                },
                "behavior": "Graph visualization of task dependencies",
                "accessibility": "Alternative list view, keyboard navigation",
            },
        }


__all__ = ["ComponentLibrary"]
