# tests/test_self_modeling.py
from oraculus_di_auditor.emcs16.self_modeling import RecursiveSelfModeling


def test_build_and_project_returns_meta_and_projection():
    rsm = RecursiveSelfModeling(time_depth=3)
    ss = {"components": {"a": {}, "b": {}}}
    # Generate a valid hex hash for deterministic seeding
    import hashlib

    h = hashlib.sha256()
    h.update(b"test_data")
    input_hash = h.hexdigest()
    out = rsm.build_and_project(ss, input_hash)
    assert "meta_state" in out
    assert "projection" in out
    assert isinstance(out["seed"], int)
    assert len(out["projection"]["projections"]) == 3
