"""Tests for scope expansion detector."""

from __future__ import annotations

from oraculus_di_auditor.analysis.scope_expansion import (
    detect_scope_expansion_anomalies,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _doc(text: str) -> dict:
    return {"document_id": "test-doc", "raw_text": text}


def _ids(doc_text: str) -> set[str]:
    return {a["id"] for a in detect_scope_expansion_anomalies(_doc(doc_text))}


# ---------------------------------------------------------------------------
# No-anomaly cases
# ---------------------------------------------------------------------------


def test_clean_contract_no_amendments_no_anomalies():
    """A plain contract with no amendment keywords should produce nothing."""
    doc = _doc(
        "Original contract for IT services. Approved amount $500,000. "
        "Not to exceed $500,000. Signed by both parties."
    )
    assert detect_scope_expansion_anomalies(doc) == []


def test_non_dict_input_returns_empty():
    assert detect_scope_expansion_anomalies(None) == []
    assert detect_scope_expansion_anomalies("not a doc") == []
    assert detect_scope_expansion_anomalies(42) == []


def test_empty_text_returns_empty():
    assert detect_scope_expansion_anomalies({"document_id": "x"}) == []


def test_amendment_below_50_percent_threshold_no_expansion_flag():
    """40% increase is below threshold — no significant-expansion finding."""
    doc = _doc(
        "Amendment No. 1 to original contract. "
        "Base contract value $100,000. Amended value $140,000. "
        "Approved amount $100,000."
    )
    anomalies = detect_scope_expansion_anomalies(doc)
    assert not any(a["id"] == "scope:significant-expansion" for a in anomalies)


def test_amendment_exactly_at_threshold_not_flagged():
    """Exactly 50% increase is not strictly greater than threshold."""
    doc = _doc(
        "Amendment to original contract. "
        "Approved amount $100,000. New total $150,000."
    )
    anomalies = detect_scope_expansion_anomalies(doc)
    assert not any(a["id"] == "scope:significant-expansion" for a in anomalies)


# ---------------------------------------------------------------------------
# scope:significant-expansion
# ---------------------------------------------------------------------------


def test_amendment_with_60_percent_expansion_flagged():
    """60% expansion above threshold → high severity finding."""
    doc = _doc(
        "Amendment No. 2. Original contract value $100,000. "
        "Amended total $160,000. Not to exceed $160,000."
    )
    anomalies = detect_scope_expansion_anomalies(doc)
    assert any(a["id"] == "scope:significant-expansion" for a in anomalies)
    finding = next(a for a in anomalies if a["id"] == "scope:significant-expansion")
    assert finding["severity"] == "high"
    assert finding["layer"] == "scope"


def test_expansion_details_contain_required_fields():
    doc = _doc(
        "Amendment. Original contract $200,000. Approved amount $200,000. "
        "Expanded to $400,000."
    )
    finding = next(
        (
            a
            for a in detect_scope_expansion_anomalies(doc)
            if a["id"] == "scope:significant-expansion"
        ),
        None,
    )
    assert finding is not None
    assert "original_amount" in finding["details"]
    assert "expanded_amount" in finding["details"]
    assert "expansion_percentage" in finding["details"]
    assert finding["details"]["expansion_percentage"] == 100.0


def test_expansion_percentage_calculated_correctly():
    """$100k → $200k = 100% expansion."""
    doc = _doc(
        "Amendment to base contract. Approved amount $100,000. New value $200,000."
    )
    finding = next(
        (
            a
            for a in detect_scope_expansion_anomalies(doc)
            if a["id"] == "scope:significant-expansion"
        ),
        None,
    )
    assert finding is not None
    assert finding["details"]["expansion_percentage"] == 100.0


def test_suffix_amounts_parsed_correctly():
    """$1M vs $2M should be detected as 100% expansion."""
    assert "scope:significant-expansion" in _ids(
        "Amendment. Not to exceed $1M. New authorized amount $2M."
    )


def test_large_expansion_in_addendum():
    """Addendum with a 5× amount expansion should be flagged."""
    assert "scope:significant-expansion" in _ids(
        "Addendum to base contract. Initial authorization $50,000. "
        "Total after addendum $300,000."
    )


# ---------------------------------------------------------------------------
# scope:amendment-without-baseline
# ---------------------------------------------------------------------------


def test_amendment_with_no_baseline_reference_flagged():
    """Amendment keyword + no original authorization reference → medium."""
    doc = _doc("Amendment No. 3. Total contract value $750,000.")
    anomalies = detect_scope_expansion_anomalies(doc)
    assert any(a["id"] == "scope:amendment-without-baseline" for a in anomalies)
    finding = next(
        a for a in anomalies if a["id"] == "scope:amendment-without-baseline"
    )
    assert finding["severity"] == "medium"
    assert finding["layer"] == "scope"


def test_amendment_with_baseline_reference_no_baseline_flag():
    """'Not to exceed' counts as a baseline reference — no baseline finding."""
    doc = _doc("Amendment No. 1. Not to exceed $200,000. New value $250,000.")
    anomalies = detect_scope_expansion_anomalies(doc)
    assert not any(a["id"] == "scope:amendment-without-baseline" for a in anomalies)


def test_extension_without_original_contract_reference():
    """'Extension' with no baseline → amendment-without-baseline."""
    assert "scope:amendment-without-baseline" in _ids(
        "Contract extension for 12 months. Total value $500,000."
    )


# ---------------------------------------------------------------------------
# scope:sole-source-expansion
# ---------------------------------------------------------------------------


def test_sole_source_with_amendment_flagged():
    """'sole source' + amendment keyword → high severity."""
    doc = _doc(
        "Amendment No. 1. Procurement method: sole source justification. "
        "Original contract $100,000. Extended to $180,000. Not to exceed."
    )
    anomalies = detect_scope_expansion_anomalies(doc)
    assert any(a["id"] == "scope:sole-source-expansion" for a in anomalies)
    finding = next(a for a in anomalies if a["id"] == "scope:sole-source-expansion")
    assert finding["severity"] == "high"
    assert finding["layer"] == "scope"


def test_sole_source_hyphenated_form_detected():
    """'sole-source' hyphenated variant is also detected."""
    assert "scope:sole-source-expansion" in _ids(
        "Modification No. 2. Sole-source award. Approved amount $300,000."
    )


def test_single_source_with_renewal_detected():
    """'single source' + renewal → sole-source-expansion."""
    assert "scope:sole-source-expansion" in _ids(
        "Contract renewal. Single source procurement. Not to exceed $400,000."
    )


def test_sole_source_details_include_matched_token():
    doc = _doc(
        "Supplemental agreement. Sole source justification. Not to exceed $100,000."
    )
    finding = next(
        (
            a
            for a in detect_scope_expansion_anomalies(doc)
            if a["id"] == "scope:sole-source-expansion"
        ),
        None,
    )
    assert finding is not None
    assert "sole" in finding["details"]["sole_source_match"].lower()


def test_sole_source_without_amendment_no_flag():
    """Sole source without any amendment keyword should not trigger."""
    assert "scope:sole-source-expansion" not in _ids(
        "Original contract. Sole source justification. Approved amount $100,000."
    )


# ---------------------------------------------------------------------------
# Multiple findings
# ---------------------------------------------------------------------------


def test_amendment_can_produce_multiple_findings():
    """A bad amendment can trigger expansion + sole-source simultaneously."""
    ids = _ids(
        "Amendment No. 1. Sole source award. "
        "Original contract $100,000. New total $200,000. Not to exceed $200,000."
    )
    assert "scope:significant-expansion" in ids
    assert "scope:sole-source-expansion" in ids


def test_mixed_amounts_only_flags_when_above_threshold():
    """Two amounts at exactly threshold and one well above — expansion fires."""
    doc = _doc(
        "Change order. Original contract $200,000. "
        "Not to exceed $300,000. Revised total $500,000."
    )
    anomalies = detect_scope_expansion_anomalies(doc)
    assert any(a["id"] == "scope:significant-expansion" for a in anomalies)
    finding = next(a for a in anomalies if a["id"] == "scope:significant-expansion")
    # Min is $200k, max is $500k → 150% expansion
    assert finding["details"]["expansion_percentage"] == 150.0
