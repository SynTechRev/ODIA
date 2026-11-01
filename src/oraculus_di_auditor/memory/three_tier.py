"""Day 9: Three-Tier Memory Architecture for the RAIA agent.

Implements working, episodic, and archival memory without Letta/MemGPT
(both unavailable on Python 3.14 -- B-11 substitution pattern).

Architecture:
  WorkingMemory   -- bounded in-process context for the current RAIA session
  EpisodicMemory  -- persistent SQLite store of past RAIA traces
  ArchivalMemory  -- persistent SQLite store of structured knowledge (JAG subgraph,
                     legal findings, corpus patterns)
  ThreeTierMemory -- unified facade; composes and updates all three tiers

Storage: data/memory/odia_memory.db (separate from oraculus_audit.db to keep
audit data and agent memory cleanly separated).

B-7 Day 9 integration points:
  - Episodic recall informs detector selection: episodes with high citation density
    record which detectors fired, allowing selective rather than all-10 invocation.
  - Finding reconciliation: archived legal findings mark verified/discounted verdicts;
    new detector output is cross-checked before entering the deepen prompt.

Day 8 integration:
  ArchivalMemory.bootstrap_from_graph() loads the JAG subgraph JSON produced by
  build_jag_subgraph.py into the archival store as structured knowledge entries.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_MEMORY_DB = Path("data/memory/odia_memory.db")

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS episodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id      TEXT UNIQUE NOT NULL,
    query           TEXT NOT NULL,
    halt_reason     TEXT,
    citation_density REAL DEFAULT 0.0,
    legal_findings_count INTEGER DEFAULT 0,
    trace_json      TEXT,
    final_answer    TEXT,
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_episodes_halt ON episodes (halt_reason);
CREATE INDEX IF NOT EXISTS idx_episodes_created ON episodes (created_at);

CREATE TABLE IF NOT EXISTS archival_entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id    TEXT UNIQUE NOT NULL,
    source      TEXT NOT NULL,
    key         TEXT NOT NULL,
    summary     TEXT NOT NULL,
    content_json TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_archival_source ON archival_entries (source);
CREATE INDEX IF NOT EXISTS idx_archival_key ON archival_entries (key);
"""


def _open_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_DDL)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Retrieval: BM25-style keyword overlap
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\b[a-zA-Z0-9]{2,}\b")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _score_overlap(query_tokens: list[str], candidate: str) -> float:
    """Simple TF overlap score between query tokens and candidate text."""
    cand_tokens = set(_tokenize(candidate))
    if not cand_tokens:
        return 0.0
    hits = sum(1 for t in query_tokens if t in cand_tokens)
    return (
        hits / len(cand_tokens) * min(1.0, len(query_tokens) / max(1, len(cand_tokens)))
    )


# ---------------------------------------------------------------------------
# Tier 1: Working Memory
# ---------------------------------------------------------------------------


@dataclass
class WorkingMemorySlot:
    slot_type: str  # "passage" | "finding" | "reflection" | "legal_finding"
    content: str
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)


class WorkingMemory:
    """Bounded in-process memory for the current RAIA session.

    Stores the most recent context slots (passages, findings, reflections) that
    the RAIA agent has processed in the current query cycle. Bounded by token
    budget so the context injected into deepen_node never exceeds the LLM window.

    Slot types map to RAIA node outputs:
      passage       -- retrieved passage from cross_reference_node
      finding       -- deepened_findings from deepen_node
      legal_finding -- legal finding from legal_scan_node (Day 7)
      reflection    -- verify_node reflection (failed citation check)
    """

    def __init__(self, max_tokens: int = 2048) -> None:
        self.max_tokens = max_tokens
        self._slots: deque[WorkingMemorySlot] = deque()
        self._token_count = 0

    def push(self, slot: WorkingMemorySlot) -> None:
        tokens = len(slot.content.split())
        while self._token_count + tokens > self.max_tokens and self._slots:
            evicted = self._slots.popleft()
            self._token_count -= len(evicted.content.split())
        self._slots.append(slot)
        self._token_count += tokens

    def clear(self) -> None:
        self._slots.clear()
        self._token_count = 0

    def get_context_block(self, slot_types: list[str] | None = None) -> str:
        """Return formatted context block for injection into deepen prompt."""
        selected = [
            s for s in self._slots if slot_types is None or s.slot_type in slot_types
        ]
        if not selected:
            return ""
        lines = ["WORKING MEMORY CONTEXT:"]
        for s in selected:
            lines.append(f"[{s.slot_type.upper()}] {s.content[:400]}")
        return "\n".join(lines)

    def get_legal_context(self) -> str:
        """Formatted block of legal findings for deepen prompt injection."""
        return self.get_context_block(slot_types=["legal_finding"])

    def update_from_state(self, state: dict) -> None:
        """Sync working memory from a RAIA state dict after a node completes."""
        # Ingest retrieved passages
        for passage in state.get("retrieved_passages", [])[-5:]:
            doc_id = passage.get("document_id", "")
            title = passage.get("title", doc_id[:40])
            issues = [
                f.get("issue", "")
                for f in passage.get("findings", [])[:2]
                if f.get("issue")
            ]
            content = f"[doc_id:{doc_id}] {title}"
            if issues:
                content += ": " + "; ".join(issues[:2])
            self.push(
                WorkingMemorySlot(
                    slot_type="passage",
                    content=content,
                    metadata={"document_id": doc_id},
                )
            )

        # Ingest legal findings
        for lf in state.get("legal_findings", []):
            content = f"{lf.get('details', {}).get('sub_detector', 'L-?')} [{lf.get('severity', '?')}]: {lf.get('issue', '')}"
            self.push(
                WorkingMemorySlot(slot_type="legal_finding", content=content[:300])
            )

        # Ingest reflection
        if state.get("reflection"):
            self.push(
                WorkingMemorySlot(slot_type="reflection", content=state["reflection"])
            )

    @property
    def token_count(self) -> int:
        return self._token_count

    @property
    def slot_count(self) -> int:
        return len(self._slots)


# ---------------------------------------------------------------------------
# Tier 2: Episodic Memory
# ---------------------------------------------------------------------------


class EpisodicMemory:
    """Persistent store of past RAIA traces backed by SQLite.

    Each episode is a complete RAIA trace (query + final_answer + halt_reason +
    citation_density + legal_findings_count + full trace_json). Episodes are
    retrieved by keyword overlap against the query field.

    B-7 integration: high-citation-density episodes (halt_reason=verify_passed)
    are prioritized in recall. The `detectors_fired` in legal_findings_count
    informs detector selection for new queries -- if similar past queries only
    needed L-1 and L-8, the agent can skip the other 8.
    """

    def __init__(self, db_path: Path = _DEFAULT_MEMORY_DB) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _open_db(self._db_path)
        return self._conn

    def store_trace(self, state: dict) -> str:
        """Persist a completed RAIA state as an episode. Returns episode_id."""
        query = state.get("query", "")
        now = datetime.now(UTC).isoformat()
        ep_id = hashlib.sha256(f"{query}:{now}".encode()).hexdigest()[:24]

        citation_density = float(state.get("confidence", 0.0))
        legal_findings_count = len(state.get("legal_findings", []))

        trace_json = json.dumps(state.get("trace", []))
        final_answer = state.get("final_answer", "")[:2000]

        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR IGNORE INTO episodes
              (episode_id, query, halt_reason, citation_density,
               legal_findings_count, trace_json, final_answer, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ep_id,
                query,
                state.get("halt_reason", ""),
                citation_density,
                legal_findings_count,
                trace_json,
                final_answer,
                now,
            ),
        )
        conn.commit()
        logger.debug(
            "Stored episode %s (halt=%s, density=%.2f)",
            ep_id,
            state.get("halt_reason"),
            citation_density,
        )
        return ep_id

    def retrieve(
        self,
        query: str,
        k: int = 5,
        min_citation_density: float = 0.0,
        verified_only: bool = False,
    ) -> list[dict]:
        """Retrieve past episodes most similar to query.

        Scores by keyword overlap against the episode's query field.
        verified_only=True restricts to halt_reason=verify_passed episodes
        (high-quality DPO training signal; useful for detector selection hints).
        """
        conn = self._get_conn()
        sql = "SELECT * FROM episodes WHERE 1=1"
        params: list[Any] = []
        if verified_only:
            sql += " AND halt_reason = 'verify_passed'"
        if min_citation_density > 0:
            sql += " AND citation_density >= ?"
            params.append(min_citation_density)
        sql += " ORDER BY created_at DESC LIMIT 200"

        rows = conn.execute(sql, params).fetchall()
        query_tokens = _tokenize(query)
        scored = []
        for row in rows:
            score = _score_overlap(query_tokens, row["query"])
            scored.append((score, dict(row)))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:k]]

    def get_detector_hints(self, query: str, k: int = 5) -> list[str]:
        """Return list of sub_detector ids that fired in similar verified episodes.

        Used for B-7 detector selection: invoke selectively based on episodic recall
        rather than running all 10 detectors blindly on every passage.
        """
        episodes = self.retrieve(
            query, k=k, verified_only=True, min_citation_density=0.75
        )
        detector_counts: dict[str, int] = {}
        for ep in episodes:
            for trace_entry in json.loads(ep.get("trace_json") or "[]"):
                for lf in trace_entry.get("legal_findings", []):
                    sub_det = lf.get("details", {}).get("sub_detector", "")
                    if sub_det:
                        detector_counts[sub_det] = detector_counts.get(sub_det, 0) + 1
        # Return detectors that fired in at least half the retrieved episodes
        threshold = max(1, len(episodes) // 2)
        return [
            d
            for d, c in sorted(
                detector_counts.items(), key=lambda x: x[1], reverse=True
            )
            if c >= threshold
        ]

    def bulk_load_from_traces_file(self, traces_path: Path) -> int:
        """Load all traces from a JSONL file (e.g. data/eval/raia_day04_traces.jsonl)."""
        if not traces_path.exists():
            logger.warning("Traces file not found: %s", traces_path)
            return 0
        loaded = 0
        for line in traces_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                trace = json.loads(line)
                self.store_trace(trace)
                loaded += 1
            except (json.JSONDecodeError, Exception):
                logger.debug("Skipping malformed trace line")
        return loaded

    def count(self) -> int:
        return self._get_conn().execute("SELECT COUNT(*) FROM episodes").fetchone()[0]

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


# ---------------------------------------------------------------------------
# Tier 3: Archival Memory
# ---------------------------------------------------------------------------


class ArchivalMemory:
    """Persistent structured knowledge store backed by SQLite.

    Entries come from:
      - JAG subgraph nodes (source='jag_subgraph')
      - Legal findings from RAIA runs (source='legal_finding')
      - Corpus pattern summaries (source='corpus_pattern')

    Retrieved by keyword overlap against the summary field.
    graph_neighbors() traverses the JAG subgraph in-memory to return connected nodes.
    """

    def __init__(self, db_path: Path = _DEFAULT_MEMORY_DB) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._graph_index: dict[str, dict] = {}

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _open_db(self._db_path)
        return self._conn

    def _entry_id(self, source: str, key: str) -> str:
        return hashlib.sha256(f"{source}:{key}".encode()).hexdigest()[:24]

    def store(
        self,
        source: str,
        key: str,
        summary: str,
        content: dict,
    ) -> str:
        entry_id = self._entry_id(source, key)
        now = datetime.now(UTC).isoformat()
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO archival_entries
              (entry_id, source, key, summary, content_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (entry_id, source, key, summary, json.dumps(content), now),
        )
        conn.commit()
        return entry_id

    def retrieve(
        self,
        query: str,
        k: int = 10,
        source_filter: str | None = None,
    ) -> list[dict]:
        """Retrieve archival entries by keyword overlap against summary."""
        conn = self._get_conn()
        sql = "SELECT * FROM archival_entries"
        params: list[Any] = []
        if source_filter:
            sql += " WHERE source = ?"
            params.append(source_filter)
        sql += " ORDER BY created_at DESC LIMIT 500"

        rows = conn.execute(sql, params).fetchall()
        query_tokens = _tokenize(query)
        scored = []
        for row in rows:
            score = _score_overlap(query_tokens, row["summary"])
            if score > 0:
                scored.append((score, dict(row)))
        scored.sort(key=lambda x: x[0], reverse=True)
        result = []
        for _, entry in scored[:k]:
            try:
                entry["content"] = json.loads(entry["content_json"])
            except (json.JSONDecodeError, KeyError):
                entry["content"] = {}
            result.append(entry)
        return result

    def bootstrap_from_graph(self, graph_json_path: Path) -> int:
        """Load JAG subgraph JSON into archival store. Returns entries written."""
        if not graph_json_path.exists():
            logger.warning("Graph JSON not found: %s", graph_json_path)
            return 0

        with graph_json_path.open(encoding="utf-8") as fh:
            export = json.load(fh)

        graph_data = export.get("graph", {})
        nodes = graph_data.get("nodes", [])
        links = graph_data.get("links", [])

        # Build an in-memory adjacency index for graph_neighbors()
        adjacency: dict[str, list[str]] = {}
        for link in links:
            src = str(link.get("source", ""))
            dst = str(link.get("target", ""))
            adjacency.setdefault(src, []).append(dst)
        self._graph_index = {n["id"]: n for n in nodes}

        written = 0
        for node in nodes:
            node_id = str(node.get("id", ""))
            node_type = node.get("node_type", "unknown")
            label = node.get("label", node_id).replace("\n", " ")
            title = node.get("title", label).replace("\n", " ")
            neighbors = adjacency.get(node_id, [])
            summary = f"{label} [{node_type}] {title[:200]}"

            self.store(
                source="jag_subgraph",
                key=node_id,
                summary=summary,
                content={
                    "node_id": node_id,
                    "node_type": node_type,
                    "label": label,
                    "title": title,
                    "color": node.get("color", ""),
                    "neighbors": neighbors,
                    "attributes": {
                        k: v
                        for k, v in node.items()
                        if k
                        not in (
                            "id",
                            "node_type",
                            "label",
                            "title",
                            "color",
                            "shape",
                            "size",
                        )
                    },
                },
            )
            written += 1

        logger.info("Bootstrapped %d JAG subgraph nodes into archival memory", written)
        return written

    def graph_neighbors(self, node_id: str) -> list[dict]:
        """Return archival entries for nodes adjacent to node_id in the JAG subgraph."""
        if node_id not in self._graph_index:
            return []
        entry = self._graph_index[node_id]
        neighbor_ids = entry.get("neighbors", [])
        results = []
        for nid in neighbor_ids:
            if nid in self._graph_index:
                results.append(self._graph_index[nid])
        return results

    def count(self, source: str | None = None) -> int:
        sql = "SELECT COUNT(*) FROM archival_entries"
        params: list[Any] = []
        if source:
            sql += " WHERE source = ?"
            params.append(source)
        return self._get_conn().execute(sql, params).fetchone()[0]

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


# ---------------------------------------------------------------------------
# Facade: ThreeTierMemory
# ---------------------------------------------------------------------------


class ThreeTierMemory:
    """Unified memory interface for the RAIA agent.

    Composes all three tiers and provides methods for:
      - compose(): inject memory context into RAIA state before deepen_node
      - update_from_trace(): update episodic + working memory after a completed cycle
      - bootstrap(): initialize archival memory from existing artifacts

    Usage pattern in raia_v0.py (Day 9 wiring):
      memory = ThreeTierMemory()
      memory.bootstrap(graph_json_path=Path('data/graphs/jag_anti_supplanting.json'),
                       traces_path=Path('data/eval/raia_day04_traces.jsonl'))

      # Before deepen_node:
      state = memory.compose(state)

      # After verify_node (on successful pass):
      memory.update_from_trace(state)
    """

    def __init__(
        self,
        db_path: Path = _DEFAULT_MEMORY_DB,
        working_max_tokens: int = 2048,
    ) -> None:
        self.working = WorkingMemory(max_tokens=working_max_tokens)
        self.episodic = EpisodicMemory(db_path=db_path)
        self.archival = ArchivalMemory(db_path=db_path)

    def bootstrap(
        self,
        graph_json_path: Path | None = None,
        traces_path: Path | None = None,
    ) -> dict[str, int]:
        """Initialize archival + episodic memory from existing artifacts.

        Call once at agent startup (or when the underlying data changes).
        Returns stats dict: {archival_nodes, episodes_loaded}.
        """
        archival_nodes = 0
        if graph_json_path is not None:
            archival_nodes = self.archival.bootstrap_from_graph(graph_json_path)

        episodes_loaded = 0
        if traces_path is not None:
            episodes_loaded = self.episodic.bulk_load_from_traces_file(traces_path)

        stats = {"archival_nodes": archival_nodes, "episodes_loaded": episodes_loaded}
        logger.info("ThreeTierMemory bootstrap complete: %s", stats)
        return stats

    def compose(self, state: dict) -> dict:
        """Inject memory context into RAIA state before deepen_node.

        Writes three new keys (does not overwrite existing keys):
          state["memory_episodic_context"]  -- relevant past episodes as formatted text
          state["memory_archival_context"]  -- relevant archival entries as formatted text
          state["memory_detector_hints"]    -- list of sub_detector ids to prioritize

        The deepen_node prompt can optionally include these blocks to ground
        its synthesis in prior work and structured knowledge.
        """
        query = state.get("query", "")

        # Episodic: retrieve similar past verified traces
        episodes = self.episodic.retrieve(
            query, k=3, verified_only=True, min_citation_density=0.75
        )
        ep_lines = ["PAST VERIFIED EPISODES:"]
        for ep in episodes:
            ep_lines.append(
                f"  Q: {ep['query'][:120]}"
                f" | density={ep['citation_density']:.2f}"
                f" | legal_findings={ep['legal_findings_count']}"
            )
            if ep.get("final_answer"):
                ep_lines.append(f"  A: {ep['final_answer'][:200]}")
        episodic_context = "\n".join(ep_lines) if episodes else ""

        # Archival: retrieve relevant JAG subgraph entries
        archival_hits = self.archival.retrieve(query, k=5, source_filter="jag_subgraph")
        arch_lines = ["ARCHIVAL KNOWLEDGE (JAG SUBGRAPH):"]
        for hit in archival_hits:
            arch_lines.append(f"  [{hit['key']}] {hit['summary'][:150]}")
        archival_context = "\n".join(arch_lines) if archival_hits else ""

        # Detector hints: sub_detectors that fired in similar past episodes
        detector_hints = self.episodic.get_detector_hints(query, k=5)

        # Update working memory from current state
        self.working.update_from_state(state)

        out = dict(state)
        out["memory_episodic_context"] = episodic_context
        out["memory_archival_context"] = archival_context
        out["memory_detector_hints"] = detector_hints
        out["memory_working_context"] = self.working.get_context_block()
        return out

    def update_from_trace(self, state: dict) -> str | None:
        """Persist a completed RAIA trace to episodic memory.

        Call after verify_node confirms halt_reason (verify_passed or max_iterations).
        Returns episode_id on success, None on error.
        """
        if not state.get("halt_reason"):
            return None
        try:
            ep_id = self.episodic.store_trace(state)
            # Reset working memory for next query cycle
            self.working.clear()
            return ep_id
        except Exception:
            logger.exception("Failed to store trace in episodic memory")
            return None

    def stats(self) -> dict[str, Any]:
        return {
            "working_slots": self.working.slot_count,
            "working_tokens": self.working.token_count,
            "episodic_count": self.episodic.count(),
            "archival_count_total": self.archival.count(),
            "archival_count_jag_subgraph": self.archival.count(source="jag_subgraph"),
            "archival_count_legal_finding": self.archival.count(source="legal_finding"),
        }

    def close(self) -> None:
        self.episodic.close()
        self.archival.close()
