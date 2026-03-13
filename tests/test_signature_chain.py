"""Tests for signature chain detector."""

from __future__ import annotations

from oraculus_di_auditor.analysis.signature_chain import detect_signature_anomalies

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _doc(text: str) -> dict:
    return {"document_id": "test-doc", "raw_text": text}


def _sections_doc(content: str) -> dict:
    return {
        "document_id": "test-doc",
        "sections": [{"section_id": "1", "content": content}],
    }


# ---------------------------------------------------------------------------
# No-anomaly cases
# ---------------------------------------------------------------------------


def test_properly_signed_document_no_anomalies():
    """A complete, signed contract should produce no findings."""
    doc = _doc(
        "This MSA has been duly executed by both parties. "
        "Signed by City Representative on 2024-01-15. "
        "Signed by Vendor Representative on 2024-01-15."
    )
    assert detect_signature_anomalies(doc) == []


def test_no_contract_keywords_no_anomalies():
    """Signature gap indicators without contract instrument keyword should not flag."""
    doc = _doc("This memo is unsigned and has not been executed by any party.")
    assert detect_signature_anomalies(doc) == []


def test_empty_document_no_anomalies():
    """Document with no extractable text should return empty."""
    assert detect_signature_anomalies({"document_id": "empty"}) == []


def test_non_dict_input_returns_empty():
    assert detect_signature_anomalies(None) == []
    assert detect_signature_anomalies("not a doc") == []
    assert detect_signature_anomalies(42) == []


# ---------------------------------------------------------------------------
# signature:unsigned-instrument
# ---------------------------------------------------------------------------


def test_unsigned_mspa_with_dollar_amount_is_critical():
    """Unsigned MSPA with a dollar amount should be severity=critical."""
    doc = _doc(
        "MSPA No. 2024-001. Total contract value $250,000. "
        "Vendor signature block blank. City signature pending."
    )
    anomalies = detect_signature_anomalies(doc)
    ids = [a["id"] for a in anomalies]
    assert "signature:unsigned-instrument" in ids
    finding = next(a for a in anomalies if a["id"] == "signature:unsigned-instrument")
    assert finding["severity"] == "critical"
    assert finding["layer"] == "signature"


def test_unsigned_instrument_without_dollar_amount_is_high():
    """Unsigned contract without a dollar amount should be severity=high."""
    doc = _doc("This agreement is unsigned and has not been executed by the vendor.")
    anomalies = detect_signature_anomalies(doc)
    ids = [a["id"] for a in anomalies]
    assert "signature:unsigned-instrument" in ids
    finding = next(a for a in anomalies if a["id"] == "signature:unsigned-instrument")
    assert finding["severity"] == "high"
    assert finding["details"]["dollar_amount"] is None


def test_unsigned_instrument_details_instrument_type():
    """Details should capture the nearest instrument keyword."""
    doc = _doc("SOW No. 5: vendor signature only. Deliverables are listed below.")
    anomalies = detect_signature_anomalies(doc)
    finding = next(
        (a for a in anomalies if a["id"] == "signature:unsigned-instrument"), None
    )
    assert finding is not None
    assert finding["details"]["instrument_type"] == "SOW"


def test_unsigned_instrument_details_dollar_amount_captured():
    """Dollar amount in the contract should appear in finding details."""
    doc = _doc("Contract (MSA) value $1.5M. Agency signature missing.")
    finding = next(
        (
            a
            for a in detect_signature_anomalies(doc)
            if a["id"] == "signature:unsigned-instrument"
        ),
        None,
    )
    assert finding is not None
    assert finding["details"]["dollar_amount"] is not None


def test_partial_signature_one_party_blank():
    """'one party signed' should trigger unsigned-instrument."""
    doc = _doc(
        "MOU between City and Vendor. One party signed. Awaiting city countersignature."
    )
    anomalies = detect_signature_anomalies(doc)
    assert any(a["id"] == "signature:unsigned-instrument" for a in anomalies)


def test_city_signature_blank_in_amendment():
    """'city signature blank' in an amendment should trigger a finding."""
    doc = _doc("Amendment No. 3 to the original contract. City signature blank.")
    anomalies = detect_signature_anomalies(doc)
    assert any(a["id"] == "signature:unsigned-instrument" for a in anomalies)


def test_blank_underscores_in_contract():
    """Long underscore sequence (blank signature line) in a contract should flag."""
    doc = _doc("PSA for consulting services. Authorized Signatory: ___________")
    anomalies = detect_signature_anomalies(doc)
    assert any(a["id"] == "signature:unsigned-instrument" for a in anomalies)


def test_docusign_pending_in_order_form():
    """DocuSign + pending in an order form should flag as unsigned instrument."""
    doc = _doc("Order form for software licenses. DocuSign envelope status: pending.")
    anomalies = detect_signature_anomalies(doc)
    assert any(a["id"] == "signature:unsigned-instrument" for a in anomalies)


def test_not_executed_in_msa():
    """'not executed' in an MSA should produce a finding."""
    doc = _doc("MSA for janitorial services. This document has not been executed.")
    anomalies = detect_signature_anomalies(doc)
    assert any(a["id"] == "signature:unsigned-instrument" for a in anomalies)


def test_sections_based_document_detected():
    """Text inside sections[] should be scanned, not only raw_text."""
    doc = _sections_doc("This contract (MSA) is unsigned. Value $75,000.")
    anomalies = detect_signature_anomalies(doc)
    assert any(a["id"] == "signature:unsigned-instrument" for a in anomalies)
    finding = next(a for a in anomalies if a["id"] == "signature:unsigned-instrument")
    assert finding["severity"] == "critical"


# ---------------------------------------------------------------------------
# signature:placeholder-tokens
# ---------------------------------------------------------------------------


def test_placeholder_s1_token_in_sow():
    r"""\\s1\\ token in any document should flag signature:placeholder-tokens."""
    doc = _doc("SOW No. 12. Signed by: \\s1\\ Date: \\d1\\")
    anomalies = detect_signature_anomalies(doc)
    assert any(a["id"] == "signature:placeholder-tokens" for a in anomalies)


def test_placeholder_signature_bracket_token():
    """[SIGNATURE] token should flag signature:placeholder-tokens."""
    doc = _doc("This agreement is executed by [SIGNATURE] on behalf of the City.")
    anomalies = detect_signature_anomalies(doc)
    assert any(a["id"] == "signature:placeholder-tokens" for a in anomalies)


def test_placeholder_token_details_include_token_value():
    """Details should record the matched placeholder token."""
    doc = _doc("Vendor: [SIGNATURE]. This SOW is pending final execution.")
    finding = next(
        (
            a
            for a in detect_signature_anomalies(doc)
            if a["id"] == "signature:placeholder-tokens"
        ),
        None,
    )
    assert finding is not None
    assert finding["details"]["token"] == "[SIGNATURE]"
    assert isinstance(finding["details"]["position"], int)


def test_placeholder_token_without_contract_keyword_still_flagged():
    """Placeholder tokens are flagged regardless of instrument keywords."""
    doc = _doc("Authorized representative: \\s1\\")
    anomalies = detect_signature_anomalies(doc)
    assert any(a["id"] == "signature:placeholder-tokens" for a in anomalies)


def test_placeholder_and_unsigned_instrument_both_returned():
    """A doc with both issues should produce two findings."""
    doc = _doc("MSA for IT services. Vendor signature block blank. Signed by: \\s1\\")
    ids = [a["id"] for a in detect_signature_anomalies(doc)]
    assert "signature:unsigned-instrument" in ids
    assert "signature:placeholder-tokens" in ids
