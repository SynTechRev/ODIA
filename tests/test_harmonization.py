# tests/test_harmonization.py
from oraculus_di_auditor.emcs16.harmonization import HarmonizationCore


def test_fuse_and_patterns():
    hc = HarmonizationCore()
    harmonics = {0: 1.0}
    probs = {"a": 0.9, "b": 0.1}
    cri = {"a": 0.8, "b": 0.2}
    meta = hc.fuse(harmonics, probs, cri)
    assert "a" in meta
    pats = hc.emergent_patterns(meta)
    assert isinstance(pats, dict)
