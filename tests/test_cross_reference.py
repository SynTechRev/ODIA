"""Tests for cross-reference auditing module.

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

from oraculus_di_auditor.analysis.cross_reference import (
    cross_reference_audit,
    detect_cross_jurisdiction_refs,
)


def test_detect_usc_references():
    """Test detection of USC citations."""
    text = "This statute is codified at 42 U.S.C. § 1983."

    refs = detect_cross_jurisdiction_refs(text)

    # No cross-jurisdiction references (only federal)
    assert len(refs) == 0


def test_detect_cfr_references():
    """Test detection of CFR citations."""
    text = "See regulations at 21 CFR § 50.25 for details."

    refs = detect_cross_jurisdiction_refs(text)

    # No cross-jurisdiction references (only federal)
    assert len(refs) == 0


def test_detect_california_code_references():
    """Test detection of California code citations."""
    text = "This is defined in Cal. Penal Code section 187."

    refs = detect_cross_jurisdiction_refs(text)

    # No cross-jurisdiction references (only state)
    assert len(refs) == 0


def test_detect_usc_and_california_cross_reference():
    """Test detection of USC and California cross-references."""
    text = """
    This statute references both 42 U.S.C. § 1983 for federal civil rights
    and Cal. Penal Code for state criminal law.
    """

    refs = detect_cross_jurisdiction_refs(text)

    assert len(refs) == 1
    assert refs[0]["type"] == "federal_state_cross_reference"
    assert refs[0]["severity"] == "info"
    assert "U.S.C." in str(refs[0]["federal"])
    assert "Cal." in str(refs[0]["state"])


def test_detect_cfr_and_california_cross_reference():
    """Test detection of CFR and California cross-references."""
    text = """
    Federal regulations at 21 CFR § 50.25 apply, but see also
    Cal. Health Code for state requirements.
    """

    refs = detect_cross_jurisdiction_refs(text)

    assert len(refs) == 1
    assert refs[0]["type"] == "cfr_state_cross_reference"
    assert "CFR" in str(refs[0]["federal"])
    assert "Cal. Health Code" in str(refs[0]["state"])


def test_detect_multiple_citations():
    """Test detection of multiple citations of same type."""
    text = """
    See 42 U.S.C. § 1983 and 28 U.S.C. § 1331 for jurisdiction,
    and Cal. Penal Code § 187 and Cal. Civil Code § 1714.
    """

    refs = detect_cross_jurisdiction_refs(text)

    assert len(refs) == 1
    assert refs[0]["type"] == "federal_state_cross_reference"

    # Should detect multiple citations
    federal_refs = refs[0]["federal"]
    state_refs = refs[0]["state"]

    assert len(federal_refs) >= 2  # 42 USC and 28 USC
    assert len(state_refs) >= 2  # Penal and Civil


def test_cross_reference_audit_empty():
    """Test audit with no documents."""
    docs = []

    anomalies = cross_reference_audit(docs)

    assert len(anomalies) == 0


def test_cross_reference_audit_no_anomalies():
    """Test audit with documents containing no cross-references."""
    docs = [
        {
            "id": "doc1",
            "text": "This is about 42 U.S.C. § 1983.",
            "jurisdiction": "federal",
        },
        {
            "id": "doc2",
            "text": "Cal. Penal Code section 187 defines murder.",
            "jurisdiction": "california",
        },
    ]

    anomalies = cross_reference_audit(docs)

    # No cross-jurisdiction references, no anomalies
    assert len(anomalies) == 0


def test_cross_reference_audit_detects_cross_refs():
    """Test audit detects cross-jurisdiction references."""
    docs = [
        {
            "id": "doc1",
            "text": "See 42 U.S.C. § 1983 and Cal. Penal Code.",
            "jurisdiction": "federal",
        }
    ]

    anomalies = cross_reference_audit(docs)

    assert len(anomalies) == 1
    assert anomalies[0]["id"] == "doc1"
    assert anomalies[0]["issue"] == "federal_state_cross_reference"
    assert anomalies[0]["severity"] == "info"


def test_cross_reference_audit_jurisdiction_mismatch_federal():
    """Test detection of federal document with mostly state references."""
    docs = [
        {
            "id": "misclassified",
            "text": """
                Cal. Penal Code § 187, Cal. Civil Code § 1714,
                Cal. Health Code § 100, and 42 U.S.C. § 1983.
            """,
            "jurisdiction": "federal",
        }
    ]

    anomalies = cross_reference_audit(docs)

    # Should detect both cross-reference and jurisdiction mismatch
    assert len(anomalies) >= 1

    # Check for jurisdiction mismatch
    mismatch_findings = [a for a in anomalies if a["issue"] == "jurisdiction_mismatch"]
    assert len(mismatch_findings) == 1
    assert mismatch_findings[0]["severity"] == "warning"


def test_cross_reference_audit_jurisdiction_mismatch_state():
    """Test detection of state document with mostly federal references."""
    docs = [
        {
            "id": "misclassified",
            "text": """
                42 U.S.C. § 1983, 28 U.S.C. § 1331, 18 U.S.C. § 242,
                21 CFR § 50.25, 45 CFR § 46.101, and Cal. Penal Code.
            """,
            "jurisdiction": "california",
        }
    ]

    anomalies = cross_reference_audit(docs)

    # Should detect jurisdiction mismatch
    mismatch_findings = [a for a in anomalies if a["issue"] == "jurisdiction_mismatch"]
    assert len(mismatch_findings) == 1
    assert mismatch_findings[0]["severity"] == "warning"


def test_cross_reference_audit_multiple_documents():
    """Test audit across multiple documents."""
    docs = [
        {
            "id": "doc1",
            "text": "42 U.S.C. § 1983 only.",
            "jurisdiction": "federal",
        },
        {
            "id": "doc2",
            "text": "Cal. Penal Code only.",
            "jurisdiction": "california",
        },
        {
            "id": "doc3",
            "text": "42 U.S.C. § 1983 and Cal. Penal Code together.",
            "jurisdiction": "federal",
        },
    ]

    anomalies = cross_reference_audit(docs)

    # Only doc3 should have findings
    doc3_findings = [a for a in anomalies if a["id"] == "doc3"]
    assert len(doc3_findings) >= 1


def test_cross_reference_audit_unknown_jurisdiction():
    """Test audit with unknown jurisdiction."""
    docs = [
        {
            "id": "doc1",
            "text": "42 U.S.C. § 1983 and Cal. Penal Code.",
            "jurisdiction": "unknown",
        }
    ]

    anomalies = cross_reference_audit(docs)

    # Should still detect cross-references
    cross_ref_findings = [a for a in anomalies if "cross_reference" in a["issue"]]
    assert len(cross_ref_findings) >= 1


def test_cross_reference_audit_missing_fields():
    """Test audit handles documents with missing fields."""
    docs = [
        {
            "id": "doc1",
            # Missing 'text' field
            "jurisdiction": "federal",
        },
        {
            # Missing 'id' field
            "text": "42 U.S.C. § 1983",
            "jurisdiction": "federal",
        },
        {
            "id": "doc3",
            "text": "42 U.S.C. § 1983",
            # Missing 'jurisdiction' field
        },
    ]

    # Should not crash, just handle gracefully
    anomalies = cross_reference_audit(docs)

    # May or may not have findings, but shouldn't crash
    assert isinstance(anomalies, list)


def test_detect_pub_law_references():
    """Test detection of Public Law citations."""
    text = "Enacted as Pub. L. No. 111-148."

    refs = detect_cross_jurisdiction_refs(text)

    # Public Law alone doesn't trigger cross-jurisdiction
    assert len(refs) == 0


def test_detect_stat_references():
    """Test detection of Statutes at Large citations."""
    text = "Codified at 124 Stat. 119."

    refs = detect_cross_jurisdiction_refs(text)

    # Stat alone doesn't trigger cross-jurisdiction
    assert len(refs) == 0


def test_case_insensitive_detection():
    """Test that citation detection is case-insensitive."""
    text = "See 42 u.s.c. § 1983 and cal. penal code."

    refs = detect_cross_jurisdiction_refs(text)

    assert len(refs) == 1
    assert refs[0]["type"] == "federal_state_cross_reference"


def test_cross_reference_audit_detailed_output():
    """Test that audit provides detailed information."""
    docs = [
        {
            "id": "test_doc",
            "text": "42 U.S.C. § 1983 and Cal. Penal Code § 187.",
            "jurisdiction": "federal",
        }
    ]

    anomalies = cross_reference_audit(docs)

    assert len(anomalies) >= 1

    finding = anomalies[0]
    assert "id" in finding
    assert "jurisdiction" in finding
    assert "issue" in finding
    assert "severity" in finding
    assert "description" in finding
