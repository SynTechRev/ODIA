"""Tests for L-9 Statute Citation Auditor detector.

Coverage: SA-1 through SA-5 fire and no-fire cases,
structured parser behavior, and false-positive guards.
"""

from __future__ import annotations

from datetime import date

import pytest
from oraculus_di_auditor.legal.detectors._base import DocContext, Severity
from oraculus_di_auditor.legal.detectors.l9_statute_citation_auditor import (
    L9StatuteCitationAuditor,
)


@pytest.fixture
def detector():
    return L9StatuteCitationAuditor()


def _ctx(text: str, doc_type: str = "policy") -> DocContext:
    import hashlib

    return DocContext(
        document_id="test-l9-001",
        document_hash=hashlib.sha256(text.encode()).hexdigest(),
        document_type=doc_type,
        jurisdiction="fresnocounty",
        authority="Fresno County Sheriff",
        version_date=date(2026, 1, 15),
        text=text,
        source_finding=None,
    )


# ---------------------------------------------------------------------------
# SA-1: Old CPRA Gov. Code §§ 6250-6276 via structured parser
# ---------------------------------------------------------------------------

_SA1_FIRE_6254 = (
    "The department denies the request for records pursuant to Government Code "
    "§ 6254(f), which exempts records of complaints about peace officers. "
    "See also Government Code § 6255 for the catchall exemption."
)

_SA1_FIRE_DECIMAL = (
    "Records are withheld under Government Code § 6276.48 (exemption for "
    "preliminary drafts not retained by the agency) and Government Code § 6254(f). "
    "This response is issued pursuant to the California Public Records Act."
)

_SA1_FIRE_6250 = (
    "The California Public Records Act (Government Code § 6250 et seq.) "
    "governs the right of access to public records in this jurisdiction."
)

_SA1_NO_FIRE_NEW = (
    "Pursuant to the California Public Records Act (Gov. Code § 7922.000 et seq.), "
    "the department provides responsive records. Exemptions under Gov. Code § 7923.600 "
    "apply to peace officer personnel records."
)

_SA1_NO_FIRE_OLD_AND_NEW = (
    "The old Government Code § 6254 has been superseded. This denial is issued "
    "under Government Code § 7922.000 effective January 1, 2023."
)


def test_sa1_fires_on_6254(detector):
    findings = detector.detect(_ctx(_SA1_FIRE_6254), resolver=None)
    sa1 = [f for f in findings if f.notes and "SA-1" in f.notes]
    assert sa1, "SA-1 should fire on Gov. Code § 6254 without § 7920+ citation"
    assert sa1[0].severity == Severity.HIGH


def test_sa1_fires_on_decimal_section(detector):
    findings = detector.detect(_ctx(_SA1_FIRE_DECIMAL), resolver=None)
    sa1 = [f for f in findings if f.notes and "SA-1" in f.notes]
    assert sa1, "SA-1 should fire on Gov. Code § 6276.48 (decimal old CPRA section)"


def test_sa1_fires_on_6250(detector):
    findings = detector.detect(_ctx(_SA1_FIRE_6250), resolver=None)
    sa1 = [f for f in findings if f.notes and "SA-1" in f.notes]
    assert sa1


def test_sa1_no_fire_new_sections(detector):
    findings = detector.detect(_ctx(_SA1_NO_FIRE_NEW), resolver=None)
    sa1 = [f for f in findings if f.notes and "SA-1" in f.notes]
    assert not sa1


def test_sa1_no_fire_old_and_new_present(detector):
    findings = detector.detect(_ctx(_SA1_NO_FIRE_OLD_AND_NEW), resolver=None)
    sa1 = [f for f in findings if f.notes and "SA-1" in f.notes]
    assert not sa1


def test_sa1_confidence(detector):
    findings = detector.detect(_ctx(_SA1_FIRE_6254), resolver=None)
    sa1 = [f for f in findings if f.notes and "SA-1" in f.notes]
    assert sa1[0].confidence >= 0.85


def test_sa1_reports_exact_section(detector):
    findings = detector.detect(_ctx(_SA1_FIRE_6254), resolver=None)
    sa1 = [f for f in findings if f.notes and "SA-1" in f.notes]
    # The notes should contain the exact section number
    assert "6254" in sa1[0].notes


# ---------------------------------------------------------------------------
# SA-2: CCP § 1281.97/98 without § 1281.96
# ---------------------------------------------------------------------------

_SA2_FIRE_97 = (
    "This arbitration agreement is subject to Cal. Code Civ. Proc. § 1281.97. "
    "The employer must pay the arbitration initiation fee within 30 days of "
    "the employee's demand, or forfeit the right to arbitrate."
)

_SA2_FIRE_98 = (
    "Pursuant to CCP § 1281.98, the consumer arbitration fees must be paid "
    "by the company within 30 days. Failure to pay results in a material "
    "breach of the arbitration agreement."
)

_SA2_NO_FIRE_HAS_96 = (
    "This agreement is subject to CCP § 1281.96 (annual data reporting), "
    "§ 1281.97 (employer fee requirements), and § 1281.98 (consumer fee requirements). "
    "All three provisions of the FAIR Act apply."
)

_SA2_NO_FIRE_NO_ARBITRATION = (
    "The parties agree to resolve disputes through mediation. The governing "
    "law is California and venue is in Fresno County Superior Court."
)


def test_sa2_fires_on_1281_97_without_96(detector):
    findings = detector.detect(_ctx(_SA2_FIRE_97), resolver=None)
    sa2 = [f for f in findings if f.notes and "SA-2" in f.notes]
    assert sa2, "SA-2 should fire on CCP § 1281.97 without § 1281.96"
    assert sa2[0].severity == Severity.MEDIUM


def test_sa2_fires_on_1281_98_without_96(detector):
    findings = detector.detect(_ctx(_SA2_FIRE_98), resolver=None)
    sa2 = [f for f in findings if f.notes and "SA-2" in f.notes]
    assert sa2


def test_sa2_no_fire_when_96_present(detector):
    findings = detector.detect(_ctx(_SA2_NO_FIRE_HAS_96), resolver=None)
    sa2 = [f for f in findings if f.notes and "SA-2" in f.notes]
    assert not sa2


def test_sa2_no_fire_no_arbitration(detector):
    findings = detector.detect(_ctx(_SA2_NO_FIRE_NO_ARBITRATION), resolver=None)
    sa2 = [f for f in findings if f.notes and "SA-2" in f.notes]
    assert not sa2


def test_sa2_statutes_applied(detector):
    findings = detector.detect(_ctx(_SA2_FIRE_97), resolver=None)
    sa2 = [f for f in findings if f.notes and "SA-2" in f.notes]
    statutes = sa2[0].statutes_applied if sa2 else []
    assert any("1281.96" in s for s in statutes)


# ---------------------------------------------------------------------------
# SA-3: Pen. Code § 832.7 without SB 1421 acknowledgment
# ---------------------------------------------------------------------------

_SA3_FIRE_832 = (
    "Pursuant to California Penal Code § 832.7, all peace officer personnel "
    "records are confidential and shall not be disclosed in response to a "
    "CPRA request. This response is issued under § 832.7 and § 832.8."
)

_SA3_NO_FIRE_SB1421 = (
    "Peace officer personnel records are generally confidential under Penal "
    "Code § 832.7. However, pursuant to SB 1421, § 832.7(b) requires disclosure "
    "of records related to serious use of force, sustained dishonesty findings, "
    "and sexual assault. The department has reviewed the requested records "
    "against these mandatory disclosure categories."
)

_SA3_NO_FIRE_832B = (
    "Penal Code § 832.7(b) mandates disclosure of certain peace officer records. "
    "The department is producing records that fall within the mandatory disclosure "
    "categories."
)

_SA3_NO_FIRE_UNRELATED = (
    "The employee handbook sets out workplace conduct standards. All employees "
    "must comply with departmental policies and applicable state law."
)


def test_sa3_fires_on_832_7_without_b(detector):
    findings = detector.detect(_ctx(_SA3_FIRE_832), resolver=None)
    sa3 = [f for f in findings if f.notes and "SA-3" in f.notes]
    assert sa3, "SA-3 should fire on Pen. Code § 832.7 without SB 1421 acknowledgment"
    assert sa3[0].severity == Severity.HIGH


def test_sa3_no_fire_when_sb1421_cited(detector):
    findings = detector.detect(_ctx(_SA3_NO_FIRE_SB1421), resolver=None)
    sa3 = [f for f in findings if f.notes and "SA-3" in f.notes]
    assert not sa3


def test_sa3_no_fire_when_832b_cited(detector):
    findings = detector.detect(_ctx(_SA3_NO_FIRE_832B), resolver=None)
    sa3 = [f for f in findings if f.notes and "SA-3" in f.notes]
    assert not sa3


def test_sa3_no_fire_unrelated(detector):
    findings = detector.detect(_ctx(_SA3_NO_FIRE_UNRELATED), resolver=None)
    sa3 = [f for f in findings if f.notes and "SA-3" in f.notes]
    assert not sa3


def test_sa3_statutes_applied(detector):
    findings = detector.detect(_ctx(_SA3_FIRE_832), resolver=None)
    sa3 = [f for f in findings if f.notes and "SA-3" in f.notes]
    statutes = sa3[0].statutes_applied if sa3 else []
    assert any("SB 1421" in s for s in statutes)


# ---------------------------------------------------------------------------
# SA-4: Federal grant citation without California oversight companion
# ---------------------------------------------------------------------------

_SA4_FIRE_JAG = (
    "This project is funded through the Byrne Justice Assistance Grant program "
    "under 34 U.S.C. § 10152. The department is authorized to use these funds "
    "to purchase surveillance equipment."
)

_SA4_FIRE_USC42 = (
    "The department receives federal funding under 42 U.S.C. § 3796 "
    "for law enforcement activities."
)

_SA4_NO_FIRE_HAS_GOV_CODE = (
    "This project is funded under 34 U.S.C. § 10152 (Byrne JAG). Pursuant to "
    "California Government Code § 26224, all county expenditures from this grant "
    "are subject to Board of Supervisors approval."
)

_SA4_NO_FIRE_NO_USC = (
    "The department budget is approved by the Board of Supervisors under "
    "California Government Code § 29000 et seq."
)


def test_sa4_fires_on_jag_no_cal_companion(detector):
    findings = detector.detect(_ctx(_SA4_FIRE_JAG), resolver=None)
    sa4 = [f for f in findings if f.notes and "SA-4" in f.notes]
    assert sa4, "SA-4 should fire on JAG citation without Cal. Gov. Code companion"
    assert sa4[0].severity == Severity.MEDIUM


def test_sa4_fires_on_usc_42_no_cal(detector):
    findings = detector.detect(_ctx(_SA4_FIRE_USC42), resolver=None)
    sa4 = [f for f in findings if f.notes and "SA-4" in f.notes]
    assert sa4


def test_sa4_no_fire_has_gov_code(detector):
    findings = detector.detect(_ctx(_SA4_NO_FIRE_HAS_GOV_CODE), resolver=None)
    sa4 = [f for f in findings if f.notes and "SA-4" in f.notes]
    assert not sa4


def test_sa4_no_fire_no_usc(detector):
    findings = detector.detect(_ctx(_SA4_NO_FIRE_NO_USC), resolver=None)
    sa4 = [f for f in findings if f.notes and "SA-4" in f.notes]
    assert not sa4


# ---------------------------------------------------------------------------
# SA-5: CPRA-adjacent language with zero parsed statute citations
# ---------------------------------------------------------------------------

_SA5_FIRE = (
    "The department has reviewed your public records request and determined "
    "that the requested records are exempt from disclosure. The records are "
    "confidential and will be withheld. Further disclosure is not authorized."
)

_SA5_NO_FIRE_HAS_STATUTE = (
    "The department has reviewed your public records request. Pursuant to "
    "Government Code § 7923.600, peace officer personnel records are exempt "
    "from disclosure. The records are withheld under this exemption."
)

_SA5_NO_FIRE_ONLY_ONE_TERM = (
    "This contract is confidential and may not be shared with third parties "
    "without prior written consent."
)


def test_sa5_fires_on_cpra_adjacent_no_citations(detector):
    findings = detector.detect(_ctx(_SA5_FIRE), resolver=None)
    sa5 = [f for f in findings if f.notes and "SA-5" in f.notes]
    assert sa5, "SA-5 should fire on CPRA-adjacent language with no statute citations"
    assert sa5[0].severity == Severity.MEDIUM


def test_sa5_no_fire_has_statute(detector):
    findings = detector.detect(_ctx(_SA5_NO_FIRE_HAS_STATUTE), resolver=None)
    sa5 = [f for f in findings if f.notes and "SA-5" in f.notes]
    assert not sa5


def test_sa5_no_fire_only_one_term(detector):
    findings = detector.detect(_ctx(_SA5_NO_FIRE_ONLY_ONE_TERM), resolver=None)
    sa5 = [f for f in findings if f.notes and "SA-5" in f.notes]
    assert not sa5


# ---------------------------------------------------------------------------
# Structural / protocol tests
# ---------------------------------------------------------------------------


def test_detector_id():
    assert L9StatuteCitationAuditor.detector_id == "l9-statute-citation-auditor"


def test_returns_list_on_empty_text(detector):
    findings = detector.detect(_ctx(""), resolver=None)
    assert isinstance(findings, list)


def test_returns_empty_on_clean_civic_text(detector):
    clean = (
        "The Board of Supervisors approved the consent calendar. "
        "The minutes were accepted unanimously. No policy changes were adopted."
    )
    findings = detector.detect(_ctx(clean), resolver=None)
    assert findings == []


def test_finding_shape(detector):
    findings = detector.detect(_ctx(_SA1_FIRE_6254), resolver=None)
    for f in findings:
        d = f.to_anomaly_dict()
        assert d["layer"] == "legal"
        assert d["severity"] in ("low", "medium", "high", "critical")
        assert "sub_detector" in d["details"]
        assert d["details"]["sub_detector"] == "l9-statute-citation-auditor"


def test_exception_returns_empty_list(detector):
    ctx = _ctx("normal civic text")
    findings = detector.detect(ctx, resolver=object())
    assert isinstance(findings, list)


def test_multiple_rules_can_fire(detector):
    combined = (
        "The department denies the public records request under Government Code § 6254. "
        "Records are also withheld under Penal Code § 832.7 and § 832.8. "
        "The department is exempt from disclosure and will withhold all confidential records."
    )
    findings = detector.detect(_ctx(combined), resolver=None)
    codes = {f.notes.split(":")[0].strip() for f in findings if f.notes}
    assert len(codes) >= 2, "SA-1 and SA-3 should independently fire"
