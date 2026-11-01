# Day 09 -- Memory Architecture

**Date**: 2026-10-31
**Branch**: learning/10-day-challenge
**Operator**: M. Sanchez (SynTechRev)
**Status**: COMPLETE

---

## What Was Built

`src/oraculus_di_auditor/memory/three_tier.py` -- three-tier memory architecture
for the RAIA agent: working, episodic, and archival memory.

---

## B-11 Substitution: Letta / MemGPT Not Available

Letta and MemGPT both fail to import (no module found on Python 3.14). Following
the B-11 substitution pattern from earlier days: native implementation over SQLite +
stdlib replaces the framework dependency. The three-tier memory semantics (working /
episodic / archival) are preserved; only the framework layer is substituted.

Storage: `data/memory/odia_memory.db` (separate from oraculus_audit.db -- audit data
and agent memory are cleanly separated).

---

## Architecture

### Tier 1: WorkingMemory

Bounded in-process context store for the current RAIA query cycle. Implemented as
a `collections.deque` of typed `WorkingMemorySlot` objects with a max_tokens budget
(default 2048). Slot types: passage, finding, legal_finding, reflection.

Key method: `update_from_state(state)` syncs from a RAIA state dict after each node
(cross_reference, legal_scan, verify). The last 5 passages are pushed; all legal
findings and the verify reflection are pushed. Oldest slots are evicted when the
token budget is exceeded.

Working memory is cleared by `ThreeTierMemory.update_from_trace()` after a query cycle
completes, so each new query starts with a clean working context.

### Tier 2: EpisodicMemory

SQLite-backed store of completed RAIA traces. Schema: `episodes` table with
episode_id (SHA256 of query + timestamp), query, halt_reason, citation_density,
legal_findings_count, trace_json, final_answer.

B-7 Day 9 integration: `get_detector_hints(query)` retrieves the sub_detectors that
fired in similar verified episodes (halt_reason=verify_passed, density>=0.75) and
returns those that fired in at least half the recalled episodes. This is the selective
detector invocation mechanism the B-7 review asked for: the agent can call
`memory.compose(state)["memory_detector_hints"]` to get a prioritized detector list
before invoking the full DETECTOR_TOOLS.

Retrieval: BM25-style keyword overlap scoring against the episode query field.
No vector index at this stage -- the keyword match is sufficient for the 50-500
episode range expected in production.

### Tier 3: ArchivalMemory

SQLite-backed structured knowledge store. Schema: `archival_entries` table with
source, key, summary, content_json. Sources: `jag_subgraph`, `legal_finding`,
`corpus_pattern`.

`bootstrap_from_graph(graph_json_path)` loads the Day 8 JAG subgraph JSON (50 nodes)
into the archival store. Each node becomes an entry with the node's label, title,
and adjacency list in content_json. `graph_neighbors(node_id)` returns adjacent
nodes from an in-memory index built during bootstrap.

Retrieval: keyword overlap against the summary field. The summary for JAG subgraph
nodes is `{label} [{node_type}] {title[:200]}` -- captures jurisdiction names,
statute numbers, and vendor names for keyword matching.

### Facade: ThreeTierMemory

Unified interface:
- `bootstrap(graph_json_path, traces_path)`: initialize from Day 8 + Day 4 artifacts
- `compose(state) -> dict`: inject memory context into RAIA state before deepen_node
  (adds memory_episodic_context, memory_archival_context, memory_detector_hints,
  memory_working_context)
- `update_from_trace(state) -> str`: persist completed trace to episodic memory,
  clear working memory
- `stats() -> dict`: current counts across all tiers
- `close()`: explicit connection cleanup (important on Windows for file handles)

---

## B-7 Day 9 Integration

Two open items from the B-7 review are addressed:

**Detector invocation strategy (selective vs. all-10):**
`get_detector_hints()` is the mechanism. After `compose()`, the RAIA agent checks
`state["memory_detector_hints"]` for a list of sub_detectors that fired in similar
past verified episodes. On Day 11/production wiring (raia_v0.py update), the
`legal_scan_node` can be passed a `detector_filter` parameter that restricts
invocation to the hinted sub_detectors. If hints are empty (new query type with no
episodic precedent), fall back to all-10.

**Finding reconciliation:**
When `state["memory_archival_context"]` contains JAG subgraph entries that overlap
with the current query, the deepen_node synthesis can be grounded in archival
knowledge rather than re-deriving it from retrieved passages. The memory context
block is injected into the deepen prompt by the caller (Day 10 wiring). Archival
entries marked with severity fields from prior legal_scan runs would provide the
reconciliation signal; storing legal_findings from completed runs to archival memory
is the next step (currently stored in episodic trace_json but not in archival_entries
directly).

---

## Build Results (2026-10-31)

| Artifact | Status | Notes |
|---|---|---|
| `src/oraculus_di_auditor/memory/__init__.py` | UPDATED | Exports all four classes |
| `src/oraculus_di_auditor/memory/three_tier.py` | COMPLETE | WorkingMemory + EpisodicMemory + ArchivalMemory + ThreeTierMemory |

Smoke test results:

| Test | Result |
|---|---|
| WorkingMemory slot/token management | PASS (2 slots, legal context correct) |
| Bootstrap from JAG subgraph JSON (50 nodes) | PASS |
| Bootstrap from Day 4 traces (5 episodes) | PASS |
| compose(): 4 memory keys injected | PASS |
| compose(): archival context contains JAG subgraph nodes | PASS |
| update_from_trace(): ep_id returned, count 5 -> 6 | PASS |
| episodic retrieve (verified_only=True) | PASS |
| close() + file cleanup (Windows file handle) | PASS |
| verify_no_dashes.sh | PASS |

---

## Status

Day 9 COMPLETE. No blockers. Day 10 proceeds.

Open items passed to Day 10:
- Wire memory.compose() into raia_v0.py deepen_node prompt (optional, Day 10 scope)
- Store legal_findings to archival_entries after each RAIA cycle (currently only in
  episodic trace_json)
- Forward mode DPO smoke test: still deferred to Vast.ai Day 11
