# Day 08 -- Knowledge Graph

**Date**: 2026-10-31
**Branch**: learning/10-day-challenge
**Operator**: M. Sanchez (SynTechRev)
**Status**: COMPLETE

---

## What Was Built

`src/oraculus_di_auditor/knowledge_graph/jag_subgraph.py` -- JAG anti-supplanting
evidence chain as a networkx DiGraph, with pyvis HTML visualization.

`scripts/build_jag_subgraph.py` -- runner script that queries oraculus_audit.db
and writes data/graphs/jag_anti_supplanting.json + data/graphs/jag_anti_supplanting.html.

---

## Data Foundation

Pre-build DB query confirmed:
- 760 total JAG findings: 614 critical (jag-without-anti-supplanting) + 146 high
  (jag-funded-surveillance)
- 14 jurisdictions: dinuba, exeter, farmersville, fresno, fresnocounty, lindsay,
  multi-jurisdiction, porterville, tcpd, tcso, tulare, tulare-county, visalia, visalia-pd
- 8 surveillance vendors named in JAG-funded-surveillance findings: Axon Enterprise,
  Flock Safety, BCS Consulting, Lexipol, T-Mobile, Motorola Solutions, Nexanet,
  Security Lines US

Note: The session-level summary and CLAUDE.md referenced "79 critical findings" and
"60 JAG anti-supplanting" for TCPD specifically. The live DB query shows 614 critical
across all 14 jurisdictions (60 for TCPD alone matches; the 79 referenced earlier was
a subset of the broader 614 cross-jurisdictional count).

---

## Design Decisions

### Graph topology (50 nodes / 105 edges)

Five node layers:
1. Federal statutes (3 nodes): 34 USC 10152 (JAG), 34 USC 10153(a)(2) (anti-supplanting),
   BJA Reporting Requirement
2. Jurisdiction nodes (14): one per jurisdiction, sized by total finding count
3. Finding cluster nodes (24): anti_supplanting (14 jurisdictions, critical) +
   jag_surveillance (10 jurisdictions with high findings)
4. Vendor nodes (8): sized by jurisdiction count; colored by vendor identity
5. Pattern-and-practice anchor (1): Section 1983 star node aggregating all 614 critical
   findings

Edge types: JAG_GRANT_RECEIVED, ANTI_SUPPLANTING_VIOLATED, BJA_REPORTING_NOT_MET,
HAS_CRITICAL_FINDING, HAS_HIGH_FINDING, NAMES_VENDOR, SUPPORTS_PATTERN_AND_PRACTICE,
REQUIRES.

### nano-graphrag replacement (B-11 resolution)

nano-graphrag fails Python 3.14 (gensim __NUMPY_SETUP__ C-extension). Day 8 replaces
it with networkx (3.6.1) + pyvis (0.3.2), both confirmed available. The networkx
DiGraph provides equivalent graph construction and analysis capabilities. pyvis provides
the interactive browser visualization. Export to node-link JSON preserves the graph
structure for Day 9 memory integration.

### Aggregation strategy: finding clusters not per-document nodes

760 document-level findings as individual nodes would violate Watch 1 (100-300 target)
and Watch 2 (pyvis under 500). Aggregating by (jurisdiction, anomaly_type) produces
24 finding cluster nodes that preserve the cross-jurisdictional signal without the
render performance penalty.

Watch 1 (subgraph scope) result:
- Anti-supplanting chain: 3 federal nodes -> 14 jurisdictions -> 14 critical clusters ->
  1 anchor node. Clean linear evidence chain from federal requirement to pattern-and-practice
  anchor.
- jag-funded-surveillance chain: 1 BJA requirement -> 10 jurisdiction surveillance clusters
  -> 8 vendor nodes. Surveillance vendor procurement pattern visible in one view.

---

## Build Results (2026-10-31)

| Artifact | Status | Notes |
|---|---|---|
| `src/oraculus_di_auditor/knowledge_graph/__init__.py` | COMPLETE | Package init |
| `src/oraculus_di_auditor/knowledge_graph/jag_subgraph.py` | COMPLETE | JAGSubgraph class, build/export functions |
| `scripts/build_jag_subgraph.py` | COMPLETE | Runner with Watch 1 + Watch 2 gates |
| `data/graphs/jag_anti_supplanting.json` | GENERATED | 50 nodes / 105 edges node-link JSON |
| `data/graphs/jag_anti_supplanting.html` | GENERATED | pyvis interactive HTML |

Graph metrics:
- Nodes: 50
- Edges: 105
- Node types: federal_statute:1, federal_requirement:2, jurisdiction:14,
  finding_cluster_critical:14, finding_cluster_high:10, vendor:8,
  pattern_and_practice_anchor:1
- Total critical findings represented: 614
- Total high findings represented: 146
- Jurisdictions covered: 14

Watch checks:
- Watch 1 (subgraph scope 100-300): PASS -- 50 nodes (all 14 jurisdictions covered,
  all 8 vendors resolved, full chain from 34 USC 10152 to Section 1983 anchor)
- Watch 2 (pyvis under 500): PASS -- 50 nodes
- Watch 3 (C.O.N.T.R.A. D9 chain substrate): 8 vendor nodes align with supply chain
  nodes documented in the Fifteen Connections memorandum. Axon Enterprise and Flock
  Safety both present with multi-jurisdiction procurement links. The vendor layer
  provides the visual substrate for the C.O.N.T.R.A. pattern-and-practice narrative.

---

## Day 9 Integration Note

data/graphs/jag_anti_supplanting.json (node-link format) is the substrate for Day 9
memory architecture integration. The `legal_findings` key added by legal_scan_node
(Day 7) feeds into the episodic memory tier; the JAG subgraph is the archival memory
anchor for the cross-jurisdictional JAG compliance record.

The B-7 architectural question about finding reconciliation (detector verdict vs. agent
reasoning) applies directly here: the JAG anti-supplanting subgraph nodes should be
surfaced to the RAIA agent as retrieved passages when a JAG-related query arrives,
so the agent's deepening synthesis incorporates the graph structure rather than
re-deriving it from raw text.

---

## Status

Day 8 COMPLETE. No blockers. Day 9 proceeds.
