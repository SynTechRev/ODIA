# scripts/phase16_example.py
import json
from pathlib import Path

from oraculus_di_auditor.emcs16.phase16_service import Phase16Service

FIXTURE_PATH = Path("tests/fixtures/phase12_13_14_15.json")
if not FIXTURE_PATH.exists():
    raise SystemExit("Please ensure tests/fixtures/phase12_13_14_15.json exists")

fixture = json.loads(FIXTURE_PATH.read_text())
svc = Phase16Service()
result = svc.run_cycle(fixture)
print("=== Phase16Result (summary) ===")
print("meta_state_vector keys:", list(result["meta_state_vector"].keys()))
print("recursive_integrity_score:", result["recursive_integrity_score"])
print("meta_harmonic_field:", result["meta_harmonic_field"])
print("provenance:", result["provenance"])
