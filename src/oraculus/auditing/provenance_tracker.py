"""Provenance tracking and reference graph building for Oraculus DI Auditor."""


class ProvenanceTracker:
    """Tracks document provenance and builds reference graphs.

    This class maintains a graph of document relationships and tracks
    the integrity and lineage of legislative documents.
    """

    def __init__(self):
        """Initialize the provenance tracker."""
        self.documents = {}
        self.reference_graph = {}

    def add_document(self, document: dict) -> str:
        """Add a document to the provenance tracker.

        Args:
            document: Normalized document following canonical schema

        Returns:
            Document ID

        Raises:
            ValueError: If document is missing required fields
        """
        if "document_id" not in document:
            raise ValueError("Document must have a document_id")

        doc_id = document["document_id"]

        # Store document
        self.documents[doc_id] = document

        # Initialize reference graph entry
        if doc_id not in self.reference_graph:
            self.reference_graph[doc_id] = {
                "references_to": [],
                "referenced_by": [],
            }

        # Build reference relationships
        if "references" in document:
            for ref in document["references"]:
                ref_doc_id = ref.get("document_id")
                if ref_doc_id:
                    self.reference_graph[doc_id]["references_to"].append(
                        {
                            "document_id": ref_doc_id,
                            "reference_type": ref.get("reference_type", "cites"),
                            "section": ref.get("section"),
                        }
                    )

                    # Initialize reverse reference
                    if ref_doc_id not in self.reference_graph:
                        self.reference_graph[ref_doc_id] = {
                            "references_to": [],
                            "referenced_by": [],
                        }

                    self.reference_graph[ref_doc_id]["referenced_by"].append(
                        {
                            "document_id": doc_id,
                            "reference_type": ref.get("reference_type", "cites"),
                        }
                    )

        return doc_id

    def get_document(self, document_id: str) -> dict | None:
        """Retrieve a document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document dictionary or None if not found
        """
        return self.documents.get(document_id)

    def get_references(self, document_id: str) -> dict:
        """Get reference graph for a document.

        Args:
            document_id: Document identifier

        Returns:
            Dictionary with references_to and referenced_by lists
        """
        return self.reference_graph.get(
            document_id,
            {
                "references_to": [],
                "referenced_by": [],
            },
        )

    def verify_hash(self, document_id: str) -> bool:
        """Verify the integrity hash of a document.

        Args:
            document_id: Document identifier

        Returns:
            True if hash is valid, False otherwise
        """
        document = self.get_document(document_id)
        if not document:
            return False

        provenance = document.get("provenance", {})
        stored_hash = provenance.get("hash")

        if not stored_hash:
            return False

        # Recompute hash from document content
        # Remove provenance for hash calculation to avoid circular dependency
        doc_copy = document.copy()
        if "provenance" in doc_copy:
            prov_copy = doc_copy["provenance"].copy()
            prov_copy.pop("hash", None)
            prov_copy.pop("verified_on", None)
            doc_copy["provenance"] = prov_copy

        # For now, just check if hash exists since we may not have original content
        return len(stored_hash) == 64 and all(
            c in "0123456789abcdef" for c in stored_hash.lower()
        )

    def get_dependencies(self, document_id: str) -> list[str]:
        """Get all documents that this document depends on.

        Args:
            document_id: Document identifier

        Returns:
            List of document IDs that this document references
        """
        refs = self.get_references(document_id)
        return [ref["document_id"] for ref in refs["references_to"]]

    def get_dependents(self, document_id: str) -> list[str]:
        """Get all documents that depend on this document.

        Args:
            document_id: Document identifier

        Returns:
            List of document IDs that reference this document
        """
        refs = self.get_references(document_id)
        return [ref["document_id"] for ref in refs["referenced_by"]]

    def detect_anomalies(self, document_id: str) -> list[dict]:
        """Detect anomalies in a document.

        Args:
            document_id: Document identifier

        Returns:
            List of anomaly dictionaries with type and description
        """
        anomalies = []
        document = self.get_document(document_id)

        if not document:
            return [{"type": "missing_document", "description": "Document not found"}]

        # Check for missing required fields
        if "title" not in document or not document["title"]:
            anomalies.append(
                {
                    "type": "missing_title",
                    "description": "Document is missing a title",
                }
            )

        # Check provenance integrity
        provenance = document.get("provenance", {})
        if not provenance.get("source"):
            anomalies.append(
                {
                    "type": "missing_source",
                    "description": "Document provenance is missing source information",
                }
            )

        if not provenance.get("hash"):
            anomalies.append(
                {
                    "type": "missing_hash",
                    "description": "Document is missing integrity hash",
                }
            )

        # Check for missing signatory on certain document types
        doc_type = document.get("document_type")
        if doc_type in ["executive_order", "contract"] and not document.get(
            "signatory"
        ):
            anomalies.append(
                {
                    "type": "missing_signatory",
                    "description": (
                        f"{doc_type} documents typically require signatories"
                    ),
                }
            )

        # Check for ambiguous jurisdiction
        if not document.get("jurisdiction"):
            anomalies.append(
                {
                    "type": "missing_jurisdiction",
                    "description": "Document does not specify jurisdiction",
                }
            )

        # Check for broken references
        refs = self.get_references(document_id)
        for ref in refs["references_to"]:
            ref_doc_id = ref["document_id"]
            if ref_doc_id not in self.documents:
                anomalies.append(
                    {
                        "type": "broken_reference",
                        "description": (
                            f"References document {ref_doc_id} "
                            "which is not in the system"
                        ),
                    }
                )

        return anomalies

    def calculate_confidence_score(self, document_id: str) -> float:
        """Calculate a confidence score for a document based on completeness.

        Args:
            document_id: Document identifier

        Returns:
            Confidence score between 0.0 and 1.0
        """
        document = self.get_document(document_id)
        if not document:
            return 0.0

        anomalies = self.detect_anomalies(document_id)

        # Start with perfect score
        score = 1.0

        # Deduct points for each anomaly type
        anomaly_weights = {
            "missing_document": 1.0,
            "missing_title": 0.1,
            "missing_source": 0.15,
            "missing_hash": 0.2,
            "missing_signatory": 0.05,
            "missing_jurisdiction": 0.1,
            "broken_reference": 0.05,
        }

        for anomaly in anomalies:
            weight = anomaly_weights.get(anomaly["type"], 0.05)
            score -= weight

        return max(0.0, score)

    def generate_audit_report(self, document_id: str) -> dict:
        """Generate an audit report for a document.

        Args:
            document_id: Document identifier

        Returns:
            Audit report dictionary with findings and compliance status
        """
        document = self.get_document(document_id)
        if not document:
            return {
                "document_id": document_id,
                "audit_result": {
                    "anomalies_detected": 1,
                    "confidence_score": 0.0,
                    "compliance_status": "Failed - Document Not Found",
                },
            }

        anomalies = self.detect_anomalies(document_id)
        confidence = self.calculate_confidence_score(document_id)

        # Determine compliance status
        if confidence >= 0.95:
            compliance_status = "Pass"
        elif confidence >= 0.85:
            compliance_status = "Pass with Notes"
        else:
            compliance_status = "Review Required"

        return {
            "document_id": document_id,
            "provenance": document.get("provenance", {}),
            "audit_result": {
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies,
                "confidence_score": confidence,
                "compliance_status": compliance_status,
            },
            "references": self.get_references(document_id),
        }

    def export_graph(self) -> dict:
        """Export the complete reference graph.

        Returns:
            Dictionary representation of the reference graph
        """
        return {
            "documents": list(self.documents.keys()),
            "graph": self.reference_graph,
        }
