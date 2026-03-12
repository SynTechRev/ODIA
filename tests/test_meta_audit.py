# tests/test_meta_audit.py
from oraculus_di_auditor.emcs16.meta_audit import MetaAudit


def test_generate_report_empty_recs():
    ma = MetaAudit()
    sup_report = {"recommended_actions": [], "integrity_score": 0.9, "issues": []}
    harmonics = {"a": 0.9}
    report = ma.generate_report(sup_report, harmonics)
    assert "summary" in report
    assert "actions" in report
