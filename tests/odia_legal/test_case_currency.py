"""Tests for L-8 case-law currency / treatment signal extraction."""

from __future__ import annotations

from odia_legal.treatment.case_currency import (
    check_document_currency,
    get_treatment,
    is_good_law,
    treatment_table,
)


def _doc(text: str) -> dict:
    return {"text": text}


# ---------------------------------------------------------------------------
# get_treatment
# ---------------------------------------------------------------------------


def test_get_treatment_copley_press_superseded():
    t = get_treatment("Copley Press")
    assert t is not None
    assert t.status == "SUPERSEDED"
    assert "SB 1421" in (t.superseded_by or "")


def test_get_treatment_chevron_overruled():
    t = get_treatment("chevron")
    assert t is not None
    assert t.status == "OVERRULED"
    assert t.doctrinal_weight == 0.0


def test_get_treatment_cbs_block_good():
    t = get_treatment("CBS")
    assert t is not None
    assert t.status == "GOOD"


def test_get_treatment_none_for_unknown():
    t = get_treatment("completely unknown case xyz 999")
    assert t is None


# ---------------------------------------------------------------------------
# is_good_law
# ---------------------------------------------------------------------------


def test_is_good_law_copley_press_false():
    assert not is_good_law("Copley Press")


def test_is_good_law_cbs_true():
    assert is_good_law("CBS")


def test_is_good_law_unknown_returns_true():
    assert is_good_law("unknown case nobody ever cited")


# ---------------------------------------------------------------------------
# treatment_table
# ---------------------------------------------------------------------------


def test_treatment_table_not_empty():
    table = treatment_table()
    assert len(table) >= 5


def test_treatment_table_has_superseded():
    statuses = {t.status for t in treatment_table()}
    assert "SUPERSEDED" in statuses
    assert "OVERRULED" in statuses
    assert "GOOD" in statuses


# ---------------------------------------------------------------------------
# check_document_currency (L-8 detector)
# ---------------------------------------------------------------------------


def test_copley_press_keyword_triggers_finding():
    doc = _doc(
        "Under Copley Press, all officer personnel records were confidential "
        "before SB 1421."
    )
    findings = check_document_currency(doc)
    assert any("copley_press" in f["id"] for f in findings)


def test_copley_press_finding_medium_severity():
    doc = _doc("The Copley Press decision held officer records confidential.")
    findings = check_document_currency(doc)
    f = next((x for x in findings if "copley_press" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"  # SUPERSEDED → medium


def test_chevron_finding_high_severity():
    doc = _doc(
        "Under Chevron USA v. Natural Resources Defense Council, we defer to "
        "the agency interpretation."
    )
    findings = check_document_currency(doc)
    f = next((x for x in findings if "chevron" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"  # OVERRULED → high


def test_good_case_no_finding():
    doc = _doc(
        "Under CBS, Inc. v. Block (1986) 42 Cal.3d 646, the agency bears the "
        "burden of proving the exemption applies."
    )
    findings = check_document_currency(doc)
    assert findings == []


def test_empty_doc_no_findings():
    assert check_document_currency({"text": ""}) == []
    assert check_document_currency({}) == []


def test_finding_has_required_fields():
    doc = _doc("The Copley Press rule applies to these records.")
    findings = check_document_currency(doc)
    for f in findings:
        assert f["id"].startswith("legal:l8:")
        assert f["layer"] == "l8_case_currency"
        assert f["severity"] in ("low", "medium", "high")
        d = f["details"]
        assert "case_name" in d
        assert "citation" in d
        assert "status" in d
        assert "doctrinal_weight" in d


def test_finding_includes_superseded_by():
    doc = _doc("The Copley Press decision says officer records are confidential.")
    findings = check_document_currency(doc)
    f = next((x for x in findings if "copley_press" in x["id"]), None)
    assert f is not None
    assert "SB 1421" in (f["details"]["superseded_by"] or "")
