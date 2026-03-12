# tests/test_meta_supervisor.py
from oraculus_di_auditor.emcs16.meta_supervisor import MetaSupervisor


def test_supervisor_detects_coherence_issue():
    sup = MetaSupervisor(coherence_threshold=0.01)
    req = {
        "system_state": {},
        "phase12_harmonics": {0: 1.0},
        "phase13_probabilities": {"x": 0.0},
        "phase14_outputs": {"cri_rankings": {"x": 0.0}},
    }
    report = sup.run_checks(req)
    assert "issues" in report
    assert report["integrity_score"] <= 1.0
