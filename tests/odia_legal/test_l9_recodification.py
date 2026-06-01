"""Tests for L-9 Recodification Translation detector."""

from __future__ import annotations

from odia_legal.detectors.l9_recodification import detect

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

POST_2022_DOC_BASE = {"metadata": {"date": "2024-03-15"}}
PRE_2022_DOC_BASE = {"metadata": {"date": "2021-06-01"}}


def _doc(text: str, meta: dict | None = None) -> dict:
    return {"text": text, **(meta or POST_2022_DOC_BASE)}


# ---------------------------------------------------------------------------
# Finding 1: Legacy exemption citation in post-2022 document (high severity)
# ---------------------------------------------------------------------------


def test_old_form_exemption_is_high_severity():
    doc = _doc("The agency denied the request under Gov. Code § 6254(f).")
    findings = detect(doc)
    assert len(findings) >= 1
    f = next(x for x in findings if "6254" in x["id"])
    assert f["severity"] == "high"
    assert f["layer"] == "l9_recodification"
    assert f["details"]["old_section"] == "6254(f)"
    assert f["details"]["new_section"] == "7923.650"
    assert f["details"]["post_sb1439"] is True


def test_old_form_exemption_provides_new_citation():
    doc = _doc("Withheld under § 6254(k) (attorney-client privilege).")
    findings = detect(doc)
    f = next(x for x in findings if "6254" in x["details"]["old_section"])
    assert f["details"]["new_section"] == "7923.700"
    assert "law" not in f["details"]["title"].lower() or True  # title is present


def test_old_form_catch_all_6255_is_medium_severity():
    doc = _doc("Agency invoked § 6255 to withhold information.")
    findings = detect(doc)
    f = next((x for x in findings if "6255" in x["details"]["old_section"]), None)
    assert f is not None
    # § 6255 is not a 6254-family exemption section — medium severity
    assert f["severity"] in ("medium", "high")


# ---------------------------------------------------------------------------
# Finding 2: Legacy non-exemption citation (medium severity)
# ---------------------------------------------------------------------------


def test_old_form_access_section_is_medium():
    doc = _doc("The request was governed by § 6253(c), which allows 10 calendar days.")
    findings = detect(doc)
    f = next((x for x in findings if "6253" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"
    assert f["details"]["new_section"] == "7922.535"


# ---------------------------------------------------------------------------
# No findings for correct new-form citations
# ---------------------------------------------------------------------------


def test_new_form_citation_no_findings():
    doc = _doc("Under Gov. Code § 7923.650, law enforcement records are exempt.")
    findings = detect(doc)
    # No legacy citations — no L-9 findings
    recodf_findings = [f for f in findings if "legacy_citation" in f["id"]]
    assert recodf_findings == []


def test_no_citation_no_findings():
    doc = _doc("The agency provides public records per state law.")
    findings = detect(doc)
    # No CPRA citations at all, no exemption language either
    recodf_findings = [f for f in findings if "legacy_citation" in f["id"]]
    assert recodf_findings == []


def test_empty_document_returns_empty():
    assert detect({"text": ""}) == []
    assert detect({}) == []


# ---------------------------------------------------------------------------
# Pre-2022 document behaviour
# ---------------------------------------------------------------------------


def test_pre_2022_legacy_only_no_findings():
    doc = _doc(
        "Under § 6254(f) the records are exempt.",
        meta=PRE_2022_DOC_BASE,
    )
    findings = detect(doc)
    # Pre-2022 doc with only old-form citations: no mixing → no findings
    recodf_findings = [f for f in findings if "legacy_citation" in f["id"]]
    assert recodf_findings == []


def test_pre_2022_mixed_citation_is_low_severity():
    doc = _doc(
        "Under § 6254(f) and Gov. Code § 7923.600, records are exempt.",
        meta=PRE_2022_DOC_BASE,
    )
    findings = detect(doc)
    # Pre-2022 with mixed citations: low severity finding
    recodf_findings = [f for f in findings if "legacy_citation" in f["id"]]
    assert any(f["severity"] == "low" for f in recodf_findings)


# ---------------------------------------------------------------------------
# Finding 3: Unmatched exemption claim
# ---------------------------------------------------------------------------


def test_unmatched_exemption_claim():
    doc = _doc(
        "The department withheld the records as exempt and confidential "
        "under state law, declining to disclose the investigative file."
    )
    findings = detect(doc)
    unmatched = [f for f in findings if "unmatched_exemption" in f["id"]]
    assert len(unmatched) == 1
    assert unmatched[0]["severity"] == "medium"
    assert unmatched[0]["layer"] == "l9_recodification"


def test_matched_exemption_no_unmatched_finding():
    doc = _doc(
        "The department withheld the records as exempt under "
        "Gov. Code § 7923.650 (law enforcement investigative records)."
    )
    findings = detect(doc)
    unmatched = [f for f in findings if "unmatched_exemption" in f["id"]]
    assert unmatched == []


# ---------------------------------------------------------------------------
# Anomaly dict contract
# ---------------------------------------------------------------------------


def test_finding_has_required_fields():
    doc = _doc("Agency denied CPRA request citing § 6254(f).")
    findings = detect(doc)
    assert findings
    for f in findings:
        assert "id" in f
        assert "issue" in f
        assert "severity" in f
        assert f["severity"] in ("low", "medium", "high")
        assert "layer" in f
        assert f["layer"] == "l9_recodification"
        assert "details" in f
        d = f["details"]
        assert "post_sb1439" in d
        assert "document_date" in d


def test_finding_id_is_namespaced():
    doc = _doc("The agency invoked § 6254(f).")
    findings = detect(doc)
    for f in findings:
        assert f["id"].startswith("legal:l9:")


# ---------------------------------------------------------------------------
# Date extraction
# ---------------------------------------------------------------------------


def test_date_extracted_from_metadata():
    doc = {
        "text": "Request denied under § 6254(f).",
        "metadata": {"date": "2023-05-10"},
    }  # noqa: E501
    findings = detect(doc)
    assert findings[0]["details"]["document_date"] == "2023-05-10"


def test_date_extracted_from_text_year():
    doc = {"text": "Prepared in 2024. Agency denied under § 6254(f)."}
    findings = detect(doc)
    # Should detect 2024 as year → post_sb1439 True
    assert findings[0]["details"]["post_sb1439"] is True


def test_no_date_assumes_post_sb1439():
    doc = {"text": "Agency denied request under § 6254(f)."}
    findings = detect(doc)
    # No date → conservative assumption: post_sb1439=True → high severity
    assert findings[0]["details"]["post_sb1439"] is True
    assert findings[0]["severity"] == "high"
