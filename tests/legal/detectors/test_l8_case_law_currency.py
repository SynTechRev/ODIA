"""Tests for L-8 Case Law Currency detector.

Coverage: CC-1 through CC-5 fire and no-fire cases,
edge cases, false-positive guards on clean civic text.
"""

from __future__ import annotations

from datetime import date

import pytest
from oraculus_di_auditor.legal.detectors._base import DocContext, Severity
from oraculus_di_auditor.legal.detectors.l8_case_law_currency import (
    L8CaseLawCurrency,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def detector():
    return L8CaseLawCurrency()


def _ctx(text: str, doc_type: str = "policy") -> DocContext:
    import hashlib

    return DocContext(
        document_id="test-l8-001",
        document_hash=hashlib.sha256(text.encode()).hexdigest(),
        document_type=doc_type,
        jurisdiction="fresnocounty",
        authority="Fresno County Sheriff",
        version_date=date(2026, 1, 15),
        text=text,
        source_finding=None,
    )


# ---------------------------------------------------------------------------
# CC-1: Smith v. Maryland third-party doctrine stale -- no Carpenter
# ---------------------------------------------------------------------------

_CC1_FIRE_SMITH = (
    "Under Smith v. Maryland, 442 U.S. 735 (1979), the department maintains "
    "that subscribers have no reasonable expectation of privacy in cell phone "
    "location data transmitted to the carrier. Accordingly, no warrant is required "
    "to obtain historical location records from wireless providers."
)

_CC1_FIRE_THIRD_PARTY = (
    "The third-party doctrine provides that digital records shared with a service "
    "provider carry no Fourth Amendment protection. The department obtained 90 days "
    "of cell-site location information without a warrant on this basis."
)

_CC1_NO_FIRE_CARPENTER = (
    "Under Smith v. Maryland, metadata transmitted to third parties traditionally "
    "lacked Fourth Amendment protection. However, as the Court held in Carpenter v. "
    "United States, 138 S. Ct. 2206 (2018), this doctrine does not extend to "
    "seven or more days of cell-site location information. A warrant is required."
)

_CC1_NO_FIRE_CARPENTER_ONLY = (
    "Pursuant to Carpenter v. United States (2018), a warrant is required before "
    "obtaining historical cell-site location information from a wireless carrier."
)


def test_cc1_fires_on_smith_no_carpenter(detector):
    findings = detector.detect(_ctx(_CC1_FIRE_SMITH), resolver=None)
    cc1 = [f for f in findings if f.notes and "CC-1" in f.notes]
    assert cc1, "CC-1 should fire on Smith v. Maryland without Carpenter"
    assert cc1[0].severity == Severity.HIGH


def test_cc1_fires_on_third_party_digital_no_carpenter(detector):
    findings = detector.detect(_ctx(_CC1_FIRE_THIRD_PARTY), resolver=None)
    cc1 = [f for f in findings if f.notes and "CC-1" in f.notes]
    assert (
        cc1
    ), "CC-1 should fire on third-party doctrine for digital records without Carpenter"


def test_cc1_no_fire_when_carpenter_cited(detector):
    findings = detector.detect(_ctx(_CC1_NO_FIRE_CARPENTER), resolver=None)
    cc1 = [f for f in findings if f.notes and "CC-1" in f.notes]
    assert not cc1


def test_cc1_no_fire_carpenter_alone(detector):
    findings = detector.detect(_ctx(_CC1_NO_FIRE_CARPENTER_ONLY), resolver=None)
    cc1 = [f for f in findings if f.notes and "CC-1" in f.notes]
    assert not cc1


def test_cc1_statutes_applied(detector):
    findings = detector.detect(_ctx(_CC1_FIRE_SMITH), resolver=None)
    cc1 = [f for f in findings if f.notes and "CC-1" in f.notes]
    statutes = cc1[0].statutes_applied if cc1 else []
    assert any("Carpenter" in s for s in statutes)
    assert any("Smith v. Maryland" in s for s in statutes)


# ---------------------------------------------------------------------------
# CC-2: Repealed CPRA section citations (§ 6250-§ 6276)
# ---------------------------------------------------------------------------

_CC2_FIRE_6254 = (
    "The department denies this public records request pursuant to Government Code "
    "§ 6254(f), which exempts records of complaints and investigations of peace "
    "officers from disclosure. See also § 6255 for the catch-all exemption."
)

_CC2_FIRE_6250 = (
    "This response is governed by the California Public Records Act (Gov. Code § 6250 "
    "et seq.). Records may be withheld under Government Code § 6254."
)

_CC2_NO_FIRE_NEW_SECTIONS = (
    "Pursuant to the California Public Records Act as recodified (Gov. Code § 7922.000 "
    "et seq.), the department provides responsive records. Exemptions under § 7923.600 "
    "apply to peace officer records."
)

_CC2_NO_FIRE_BOTH = (
    "The old Government Code § 6254 has been recodified. This denial is issued under "
    "the new California Public Records Act section numbering (Gov. Code § 7920 et seq.) "
    "effective January 1, 2023."
)


def test_cc2_fires_on_old_cpra_section(detector):
    findings = detector.detect(_ctx(_CC2_FIRE_6254), resolver=None)
    cc2 = [f for f in findings if f.notes and "CC-2" in f.notes]
    assert cc2, "CC-2 should fire on old CPRA § 6254 without § 7920 recodification"
    assert cc2[0].severity == Severity.HIGH


def test_cc2_fires_on_6250_et_seq(detector):
    findings = detector.detect(_ctx(_CC2_FIRE_6250), resolver=None)
    cc2 = [f for f in findings if f.notes and "CC-2" in f.notes]
    assert cc2


def test_cc2_no_fire_new_sections(detector):
    findings = detector.detect(_ctx(_CC2_NO_FIRE_NEW_SECTIONS), resolver=None)
    cc2 = [f for f in findings if f.notes and "CC-2" in f.notes]
    assert not cc2


def test_cc2_no_fire_both_old_and_new(detector):
    findings = detector.detect(_ctx(_CC2_NO_FIRE_BOTH), resolver=None)
    cc2 = [f for f in findings if f.notes and "CC-2" in f.notes]
    assert not cc2


def test_cc2_statutes_applied(detector):
    findings = detector.detect(_ctx(_CC2_FIRE_6254), resolver=None)
    cc2 = [f for f in findings if f.notes and "CC-2" in f.notes]
    statutes = cc2[0].statutes_applied if cc2 else []
    assert any("7920" in s for s in statutes)


# ---------------------------------------------------------------------------
# CC-3: Pre-Riley search incident to arrest for digital devices
# ---------------------------------------------------------------------------

_CC3_FIRE_SITA_PHONE = (
    "Officers are authorized to search cell phones incident to a lawful arrest "
    "without obtaining a warrant. This authority derives from the search-incident-to-"
    "arrest exception and permits inspection of the phone's contents."
)

_CC3_FIRE_SMARTPHONE = (
    "The search-incident-to-arrest doctrine permits a full search of a smartphone "
    "found on the arrestee. The Robinson rule supports this warrantless search "
    "of the electronic device."
)

_CC3_NO_FIRE_RILEY = (
    "While the search-incident-to-arrest exception applies to physical items found "
    "on an arrestee, Riley v. California, 573 U.S. 373 (2014), held that officers "
    "must obtain a warrant before searching a cell phone incident to arrest, absent "
    "exigent circumstances."
)

_CC3_NO_FIRE_RILEY_SHORT = (
    "A warrant is required to search a cell phone, per Riley v. California (2014), "
    "even when found on an arrestee."
)


def test_cc3_fires_on_sita_phone_no_riley(detector):
    findings = detector.detect(_ctx(_CC3_FIRE_SITA_PHONE), resolver=None)
    cc3 = [f for f in findings if f.notes and "CC-3" in f.notes]
    assert (
        cc3
    ), "CC-3 should fire on search incident to arrest for cell phone without Riley"
    assert cc3[0].severity == Severity.HIGH


def test_cc3_fires_on_robinson_smartphone(detector):
    findings = detector.detect(_ctx(_CC3_FIRE_SMARTPHONE), resolver=None)
    cc3 = [f for f in findings if f.notes and "CC-3" in f.notes]
    assert cc3


def test_cc3_no_fire_when_riley_cited(detector):
    findings = detector.detect(_ctx(_CC3_NO_FIRE_RILEY), resolver=None)
    cc3 = [f for f in findings if f.notes and "CC-3" in f.notes]
    assert not cc3


def test_cc3_no_fire_riley_short(detector):
    findings = detector.detect(_ctx(_CC3_NO_FIRE_RILEY_SHORT), resolver=None)
    cc3 = [f for f in findings if f.notes and "CC-3" in f.notes]
    assert not cc3


def test_cc3_statutes_applied(detector):
    findings = detector.detect(_ctx(_CC3_FIRE_SITA_PHONE), resolver=None)
    cc3 = [f for f in findings if f.notes and "CC-3" in f.notes]
    statutes = cc3[0].statutes_applied if cc3 else []
    assert any("Riley" in s for s in statutes)


# ---------------------------------------------------------------------------
# CC-4: Pre-AB 392 "reasonable force" without "necessary" standard
# ---------------------------------------------------------------------------

_CC4_FIRE_REASONABLE = (
    "Officers may use reasonable force to effect an arrest, prevent escape, or "
    "overcome resistance. The department's use-of-force policy is based on the "
    "objective reasonableness standard established in Graham v. Connor, 490 U.S. 386."
)

_CC4_FIRE_CA_REASONABLE = (
    "California law enforcement officers may use reasonable force as appropriate. "
    "The use-of-force policy authorizes reasonable force in all circumstances "
    "where resistance is encountered."
)

_CC4_NO_FIRE_NECESSARY = (
    "Officers may use force only when necessary to defend against an imminent threat "
    "of death or serious bodily injury, consistent with the standard set forth in "
    "California Penal Code § 835a as amended by AB 392 (2019)."
)

_CC4_NO_FIRE_AB392 = (
    "Pursuant to AB 392 and Cal. Pen. Code § 835a, effective January 1, 2020, "
    "deadly force is authorized only when necessary. The department's use-of-force "
    "policy incorporates both the federal objective reasonableness standard and the "
    "California 'necessary' standard."
)

_CC4_NO_FIRE_NO_CA_LE_CONTEXT = (
    "The contract requires reasonable force provisions in line with industry practice. "
    "Reasonable force is a standard term in security service agreements."
)


def test_cc4_fires_on_reasonable_force_no_necessary(detector):
    findings = detector.detect(_ctx(_CC4_FIRE_REASONABLE), resolver=None)
    cc4 = [f for f in findings if f.notes and "CC-4" in f.notes]
    assert (
        cc4
    ), "CC-4 should fire on 'reasonable force' for law enforcement without 'necessary'"
    assert cc4[0].severity == Severity.HIGH


def test_cc4_fires_on_ca_reasonable_no_necessary(detector):
    findings = detector.detect(_ctx(_CC4_FIRE_CA_REASONABLE), resolver=None)
    cc4 = [f for f in findings if f.notes and "CC-4" in f.notes]
    assert cc4


def test_cc4_no_fire_when_necessary_standard_cited(detector):
    findings = detector.detect(_ctx(_CC4_NO_FIRE_NECESSARY), resolver=None)
    cc4 = [f for f in findings if f.notes and "CC-4" in f.notes]
    assert not cc4


def test_cc4_no_fire_when_ab392_cited(detector):
    findings = detector.detect(_ctx(_CC4_NO_FIRE_AB392), resolver=None)
    cc4 = [f for f in findings if f.notes and "CC-4" in f.notes]
    assert not cc4


def test_cc4_statutes_applied(detector):
    findings = detector.detect(_ctx(_CC4_FIRE_REASONABLE), resolver=None)
    cc4 = [f for f in findings if f.notes and "CC-4" in f.notes]
    statutes = cc4[0].statutes_applied if cc4 else []
    assert any("835a" in s for s in statutes)
    assert any("AB 392" in s for s in statutes)


# ---------------------------------------------------------------------------
# CC-5: Qualified immunity for California constitutional claims without SB 2
# ---------------------------------------------------------------------------

_CC5_FIRE_QI_CA = (
    "The individual defendants are entitled to qualified immunity under the "
    "California Constitution claims. Officers could not have known that their "
    "conduct violated clearly established California constitutional rights."
)

_CC5_FIRE_QI_BANE = (
    "Qualified immunity provides a complete defense to the Bane Act claim. "
    "The officers acted on reasonable belief and are protected by qualified "
    "immunity under California state law."
)

_CC5_NO_FIRE_SB2 = (
    "Qualified immunity is available as a defense to the federal § 1983 claims. "
    "However, as enacted by SB 2 (Cal. Pen. Code § 1021.7, eff. Jan. 1, 2022), "
    "qualified immunity is not available as a defense to claims under California law."
)

_CC5_NO_FIRE_1021 = (
    "Note that Penal Code § 1021.7 eliminates qualified immunity as a defense to "
    "California civil rights claims. The state Bane Act claim proceeds regardless "
    "of federal qualified immunity analysis."
)

_CC5_NO_FIRE_FEDERAL_ONLY = (
    "Qualified immunity under § 1983 bars this federal civil rights claim. "
    "The officers acted on an objectively reasonable interpretation of existing law."
)


def test_cc5_fires_on_qi_california_no_sb2(detector):
    findings = detector.detect(_ctx(_CC5_FIRE_QI_CA), resolver=None)
    cc5 = [f for f in findings if f.notes and "CC-5" in f.notes]
    assert cc5, "CC-5 should fire on qualified immunity asserted for California claim without SB 2"
    assert cc5[0].severity == Severity.HIGH


def test_cc5_fires_on_qi_bane_act_no_sb2(detector):
    findings = detector.detect(_ctx(_CC5_FIRE_QI_BANE), resolver=None)
    cc5 = [f for f in findings if f.notes and "CC-5" in f.notes]
    assert cc5


def test_cc5_no_fire_when_sb2_cited(detector):
    findings = detector.detect(_ctx(_CC5_NO_FIRE_SB2), resolver=None)
    cc5 = [f for f in findings if f.notes and "CC-5" in f.notes]
    assert not cc5


def test_cc5_no_fire_when_1021_7_cited(detector):
    findings = detector.detect(_ctx(_CC5_NO_FIRE_1021), resolver=None)
    cc5 = [f for f in findings if f.notes and "CC-5" in f.notes]
    assert not cc5


def test_cc5_no_fire_federal_claim_only(detector):
    findings = detector.detect(_ctx(_CC5_NO_FIRE_FEDERAL_ONLY), resolver=None)
    cc5 = [f for f in findings if f.notes and "CC-5" in f.notes]
    assert not cc5


def test_cc5_statutes_applied(detector):
    findings = detector.detect(_ctx(_CC5_FIRE_QI_CA), resolver=None)
    cc5 = [f for f in findings if f.notes and "CC-5" in f.notes]
    statutes = cc5[0].statutes_applied if cc5 else []
    assert any("1021.7" in s for s in statutes)
    assert any("SB 2" in s for s in statutes)


# ---------------------------------------------------------------------------
# Structural / protocol tests
# ---------------------------------------------------------------------------


def test_detector_id():
    assert L8CaseLawCurrency.detector_id == "l8-case-law-currency"


def test_returns_list_on_empty_text(detector):
    findings = detector.detect(_ctx(""), resolver=None)
    assert isinstance(findings, list)


def test_returns_empty_on_clean_civic_text(detector):
    clean = (
        "The Board of Supervisors approved the fiscal year 2026-2027 budget. "
        "All appropriations are consistent with state law and local ordinances. "
        "No contracts were awarded at this meeting."
    )
    findings = detector.detect(_ctx(clean), resolver=None)
    assert findings == []


def test_finding_shape(detector):
    findings = detector.detect(_ctx(_CC2_FIRE_6254), resolver=None)
    for f in findings:
        d = f.to_anomaly_dict()
        assert d["layer"] == "legal"
        assert d["severity"] in ("low", "medium", "high", "critical")
        assert "sub_detector" in d["details"]
        assert d["details"]["sub_detector"] == "l8-case-law-currency"


def test_exception_returns_empty_list(detector):
    """Detector must never raise; it returns [] on any exception."""
    ctx = _ctx("normal civic text")
    findings = detector.detect(ctx, resolver=object())
    assert isinstance(findings, list)


def test_multiple_rules_can_fire_in_one_document(detector):
    combined = (
        "The department denies this request under Government Code § 6254(f). "
        "Officers may use reasonable force in all circumstances, per department policy. "
        "Smith v. Maryland establishes no expectation of privacy for third-party records."
    )
    findings = detector.detect(_ctx(combined), resolver=None)
    codes = [f.notes.split(":")[0].strip() if f.notes else "" for f in findings]
    assert len(set(codes)) >= 2, "Multiple rules should independently fire"
