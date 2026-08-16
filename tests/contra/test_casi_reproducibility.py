"""CASI reproducibility: 3-run determinism across the golden corpus (V2.0-A-3).

For each golden fixture (g01-g05) the full C.O.N.T.R.A. L-11..L-20 detector
pipeline plus compute_casi() must yield bit-identical CasiAxes on every
independent run.  This guards against:

  - Non-deterministic state in any detector (random calls, mutable module-level
    accumulators, timestamp-dependent branching, set-iteration order).
  - compute_casi() regressions that introduce non-determinism at the scoring
    layer.

Each parametrised case runs three back-to-back passes and asserts equality
across all three.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

GOLDEN_DIR = Path(__file__).parent / "golden"
GOLDEN_FILES = sorted(GOLDEN_DIR.glob("g*.txt"))

if not GOLDEN_FILES:
    pytest.skip("No golden fixtures found in tests/contra/golden/", allow_module_level=True)

_DOC_META: dict[str, Any] = {
    "entity_id": "test-entity-repro",
    "entity_name": "Test Entity",
    "doc_type": "tos",
    "effective_date": None,
    "document_hash": "0" * 64,
    "source_url": None,
}


def _score_once(doc_text: str) -> dict:
    from oraculus_di_auditor.ingest.commercial import _run_contra_detectors
    from oraculus_di_auditor.scoring.casi import compute_casi

    findings = _run_contra_detectors(doc_text, dict(_DOC_META))
    axes = compute_casi(findings)
    return axes.to_dict()


@pytest.mark.parametrize("golden_path", GOLDEN_FILES, ids=lambda p: p.stem)
def test_casi_deterministic_three_runs(golden_path: Path) -> None:
    """CasiAxes must be bit-identical across 3 independent runs on the same input."""
    doc_text = golden_path.read_text(encoding="utf-8")

    run1 = _score_once(doc_text)
    run2 = _score_once(doc_text)
    run3 = _score_once(doc_text)

    assert run1 == run2, (
        f"{golden_path.name}: run 1 != run 2\n  run1={run1}\n  run2={run2}"
    )
    assert run2 == run3, (
        f"{golden_path.name}: run 2 != run 3\n  run2={run2}\n  run3={run3}"
    )


@pytest.mark.parametrize("golden_path", GOLDEN_FILES, ids=lambda p: p.stem)
def test_casi_aggregate_within_bounds(golden_path: Path) -> None:
    """Aggregate score must remain in [0, 100] for all golden fixtures."""
    doc_text = golden_path.read_text(encoding="utf-8")
    result = _score_once(doc_text)
    agg = result["aggregate"]
    assert 0 <= agg <= 100, (
        f"{golden_path.name}: aggregate {agg} out of [0, 100]"
    )


@pytest.mark.parametrize("golden_path", GOLDEN_FILES, ids=lambda p: p.stem)
def test_casi_axes_within_bounds(golden_path: Path) -> None:
    """Each individual axis score must be in [0, 20]."""
    doc_text = golden_path.read_text(encoding="utf-8")
    result = _score_once(doc_text)
    axes = (
        "remedy_foreclosure",
        "data_extraction_depth",
        "modification_and_consent",
        "procedural_adhesion",
        "enforcement_cost_asymmetry",
    )
    for axis in axes:
        val = result[axis]
        assert 0 <= val <= 20, (
            f"{golden_path.name}: axis '{axis}'={val} out of [0, 20]"
        )


@pytest.mark.parametrize("golden_path", GOLDEN_FILES, ids=lambda p: p.stem)
def test_casi_band_is_valid_string(golden_path: Path) -> None:
    """Band label must be one of the five defined CASI bands."""
    valid_bands = {
        "Baseline Adhesion",
        "Elevated Asymmetry",
        "Substantial Asymmetry",
        "Severe Asymmetry",
        "Foreclosure Regime",
    }
    doc_text = golden_path.read_text(encoding="utf-8")
    result = _score_once(doc_text)
    assert result["band"] in valid_bands, (
        f"{golden_path.name}: unexpected band '{result['band']}'"
    )
