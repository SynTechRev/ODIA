# tests/test_phase16_service.py
import json
from pathlib import Path

from oraculus_di_auditor.emcs16.phase16_service import Phase16Service


def _load_fixture():
    """Load fixture data to avoid shared mutable state between tests."""
    return json.loads(Path("tests/fixtures/phase12_13_14_15.json").read_text())


def test_phase16_run_basic():
    fixture = _load_fixture()
    svc = Phase16Service()
    out = svc.run_cycle(fixture)
    assert "meta_state_vector" in out
    assert "meta_harmonic_field" in out
    assert out["provenance"]["service_version"].startswith("emcs16")
    # basic sanity values
    assert isinstance(out["recursive_integrity_score"], float)


def test_phase16_determinism():
    fixture = _load_fixture()
    svc = Phase16Service()
    r1 = svc.run_cycle(fixture)
    r2 = svc.run_cycle(fixture)
    # Compare all fields except timestamps which are always different
    for key in r1.keys():
        if key != "timestamp":
            if key == "provenance":
                # Compare provenance without timestamp
                for prov_key in r1["provenance"].keys():
                    if prov_key != "timestamp":
                        assert r1["provenance"][prov_key] == r2["provenance"][prov_key]
            else:
                assert r1[key] == r2[key], f"Mismatch in {key}"
