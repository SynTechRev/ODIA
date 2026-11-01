# Day 07 -- Neurosymbolic Integration

**Date**: 2026-10-31
**Branch**: learning/10-day-challenge
**Operator**: M. Sanchez (SynTechRev)
**Status**: COMPLETE -- B-7 checkpoint open (Mars sign-off required before Day 9)

---

## What Was Built

`src/oraculus_di_auditor/tools/detector_tools.py`

Wraps all 10 L-detectors (L-1 through L-10) as callable LangGraph tools and provides
a batch runner node for RAIA agent integration.

---

## Architecture Survey (Pre-Build)

Before writing a line of code, read:
- `agents/raia_v0.py` (full): five nodes (analyze, cross_reference, deepen, verify, finalize),
  StateGraph cycle, no tool-calling capability.
- `legal/detectors/_base.py`: DocContext, LegalFinding, Severity, LegalDetector Protocol.
- `legal/detectors/l1_statutory_applicability.py`: concrete implement of detect() pattern.
- `legal/legal_resolver.py`: LegalResolver class (loads legal corpora at startup).

Key interface contracts:
- `LegalDetector.detect(ctx: DocContext, resolver: LegalResolver) -> list[LegalFinding]`
- `LegalFinding.to_anomaly_dict()` serializes to ODIA anomaly dict shape
- `DocContext.text` is the full document text; all detectors do static pattern analysis only
- L-1 uses `resolver: object` to avoid circular import -- all others likely similar

Decision from survey: Day 7 establishes the tool pattern without modifying raia_v0.py.
Graph wiring (adding legal_scan_node between cross_reference and deepen) is deferred to
Day 9 after B-7 sign-off.

---

## Design Decisions

### 1. @tool decorator pattern

LangGraph tools must be `@tool`-decorated callables with serializable inputs.
The DocContext dataclass has many fields including a long `text` field -- passing it as
a single `doc_context_json: str` is cleaner than multi-argument signatures and aligns
with the ToolNode calling convention.

Output is also JSON (`findings_json: str`) so the tool return is LLM-readable and
ToolNode-passable without further deserialization at the node boundary.

`@tool(description=...)` is used instead of inline docstrings because the description
constant `_TOOL_DESCRIPTION_SUFFIX` is shared across all 10 wrappers and Python only
assigns `__doc__` to string literals, not expressions.

### 2. _NullResolver sentinel

`LegalResolver.initialize()` loads YAML corpora at backend startup. At tool-call time
(from the RAIA agent), the resolver may not be initialized. The `_NullResolver` sentinel
allows all 10 detectors to run in static-analysis mode (pattern matching, heuristics)
without corpus lookups. Detectors that call resolver methods would raise AttributeError --
none of L-1 through L-10 do so in practice (they use resolver: object annotations for
exactly this reason).

### 3. DetectorRegistry vs. per-tool instances

Each `@tool` wrapper calls `DetectorCls()` to create a fresh instance per call.
Detector classes are stateless (no instance variables written during detect()), so
this is safe. `DetectorRegistry` holds singleton instances for `legal_scan_node` batch
runs where instantiation cost would accumulate across 10+ passages.

### 4. legal_scan_node state contract

`legal_scan_node(state: dict, resolver=None) -> dict` takes and returns a plain dict
(not RAIAState TypedDict) so it is compatible with RAIAState and any future superset.
The node:
- Reads `state["retrieved_passages"]` (populated by cross_reference_node)
- Writes `state["legal_findings"]` (list of anomaly dicts, one per LegalFinding)
- Appends a trace entry `{"node": "legal_scan", "passages_scanned": N, "findings_produced": M}`
- Skips passages with no `document_id`

Proposed Day 9 wiring (pending B-7 sign-off):
```python
builder.add_node("legal_scan", lambda s: legal_scan_node(s))
builder.add_edge("cross_reference", "legal_scan")
builder.add_edge("legal_scan", "deepen")
```

Position between cross_reference and deepen means the legal scan runs on every RAIA
iteration before the LLM deepening step -- findings are available to deepen_node via
state["legal_findings"] for statute-level grounding.

---

## Build Results (2026-10-31)

| Artifact | Status | Notes |
|---|---|---|
| `src/oraculus_di_auditor/tools/detector_tools.py` | COMPLETE | 10 @tool wrappers + DetectorRegistry + legal_scan_node |
| `src/oraculus_di_auditor/tools/__init__.py` | UPDATED | Exports DETECTOR_TOOLS, DetectorRegistry, build_doc_context_from_passage, legal_scan_node |

Smoke test results:

| Test | Result |
|---|---|
| Import + tool count | PASS (10 tools) |
| Tool names | PASS (run_l1_statutory_applicability ... run_l10_balancing_test) |
| build_doc_context_from_passage (ALPR agenda doc) | PASS (document_id=abc123, version_date=2024-01-15) |
| DetectorRegistry.run_all on ALPR/surveillance doc | PASS (3 findings: L-1/low, L-8/high, L-10/high) |
| legal_scan_node (1 passage) | PASS (3 findings, trace entry correct) |
| @tool.invoke JSON path (L-1) | PASS (1 finding returned as JSON array) |
| verify_no_dashes.sh | PASS (0 em-dashes, 0 en-dashes) |

Detector trigger analysis on test doc ("ALPR license plate reader surveillance policy"):
- L-1 (Statutory Applicability): FIRED -- Tier 3 ALPR signal + agenda doc_type. LOW severity, 3 statutes.
- L-8 (Case Law Currency): FIRED -- date-dependent analysis. HIGH severity.
- L-10 (Balancing Test): FIRED -- surveillance context triggers balancing test check. HIGH severity.
- L-2 through L-7, L-9: Did not fire on minimal test text (correct -- no procedural/exemption/grant signals present).

---

## B-7 Checkpoint: Mars Review Items

Three decisions are open for sign-off before Day 9 starts:

**Item 1: _NullResolver pattern**
Current: legal_scan_node passes _NullResolver() when no resolver provided.
Question: Acceptable for Day 9 production wiring, or should legal_scan_node require
a live LegalResolver injected via partial() or a registry?

**Item 2: Graph wiring position**
Current proposal: legal_scan between cross_reference and deepen (runs on every iteration).
Alternative: legal_scan as a post-finalize enrichment step (runs once, on the final answer).
Tradeoff: Between-node placement makes legal findings available to the LLM for statute
grounding; post-finalize placement reduces VRAM pressure on long iteration chains.

**Item 3: RAIAState TypedDict extension**
legal_findings is added to state dynamically (not declared in RAIAState TypedDict).
Options: (a) extend RAIAState with legal_findings: list[dict] field, (b) leave as dynamic
addition (acceptable for LangGraph -- StateGraph tolerates extra keys), (c) create
RAIALegalState as a separate TypedDict subclass.

---

## Status

B-7 checkpoint open. Mars sign-off required before Day 9.
Day 8 (Knowledge Graph) proceeds independently -- no dependency on B-7.
