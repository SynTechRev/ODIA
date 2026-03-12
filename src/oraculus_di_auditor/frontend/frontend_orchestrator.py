"""Phase 6 Frontend Orchestrator - Main coordination kernel for UI generation.

This module implements the core Phase 6 orchestration logic for generating
deterministic, structured front-end build instructions that agents can execute.

The orchestrator:
- Analyzes backend API capabilities
- Generates component specifications
- Produces build instructions
- Detects gaps and incompatibilities
- Creates deployment configurations

All operations are deterministic, structured, and maintain architectural continuity
with Phases 1-5.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .api_client import APIClientGenerator
from .components import ComponentLibrary
from .gaps import GapDetector


class Phase6Orchestrator:
    """Phase 6 Orchestration Kernel for Front-End Generation.

    Coordinates front-end architecture generation with deterministic execution,
    full compatibility checking, and structured output formatting.

    This is the main entry point for Phase 6 operations.
    """

    def __init__(self):
        """Initialize Phase 6 Orchestrator with all subsystems."""
        self.component_library = ComponentLibrary()
        self.api_client_generator = APIClientGenerator()
        self.gap_detector = GapDetector()

    def execute_request(
        self, request: dict[str, Any], mode: str = "full"
    ) -> dict[str, Any]:
        """Execute a front-end generation request.

        This is the main entry point for Phase 6 operations.

        Args:
            request: User request containing:
                - type (str): Request type ("task_plan", "build_instructions",
                             "gap_report", "full_bundle")
                - backend_info (dict, optional): Backend API information
                - requirements (list, optional): Specific UI requirements
                - framework (str, optional): Preferred framework (default: "nextjs")
            mode: Execution mode ("full", "analysis_only", "instructions_only")

        Returns:
            Structured Phase 6 response with appropriate format based on type

        Example:
            >>> orchestrator = Phase6Orchestrator()
            >>> result = orchestrator.execute_request({
            ...     "type": "full_bundle",
            ...     "framework": "nextjs"
            ... })
        """
        request_type = request.get("type", "full_bundle")
        timestamp = datetime.now(UTC).isoformat()

        # Analyze backend capabilities
        backend_analysis = self._analyze_backend(request.get("backend_info", {}))

        if request_type == "task_plan":
            return self._generate_task_plan(backend_analysis, request, timestamp)
        elif request_type == "build_instructions":
            return self._generate_build_instructions(
                backend_analysis, request, timestamp
            )
        elif request_type == "gap_report":
            return self._generate_gap_report(backend_analysis, request, timestamp)
        elif request_type == "full_bundle":
            return self._generate_full_bundle(backend_analysis, request, timestamp)
        else:
            return {
                "error": f"Unknown request type: {request_type}",
                "timestamp": timestamp,
            }

    def _analyze_backend(self, backend_info: dict[str, Any]) -> dict[str, Any]:
        """Analyze backend capabilities and extract API information.

        Args:
            backend_info: Backend information (optional, can auto-discover)

        Returns:
            Backend analysis with endpoints, schemas, and capabilities
        """
        # Default backend analysis based on known Phase 4 + Phase 5 capabilities
        default_endpoints = [
            {
                "path": "/api/v1/health",
                "method": "GET",
                "description": "Health check endpoint",
            },
            {
                "path": "/analyze",
                "method": "POST",
                "description": "Primary Phase 4 unified analysis endpoint",
                "input_schema": {
                    "document_text": "string",
                    "metadata": "object",
                },
                "output_schema": {
                    "findings": "object",
                    "severity_score": "number",
                    "lattice_score": "number",
                    "flags": "array",
                },
            },
            {
                "path": "/api/v1/analyze",
                "method": "POST",
                "description": "Legacy analysis endpoint",
            },
            {
                "path": "/api/v1/info",
                "method": "GET",
                "description": "API information and capabilities",
            },
        ]

        return {
            "endpoints": backend_info.get("endpoints", default_endpoints),
            "detectors": backend_info.get(
                "detectors",
                ["fiscal", "constitutional", "surveillance", "cross-reference"],
            ),
            "features": backend_info.get(
                "features",
                [
                    "Multi-format document ingestion",
                    "Anomaly detection",
                    "Recursive scalar scoring",
                    "Provenance tracking",
                    "Phase 4 unified analysis pipeline",
                    "Phase 5 orchestration",
                ],
            ),
            "orchestration_available": True,
            "phase5_agents": [
                "IngestionAgent",
                "AnalysisAgent",
                "AnomalyAgent",
                "SynthesisAgent",
                "DatabaseAgent",
                "InterfaceAgent",
            ],
        }

    def _generate_task_plan(
        self,
        backend_analysis: dict[str, Any],
        request: dict[str, Any],
        timestamp: str,
    ) -> dict[str, Any]:
        """Generate a front-end task plan.

        Args:
            backend_analysis: Backend capabilities analysis
            request: Original request
            timestamp: Request timestamp

        Returns:
            Structured task plan in Phase 6 format
        """
        framework = request.get("framework", "nextjs")

        # Generate component list based on backend capabilities
        components = self.component_library.generate_component_list(backend_analysis)

        # Identify required APIs
        apis_needed = self.api_client_generator.identify_required_apis(backend_analysis)

        # Generate data models
        data_models = self._generate_data_models(backend_analysis)

        # Determine state management approach
        state_management = self._determine_state_management(framework, components)

        # Generate execution order
        execution_order = self._generate_execution_order(components)

        # Identify dependencies
        dependencies = self._identify_dependencies(framework, components)

        # Detect risk flags
        risk_flags = self.gap_detector.detect_risk_flags(
            backend_analysis, components, apis_needed
        )

        # Calculate readiness score
        readiness_score = self._calculate_readiness_score(
            backend_analysis, components, risk_flags
        )

        return {
            "type": "task_plan",
            "components": components,
            "apis_needed": apis_needed,
            "data_models": data_models,
            "state_management": state_management,
            "execution_order": execution_order,
            "dependencies": dependencies,
            "risk_flags": risk_flags,
            "readiness_score": readiness_score,
            "timestamp": timestamp,
        }

    def _generate_build_instructions(
        self,
        backend_analysis: dict[str, Any],
        request: dict[str, Any],
        timestamp: str,
    ) -> dict[str, Any]:
        """Generate front-end build instructions.

        Args:
            backend_analysis: Backend capabilities analysis
            request: Original request
            timestamp: Request timestamp

        Returns:
            Structured build instructions in Phase 6 format
        """
        framework = request.get("framework", "nextjs")

        # Generate scaffold commands
        scaffold_commands = self._generate_scaffold_commands(framework)

        # Generate directory structure
        directory_structure = self._generate_directory_structure(framework)

        # Generate setup steps
        setup_steps = self._generate_setup_steps(framework, backend_analysis)

        # Generate integration steps
        integration_steps = self._generate_integration_steps(
            framework, backend_analysis
        )

        # Generate success criteria
        success_criteria = self._generate_success_criteria(backend_analysis)

        return {
            "type": "build_instructions",
            "framework": framework,
            "scaffold_commands": scaffold_commands,
            "directory_structure": directory_structure,
            "setup_steps": setup_steps,
            "integration_steps": integration_steps,
            "success_criteria": success_criteria,
            "timestamp": timestamp,
        }

    def _generate_gap_report(
        self,
        backend_analysis: dict[str, Any],
        request: dict[str, Any],
        timestamp: str,
    ) -> dict[str, Any]:
        """Generate gap identification report.

        Args:
            backend_analysis: Backend capabilities analysis
            request: Original request
            timestamp: Request timestamp

        Returns:
            Structured gap report in Phase 6 format
        """
        gaps = self.gap_detector.identify_gaps(backend_analysis)

        return {
            "type": "gap_report",
            "missing_endpoints": gaps["missing_endpoints"],
            "missing_ui_components": gaps["missing_ui_components"],
            "backend_incompatibilities": gaps["backend_incompatibilities"],
            "security_issues": gaps["security_issues"],
            "suggested_fixes": gaps["suggested_fixes"],
            "priority": gaps["priority"],
            "timestamp": timestamp,
        }

    def _generate_full_bundle(
        self,
        backend_analysis: dict[str, Any],
        request: dict[str, Any],
        timestamp: str,
    ) -> dict[str, Any]:
        """Generate complete Phase 6 output bundle.

        Args:
            backend_analysis: Backend capabilities analysis
            request: Original request
            timestamp: Request timestamp

        Returns:
            Complete Phase 6 bundle with all outputs
        """
        framework = request.get("framework", "nextjs")

        # Generate all sub-outputs
        task_plan = self._generate_task_plan(backend_analysis, request, timestamp)
        build_instructions = self._generate_build_instructions(
            backend_analysis, request, timestamp
        )
        gap_report = self._generate_gap_report(backend_analysis, request, timestamp)

        # Generate architecture specification
        architecture = self._generate_architecture_spec(framework, backend_analysis)

        # Generate component specifications
        components = self.component_library.generate_full_specifications(
            backend_analysis
        )

        # Generate state model
        state_model = self._generate_state_model(framework, components)

        # Generate API client
        api_client = self.api_client_generator.generate_client_code(
            backend_analysis, framework
        )

        # Generate testing strategy
        testing = self._generate_testing_strategy(framework, components)

        # Generate deployment configuration
        deployment = self._generate_deployment_config(framework, backend_analysis)

        # Recommend next phase
        recommended_next_phase = self._recommend_next_phase(gap_report)

        # Calculate confidence
        confidence = self._calculate_confidence(gap_report, backend_analysis)

        return {
            "type": "full_bundle",
            "architecture": architecture,
            "components": components,
            "state_model": state_model,
            "api_client": api_client,
            "testing": testing,
            "deployment": deployment,
            "task_plan": task_plan,
            "build_instructions": build_instructions,
            "gap_report": gap_report,
            "recommended_next_phase": recommended_next_phase,
            "confidence": confidence,
            "timestamp": timestamp,
        }

    # Helper methods for generating specific elements

    def _generate_data_models(self, backend_analysis: dict[str, Any]) -> list[dict]:
        """Generate TypeScript/JavaScript data models based on backend schemas."""
        models = []

        # Document model
        models.append(
            {
                "name": "Document",
                "fields": {
                    "document_text": "string",
                    "metadata": "Record<string, any>",
                },
                "description": "Input document for analysis",
            }
        )

        # Analysis result model
        models.append(
            {
                "name": "AnalysisResult",
                "fields": {
                    "findings": "Record<string, Finding[]>",
                    "severity_score": "number",
                    "lattice_score": "number",
                    "flags": "string[]",
                    "summary": "string",
                    "timestamp": "string",
                },
                "description": "Analysis pipeline output",
            }
        )

        # Finding model
        models.append(
            {
                "name": "Finding",
                "fields": {
                    "type": "string",
                    "description": "string",
                    "location": "string | null",
                    "severity": "number",
                },
                "description": "Individual anomaly finding",
            }
        )

        return models

    def _determine_state_management(
        self, framework: str, components: list[dict]
    ) -> dict[str, Any]:
        """Determine appropriate state management strategy."""
        return {
            "library": "zustand" if framework == "nextjs" else "redux",
            "rationale": "Lightweight, TypeScript-friendly, minimal boilerplate",
            "stores": [
                {
                    "name": "documentStore",
                    "purpose": "Manage document list and upload state",
                },
                {
                    "name": "analysisStore",
                    "purpose": "Manage analysis results and status",
                },
                {
                    "name": "uiStore",
                    "purpose": "Manage UI state (theme, panels, etc)",
                },
            ],
        }

    def _generate_execution_order(self, components: list[dict]) -> list[str]:
        """Generate component implementation order based on dependencies."""
        return [
            "1. Setup project scaffold and dependencies",
            "2. Configure TypeScript and linting",
            "3. Create API client library",
            "4. Implement state management stores",
            "5. Build core UI components (Button, Input, Card, etc)",
            "6. Build data display components (charts, tables)",
            "7. Implement document uploader",
            "8. Build analysis dashboard",
            "9. Implement anomaly inspector",
            "10. Add provenance viewer",
            "11. Configure routing and navigation",
            "12. Add error handling and loading states",
            "13. Implement responsive design",
            "14. Add accessibility features",
            "15. Configure deployment",
        ]

    def _identify_dependencies(
        self, framework: str, components: list[dict]
    ) -> dict[str, list[str]]:
        """Identify npm/yarn dependencies required."""
        base_deps = {
            "runtime": [
                "react@^18.0.0",
                "react-dom@^18.0.0",
                "zustand@^4.0.0",
                "axios@^1.6.0",
            ],
            "development": [
                "typescript@^5.0.0",
                "@types/react@^18.0.0",
                "@types/react-dom@^18.0.0",
                "eslint@^8.0.0",
                "prettier@^3.0.0",
            ],
        }

        if framework == "nextjs":
            base_deps["runtime"].extend(["next@^14.0.0"])
            base_deps["development"].extend(["@types/node@^20.0.0"])

        # Add visualization libraries
        base_deps["runtime"].extend(
            [
                "recharts@^2.10.0",
                "tailwindcss@^3.4.0",
            ]
        )

        return base_deps

    def _calculate_readiness_score(
        self,
        backend_analysis: dict[str, Any],
        components: list[dict],
        risk_flags: list[str],
    ) -> float:
        """Calculate front-end readiness score (0-1)."""
        score = 1.0

        # Deduct for missing endpoints
        if not backend_analysis.get("endpoints"):
            score -= 0.3

        # Deduct for risk flags
        score -= min(0.3, len(risk_flags) * 0.05)

        # Deduct if no orchestration
        if not backend_analysis.get("orchestration_available"):
            score -= 0.2

        return max(0.0, score)

    def _generate_scaffold_commands(self, framework: str) -> list[str]:
        """Generate framework scaffolding commands."""
        if framework == "nextjs":
            return [
                "npx create-next-app@latest oraculus-ui --typescript "
                "--tailwind --app --no-src-dir",
                "cd oraculus-ui",
                "npm install zustand axios recharts",
                "npm install -D @types/node prettier eslint-config-prettier",
            ]
        else:
            return [
                "npx create-react-app oraculus-ui --template typescript",
                "cd oraculus-ui",
                "npm install zustand axios recharts",
                "npm install -D prettier eslint-config-prettier",
            ]

    def _generate_directory_structure(self, framework: str) -> dict[str, Any]:
        """Generate recommended directory structure."""
        return {
            "root": "oraculus-ui/",
            "structure": {
                "app/" if framework == "nextjs" else "src/": {
                    "components/": {
                        "ui/": "Base UI components (buttons, inputs, cards)",
                        "dashboard/": "Dashboard-specific components",
                        "analysis/": "Analysis display components",
                        "upload/": "Document upload components",
                    },
                    "lib/": {
                        "api/": "API client and utilities",
                        "stores/": "State management stores",
                        "types/": "TypeScript type definitions",
                        "utils/": "Helper functions",
                    },
                    "hooks/": "Custom React hooks",
                },
                "public/": "Static assets",
                "tests/": "Test files",
            },
        }

    def _generate_setup_steps(
        self, framework: str, backend_analysis: dict[str, Any]
    ) -> list[dict]:
        """Generate setup steps with descriptions."""
        return [
            {
                "step": 1,
                "action": "Initialize project",
                "commands": self._generate_scaffold_commands(framework),
                "validation": (
                    "Check that package.json exists and has correct dependencies"
                ),
            },
            {
                "step": 2,
                "action": "Configure TypeScript",
                "commands": [
                    "# Ensure tsconfig.json has strict mode enabled",
                    "# Enable path aliases for cleaner imports",
                ],
                "validation": "Run tsc --noEmit successfully",
            },
            {
                "step": 3,
                "action": "Setup Tailwind CSS",
                "commands": [
                    "# Configure tailwind.config.js with custom theme",
                    "# Add dark mode support",
                ],
                "validation": "Build succeeds and styles are applied",
            },
            {
                "step": 4,
                "action": "Create API client",
                "commands": [
                    "# Create lib/api/client.ts with Axios instance",
                    "# Configure base URL and interceptors",
                ],
                "validation": "API client can make requests to backend",
            },
        ]

    def _generate_integration_steps(
        self, framework: str, backend_analysis: dict[str, Any]
    ) -> list[dict]:
        """Generate backend integration steps."""
        return [
            {
                "step": 1,
                "action": "Configure CORS",
                "description": "Set ORACULUS_CORS_ORIGINS environment variable",
                "example": 'ORACULUS_CORS_ORIGINS="http://localhost:3000"',
            },
            {
                "step": 2,
                "action": "Implement API client methods",
                "description": "Create methods for each backend endpoint",
                "endpoints": [
                    ep["path"] for ep in backend_analysis.get("endpoints", [])
                ],
            },
            {
                "step": 3,
                "action": "Add request/response types",
                "description": "Define TypeScript types matching backend schemas",
            },
            {
                "step": 4,
                "action": "Implement error handling",
                "description": "Handle network errors, timeouts, and API errors",
            },
            {
                "step": 5,
                "action": "Add loading states",
                "description": "Show loading indicators during API calls",
            },
        ]

    def _generate_success_criteria(self, backend_analysis: dict[str, Any]) -> list[str]:
        """Generate success criteria checklist."""
        return [
            "✓ Application builds without errors",
            "✓ All TypeScript types compile successfully",
            "✓ API client successfully connects to backend",
            "✓ Document upload works and triggers analysis",
            "✓ Analysis results display correctly",
            "✓ All detectors visible in UI",
            "✓ Responsive design works on mobile/tablet/desktop",
            "✓ Dark mode theme works",
            "✓ WCAG accessibility standards met",
            "✓ No console errors in browser",
            "✓ Loading states visible during operations",
            "✓ Error messages clear and actionable",
        ]

    def _generate_architecture_spec(
        self, framework: str, backend_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate high-level architecture specification."""
        pattern = (
            "Server-Side Rendering (SSR)"
            if framework == "nextjs"
            else "Single Page Application (SPA)"
        )
        routing = "Next.js App Router" if framework == "nextjs" else "React Router"

        return {
            "pattern": pattern,
            "framework": framework,
            "language": "TypeScript",
            "styling": "Tailwind CSS",
            "state_management": "Zustand",
            "api_layer": "Axios with custom client",
            "routing": routing,
            "testing": "Vitest + React Testing Library",
            "build_tool": "Next.js" if framework == "nextjs" else "Vite",
            "principles": [
                "Component-based architecture",
                "Type safety throughout",
                "Separation of concerns",
                "Reusable UI components",
                "Centralized state management",
                "Error boundary protection",
                "Accessibility first",
            ],
        }

    def _generate_state_model(
        self, framework: str, components: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate state management model."""
        return {
            "approach": "Zustand stores",
            "stores": {
                "documentStore": {
                    "state": {
                        "documents": "Document[]",
                        "selectedDocument": "Document | null",
                        "uploadStatus": "'idle' | 'uploading' | 'success' | 'error'",
                    },
                    "actions": [
                        "addDocument",
                        "removeDocument",
                        "selectDocument",
                        "setUploadStatus",
                    ],
                },
                "analysisStore": {
                    "state": {
                        "results": "Map<string, AnalysisResult>",
                        "currentAnalysis": "AnalysisResult | null",
                        "isAnalyzing": "boolean",
                    },
                    "actions": [
                        "setResult",
                        "clearResults",
                        "startAnalysis",
                        "finishAnalysis",
                    ],
                },
                "uiStore": {
                    "state": {
                        "theme": "'light' | 'dark'",
                        "sidebarOpen": "boolean",
                        "activeView": "string",
                    },
                    "actions": ["toggleTheme", "toggleSidebar", "setActiveView"],
                },
            },
        }

    def _generate_testing_strategy(
        self, framework: str, components: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate testing strategy."""
        return {
            "unit_tests": {
                "tool": "Vitest",
                "coverage": "Components, utilities, stores",
                "target": "80%+ coverage",
            },
            "integration_tests": {
                "tool": "React Testing Library",
                "coverage": "User flows, API integration",
            },
            "e2e_tests": {
                "tool": "Playwright (optional)",
                "coverage": "Critical user journeys",
            },
            "accessibility_tests": {
                "tool": "axe-core",
                "coverage": "All interactive components",
            },
        }

    def _generate_deployment_config(
        self, framework: str, backend_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate deployment configuration."""
        return {
            "platforms": {
                "vercel": {
                    "recommended": framework == "nextjs",
                    "steps": [
                        "Connect GitHub repository",
                        "Set environment variables",
                        "Deploy automatically on push",
                    ],
                },
                "netlify": {
                    "recommended": framework == "react",
                    "steps": [
                        "Connect GitHub repository",
                        "Set build command: npm run build",
                        "Set publish directory: dist",
                    ],
                },
                "docker": {
                    "recommended": True,
                    "dockerfile": "Provided in deployment bundle",
                },
            },
            "environment_variables": [
                {
                    "name": "NEXT_PUBLIC_API_URL",
                    "description": "Backend API base URL",
                    "example": "https://api.oraculus.example.com",
                },
                {
                    "name": "NEXT_PUBLIC_APP_NAME",
                    "description": "Application name for branding",
                    "example": "Oraculus DI Auditor",
                },
            ],
            "ci_cd": {
                "github_actions": True,
                "workflow": ".github/workflows/frontend-ci.yml",
                "steps": ["Lint", "Type check", "Test", "Build", "Deploy"],
            },
        }

    def _recommend_next_phase(self, gap_report: dict[str, Any]) -> str:
        """Recommend next phase based on gap analysis."""
        priority = gap_report.get("priority", "low")

        if priority == "critical":
            return "Address critical gaps before proceeding"
        elif priority == "high":
            return "Implement high-priority fixes, then proceed to Phase 7"
        elif priority == "medium":
            return "Phase 7: Strategic Data Integration + Expansion"
        else:
            return "Phase 7: Strategic Data Integration + Expansion"

    def _calculate_confidence(
        self, gap_report: dict[str, Any], backend_analysis: dict[str, Any]
    ) -> float:
        """Calculate overall confidence score (0-1)."""
        confidence = 1.0

        # Deduct for gaps
        gap_count = (
            len(gap_report.get("missing_endpoints", []))
            + len(gap_report.get("backend_incompatibilities", []))
            + len(gap_report.get("security_issues", []))
        )

        confidence -= min(0.4, gap_count * 0.1)

        # Deduct if backend incomplete
        if len(backend_analysis.get("endpoints", [])) < 3:
            confidence -= 0.2

        return max(0.0, confidence)


__all__ = ["Phase6Orchestrator"]
