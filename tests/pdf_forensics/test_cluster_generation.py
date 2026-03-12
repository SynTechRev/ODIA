#!/usr/bin/env python3
"""Tests for origin cluster generation functionality.

This module tests the cluster_pdfs_by_origin function.
Total: 10 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.pdf_forensics.pdf_metadata_miner import cluster_pdfs_by_origin


class TestClusterPdfsByOrigin:
    """Tests for cluster_pdfs_by_origin function."""

    def test_cluster_empty_list(self):
        """Test clustering empty list."""
        result = cluster_pdfs_by_origin([])
        assert result["cluster_count"] == 0
        assert result["clusters"] == {}

    def test_cluster_single_pdf(self):
        """Test clustering single PDF."""
        metadata_list = [
            {
                "file_path": "/path/to/doc.pdf",
                "file_name": "doc.pdf",
                "info_dict": {
                    "producer": "Microsoft Word 2016",
                    "creator": "Microsoft Word",
                },
            }
        ]
        result = cluster_pdfs_by_origin(metadata_list)
        assert result["cluster_count"] == 1

    def test_cluster_same_origin(self):
        """Test clustering PDFs with same origin."""
        metadata_list = [
            {
                "file_path": "/path/to/doc1.pdf",
                "file_name": "doc1.pdf",
                "info_dict": {
                    "producer": "Microsoft Word 2016",
                    "creator": "",
                },
            },
            {
                "file_path": "/path/to/doc2.pdf",
                "file_name": "doc2.pdf",
                "info_dict": {
                    "producer": "Microsoft Word 2019",
                    "creator": "",
                },
            },
        ]
        result = cluster_pdfs_by_origin(metadata_list)
        # Both should be in same Microsoft cluster
        assert result["cluster_count"] >= 1
        has_microsoft = any(
            "microsoft" in name.lower() for name in result["clusters"].keys()
        )
        assert has_microsoft

    def test_cluster_different_origins(self):
        """Test clustering PDFs with different origins."""
        metadata_list = [
            {
                "file_path": "/path/to/doc1.pdf",
                "file_name": "doc1.pdf",
                "info_dict": {
                    "producer": "Microsoft Word",
                    "creator": "",
                },
            },
            {
                "file_path": "/path/to/doc2.pdf",
                "file_name": "doc2.pdf",
                "info_dict": {
                    "producer": "Xerox WorkCentre",
                    "creator": "",
                },
            },
        ]
        result = cluster_pdfs_by_origin(metadata_list)
        # Should have 2 clusters
        assert result["cluster_count"] == 2

    def test_cluster_contains_member_count(self):
        """Test that clusters contain member count."""
        metadata_list = [
            {
                "file_path": "/path/to/doc1.pdf",
                "file_name": "doc1.pdf",
                "info_dict": {
                    "producer": "Adobe Acrobat",
                    "creator": "",
                },
            },
            {
                "file_path": "/path/to/doc2.pdf",
                "file_name": "doc2.pdf",
                "info_dict": {
                    "producer": "Adobe Reader",
                    "creator": "",
                },
            },
        ]
        result = cluster_pdfs_by_origin(metadata_list)
        for _cluster_name, cluster_data in result["clusters"].items():
            assert "member_count" in cluster_data
            assert cluster_data["member_count"] > 0

    def test_cluster_contains_origin_type(self):
        """Test that clusters contain origin type."""
        metadata_list = [
            {
                "file_path": "/path/to/doc.pdf",
                "file_name": "doc.pdf",
                "info_dict": {
                    "producer": "Canon Scanner",
                    "creator": "",
                },
            },
        ]
        result = cluster_pdfs_by_origin(metadata_list)
        for cluster_data in result["clusters"].values():
            assert "origin_type" in cluster_data

    def test_cluster_contains_vendor(self):
        """Test that clusters contain vendor info."""
        metadata_list = [
            {
                "file_path": "/path/to/doc.pdf",
                "file_name": "doc.pdf",
                "info_dict": {
                    "producer": "Microsoft Word",
                    "creator": "",
                },
            },
        ]
        result = cluster_pdfs_by_origin(metadata_list)
        for cluster_data in result["clusters"].values():
            assert "vendor" in cluster_data

    def test_cluster_contains_members(self):
        """Test that clusters contain member list."""
        metadata_list = [
            {
                "file_path": "/path/to/doc.pdf",
                "file_name": "doc.pdf",
                "info_dict": {
                    "producer": "Adobe Acrobat",
                    "creator": "",
                },
            },
        ]
        result = cluster_pdfs_by_origin(metadata_list)
        for cluster_data in result["clusters"].values():
            assert "members" in cluster_data
            assert isinstance(cluster_data["members"], list)

    def test_cluster_unknown_origin(self):
        """Test clustering PDFs with unknown origin."""
        metadata_list = [
            {
                "file_path": "/path/to/doc.pdf",
                "file_name": "doc.pdf",
                "info_dict": {
                    "producer": "",
                    "creator": "",
                },
            },
        ]
        result = cluster_pdfs_by_origin(metadata_list)
        assert result["cluster_count"] == 1
        assert "unknown" in list(result["clusters"].keys())[0].lower()

    def test_cluster_large_batch(self):
        """Test clustering large batch of PDFs."""
        metadata_list = []
        producers = [
            "Microsoft Word",
            "Adobe Acrobat",
            "Xerox Scanner",
            "Canon Scanner",
            "",
        ]

        for i in range(100):
            producer = producers[i % len(producers)]
            metadata_list.append(
                {
                    "file_path": f"/path/to/doc{i}.pdf",
                    "file_name": f"doc{i}.pdf",
                    "info_dict": {
                        "producer": producer,
                        "creator": "",
                    },
                }
            )

        result = cluster_pdfs_by_origin(metadata_list)
        # Should have multiple clusters
        assert result["cluster_count"] >= 3
        # Total members should equal input
        total_members = sum(c["member_count"] for c in result["clusters"].values())
        assert total_members == 100
