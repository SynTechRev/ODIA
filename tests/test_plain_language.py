"""Tests for src/oraculus_di_auditor/reporting/plain_language.py."""

from __future__ import annotations

import pytest

from oraculus_di_auditor.reporting.plain_language import (
    TRANSLATIONS,
    translate_finding,
    translate_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_finding(layer: str, subtype: str, severity: str = "high") -> dict:
    return {
        "id": f"{layer}:{subtype}",
        "issue": f"Test issue for {layer}:{subtype}",
        "severity": severity,
        "layer": layer,
        "details": {"test": True},
    }


# ---------------------------------------------------------------------------
# translate_finding — field presence
# ---------------------------------------------------------------------------


class TestTranslateFindingFields:
    def test_adds_plain_summary(self):
        f = translate_finding(_make_finding("fiscal", "amount_without_appropriation"))
        assert "plain_summary" in f

    def test_adds_plain_impact(self):
        f = translate_finding(_make_finding("fiscal", "amount_without_appropriation"))
        assert "plain_impact" in f

    def test_adds_plain_action(self):
        f = translate_finding(_make_finding("fiscal", "amount_without_appropriation"))
        assert "plain_action" in f

    def test_original_fields_preserved(self):
        original = _make_finding("fiscal", "amount_without_appropriation")
        result = translate_finding(original)
        assert result["id"] == original["id"]
        assert result["severity"] == original["severity"]
        assert result["layer"] == original["layer"]

    def test_original_dict_not_mutated(self):
        original = _make_finding("fiscal", "amount_without_appropriation")
        original_copy = dict(original)
        translate_finding(original)
        assert original == original_copy

    def test_plain_fields_are_non_empty_strings(self):
        f = translate_finding(_make_finding("fiscal", "amount_without_appropriation"))
        assert isinstance(f["plain_summary"], str) and f["plain_summary"]
        assert isinstance(f["plain_impact"], str) and f["plain_impact"]
        assert isinstance(f["plain_action"], str) and f["plain_action"]


# ---------------------------------------------------------------------------
# translate_finding — known detector types
# ---------------------------------------------------------------------------


class TestKnownDetectorTypes:
    @pytest.mark.parametrize("detector,subtype", [
        ("procurement_timeline", "execution_before_authorization"),
        ("procurement_timeline", "rapid_execution"),
        ("signature_chain", "blank_signature"),
        ("signature_chain", "pending_docusign"),
        ("governance_gap", "capability_without_governance"),
        ("scope_expansion", "amendment_exceeds_threshold"),
        ("scope_expansion", "sole_source_expansion"),
        ("surveillance", "outsourcing_detected"),
        ("fiscal", "amount_without_appropriation"),
        ("fiscal", "missing_provenance_hash"),
        ("constitutional", "broad_delegation"),
        ("administrative_integrity", "missing_final_action"),
        ("administrative_integrity", "retroactive_authorization"),
        ("cross_reference", "jurisdiction_boundary"),
        ("temporal_pattern", "contract_evolution"),
    ])
    def test_known_type_returns_specific_translation(self, detector, subtype):
        f = translate_finding(_make_finding(detector, subtype))
        # Specific translations should not be the generic fallback
        assert "anomaly was detected" not in f["plain_summary"]
        assert len(f["plain_summary"]) > 20

    def test_fiscal_summary_mentions_spending_or_funds(self):
        f = translate_finding(_make_finding("fiscal", "amount_without_appropriation"))
        text = f["plain_summary"].lower()
        assert any(word in text for word in ("spending", "funds", "document", "budget"))

    def test_procurement_summary_mentions_contract_or_council(self):
        f = translate_finding(_make_finding("procurement_timeline", "execution_before_authorization"))
        text = f["plain_summary"].lower()
        assert any(word in text for word in ("contract", "council", "voted", "signed"))

    def test_governance_gap_mentions_surveillance(self):
        f = translate_finding(_make_finding("governance_gap", "capability_without_governance"))
        text = f["plain_summary"].lower()
        assert "surveillance" in text or "technology" in text


# ---------------------------------------------------------------------------
# translate_finding — aliases and fallbacks
# ---------------------------------------------------------------------------


class TestAliasesAndFallbacks:
    def test_alias_procurement_maps_to_procurement_timeline(self):
        finding = {
            "id": "procurement:execution_before_authorization",
            "issue": "test",
            "severity": "high",
            "layer": "procurement",
            "details": {},
        }
        f = translate_finding(finding)
        # Should resolve via alias
        assert "anomaly was detected" not in f["plain_summary"]

    def test_unknown_detector_gets_fallback(self):
        f = translate_finding({
            "id": "unknown_detector:unknown_subtype",
            "issue": "test",
            "severity": "medium",
            "layer": "unknown_detector",
            "details": {},
        })
        assert "anomaly was detected" in f["plain_summary"].lower()
        assert "professional review" in f["plain_impact"].lower()

    def test_known_detector_unknown_subtype_gets_fallback(self):
        f = translate_finding(_make_finding("fiscal", "totally_unknown_subtype"))
        # May get fallback or partial match — should always have non-empty fields
        assert f["plain_summary"]
        assert f["plain_impact"]
        assert f["plain_action"]

    def test_finding_without_id_uses_layer(self):
        finding = {
            "issue": "test",
            "severity": "low",
            "layer": "fiscal",
            "details": {},
        }
        f = translate_finding(finding)
        assert "plain_summary" in f

    def test_severity_mentioned_in_fallback(self):
        f = translate_finding({
            "id": "nonexistent:subtype",
            "issue": "test",
            "severity": "critical",
            "layer": "nonexistent",
            "details": {},
        })
        assert "critical" in f["plain_summary"]


# ---------------------------------------------------------------------------
# translate_report
# ---------------------------------------------------------------------------


class TestTranslateReport:
    def test_empty_list_returns_empty(self):
        assert translate_report([]) == []

    def test_all_findings_get_translated(self):
        findings = [
            _make_finding("fiscal", "amount_without_appropriation"),
            _make_finding("procurement_timeline", "execution_before_authorization"),
            _make_finding("constitutional", "broad_delegation"),
        ]
        results = translate_report(findings)
        assert len(results) == 3
        for r in results:
            assert "plain_summary" in r
            assert "plain_impact" in r
            assert "plain_action" in r

    def test_returns_new_list_not_mutation(self):
        findings = [_make_finding("fiscal", "amount_without_appropriation")]
        results = translate_report(findings)
        assert results is not findings
        assert "plain_summary" not in findings[0]

    def test_order_preserved(self):
        findings = [
            _make_finding("fiscal", "amount_without_appropriation"),
            _make_finding("surveillance", "outsourcing_detected"),
            _make_finding("constitutional", "broad_delegation"),
        ]
        results = translate_report(findings)
        for original, translated in zip(findings, results):
            assert translated["layer"] == original["layer"]


# ---------------------------------------------------------------------------
# TRANSLATIONS dict completeness
# ---------------------------------------------------------------------------


class TestTranslationsDict:
    def test_all_detector_types_present(self):
        required = [
            "procurement_timeline",
            "signature_chain",
            "governance_gap",
            "scope_expansion",
            "surveillance",
            "fiscal",
            "constitutional",
            "administrative_integrity",
            "cross_reference",
            "temporal_pattern",
        ]
        for detector in required:
            assert detector in TRANSLATIONS, f"Missing detector in TRANSLATIONS: {detector}"

    def test_each_translation_has_required_fields(self):
        for detector, subtypes in TRANSLATIONS.items():
            for subtype, t in subtypes.items():
                assert "summary" in t, f"{detector}:{subtype} missing 'summary'"
                assert "impact" in t, f"{detector}:{subtype} missing 'impact'"
                assert "action" in t, f"{detector}:{subtype} missing 'action'"

    def test_no_empty_translation_values(self):
        for detector, subtypes in TRANSLATIONS.items():
            for subtype, t in subtypes.items():
                for key in ("summary", "impact", "action"):
                    assert t[key].strip(), (
                        f"{detector}:{subtype}[{key}] is empty"
                    )
