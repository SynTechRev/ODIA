"""R.A.I.A. v0 agent: Recursive Analysis Investigative Audit.

Four-node LangGraph cycle: analyze -> cross_reference -> deepen -> verify.
Verify emits either halt (confidence threshold met or max iterations reached)
or loop (back to analyze with reflection in state).

Wired to the production Hybrid retriever (BGE-M3 dense + BM25 sparse + RRF
fusion, reranker disabled per Day 3 production decision).

ReAct pattern (Yao 2022): Thought (analyze/deepen) interleaved with Action
(cross_reference retrieval) and Observation (retrieved passages).
Reflexion pattern (Shinn 2023): verify_node writes a reflection on failure;
analyze_node consumes that reflection on the next iteration to guide deeper
sub-question decomposition.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from oraculus_di_auditor.llm_providers import BaseLLMProvider
from oraculus_di_auditor.retrieval.hybrid import HybridRetriever

logger = logging.getLogger(__name__)

_CITATION_RE = re.compile(r"\(doc_id:([^)]+)\)")


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------


class RAIAState(TypedDict):
    # Input
    query: str
    max_iterations: int
    confidence_threshold: float

    # Analytical state (populated by analyze_node)
    iteration: int
    sub_questions: list[str]
    analytical_angle: str

    # Retrieval state (populated by cross_reference_node)
    retrieved_passages: list[dict[str, Any]]
    citation_pool: list[str]  # doc_ids that passed through retrieval

    # Synthesis state (populated by deepen_node)
    deepened_findings: str
    confidence: float

    # Verification state (populated by verify_node)
    citation_validity: dict[str, bool]  # doc_id -> exists_in_corpus
    verification_notes: str
    reflection: str | None  # populated on failed verify, consumed by next analyze

    # Terminal state (populated by finalize_node)
    final_answer: str
    halt_reason: str  # "verify_passed" | "max_iterations"

    # Full step trace for Mars review
    trace: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def _build_analyze_prompt(
    query: str,
    reflection: str | None,
    iteration: int,
) -> str:
    reflection_block = (
        f"\nPREVIOUS ATTEMPT REFLECTION:\n{reflection}\n" if reflection else ""
    )
    return (
        "You are O.D.I.A., an investigative audit AI analyzing civic documents.\n"
        f"ITERATION: {iteration + 1}\n"
        f"QUERY: {query}\n"
        f"{reflection_block}\n"
        "Decompose this query into 2-4 specific sub-questions each targeting a "
        "different investigative angle. Then state the primary analytical lens.\n\n"
        "Respond in this exact format:\n"
        "SUB_QUESTIONS:\n"
        "1. [sub-question]\n"
        "2. [sub-question]\n\n"
        "ANALYTICAL_ANGLE: [one sentence describing the primary investigative lens]"
    )


def _parse_analyze_response(response: str) -> tuple[list[str], str]:
    sub_questions: list[str] = []
    angle = ""
    in_sq = False
    for line in response.strip().splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("SUB_QUESTIONS"):
            in_sq = True
            continue
        if stripped.upper().startswith("ANALYTICAL_ANGLE"):
            in_sq = False
            angle = stripped.split(":", 1)[-1].strip()
            continue
        if in_sq and re.match(r"^\d+\.", stripped):
            sq = re.sub(r"^\d+\.\s*", "", stripped).strip()
            if sq:
                sub_questions.append(sq)
    if not sub_questions:
        sub_questions = [response[:200].strip() or "re-examine the query"]
    if not angle:
        angle = "investigative audit analysis"
    return sub_questions, angle


def _build_deepen_prompt(
    query: str,
    sub_questions: list[str],
    passages: list[dict[str, Any]],
    angle: str,
) -> str:
    sq_text = "\n".join(f"  {i + 1}. {q}" for i, q in enumerate(sub_questions))
    passage_lines: list[str] = []
    for p in passages[:15]:
        doc_id = p.get("document_id", "unknown")
        title = p.get("title", "")
        findings = p.get("findings", [])
        issues = [f.get("issue", "") for f in findings[:2] if f.get("issue")]
        issues_text = "\n".join(f"    - {iss}" for iss in issues)
        passage_lines.append(f"  [doc_id:{doc_id}] {title}\n{issues_text}")
    passages_block = "\n".join(passage_lines)
    return (
        "You are O.D.I.A., an investigative audit AI.\n"
        f"QUERY: {query}\n"
        f"ANALYTICAL ANGLE: {angle}\n"
        f"SUB-QUESTIONS:\n{sq_text}\n\n"
        "Synthesize a specific investigative finding from the passages below.\n"
        "Rules:\n"
        "  - Cite every specific document using the format (doc_id:XXXX) "
        "where XXXX is the exact doc_id shown in PASSAGES.\n"
        "  - Only cite doc_ids that appear verbatim in the PASSAGES section.\n"
        "  - End your response with a JSON confidence block on its own line: "
        '{"confidence": 0.XX}\n\n'
        f"PASSAGES:\n{passages_block}"
    )


def _parse_deepen_response(response: str) -> tuple[str, float]:
    confidence = 0.5
    match = re.search(r'\{"confidence":\s*(-?[0-9.]+)\}', response)
    if match:
        try:
            confidence = max(0.0, min(1.0, float(match.group(1))))
        except ValueError:
            pass
    findings = re.sub(r'\{"confidence":\s*[0-9.]+\}', "", response).strip()
    return findings, confidence


def _extract_citations(text: str) -> list[str]:
    seen: dict[str, None] = {}
    for m in _CITATION_RE.finditer(text):
        seen[m.group(1)] = None
    return list(seen)


def _build_verify_notes(
    validity: dict[str, bool],
    all_valid: bool,
    confidence_met: bool,
) -> str:
    parts: list[str] = []
    if not validity:
        parts.append("No citations found in findings.")
    elif not all_valid:
        invalid = [d for d, v in validity.items() if not v]
        parts.append(f"Invalid citations: {invalid}.")
    else:
        parts.append("All citations valid.")
    parts.append("Confidence threshold " + ("met." if confidence_met else "not met."))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def analyze_node(state: RAIAState, provider: BaseLLMProvider) -> RAIAState:
    """Decompose query into sub-questions. Consume reflection on loop iterations."""
    prompt = _build_analyze_prompt(
        query=state["query"],
        reflection=state.get("reflection"),
        iteration=state["iteration"],
    )
    response = provider.generate(prompt=prompt, context="", max_tokens=512)
    sub_questions, angle = _parse_analyze_response(response)
    state["sub_questions"] = sub_questions
    state["analytical_angle"] = angle
    state["trace"].append(
        {
            "node": "analyze",
            "iteration": state["iteration"],
            "sub_questions": sub_questions,
            "angle": angle,
        }
    )
    return state


def cross_reference_node(
    state: RAIAState,
    retriever: HybridRetriever,
    k: int = 10,
) -> RAIAState:
    """Retrieve related passages for each sub-question. Build citation pool."""
    all_passages: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for sub_q in state["sub_questions"]:
        results = retriever.query(sub_q, top_k=k)
        for r in results:
            doc_id = r.get("document_id", "")
            if doc_id and doc_id not in seen_ids:
                all_passages.append(r)
                seen_ids.add(doc_id)
    state["retrieved_passages"] = all_passages
    state["citation_pool"] = sorted(seen_ids)
    state["trace"].append(
        {
            "node": "cross_reference",
            "iteration": state["iteration"],
            "passages_retrieved": len(all_passages),
            "unique_docs": len(seen_ids),
        }
    )
    return state


def deepen_node(state: RAIAState, provider: BaseLLMProvider) -> RAIAState:
    """Synthesize pattern from retrieved passages. Produce deepened findings
    with inline citations as (doc_id:XXX) markers."""
    prompt = _build_deepen_prompt(
        query=state["query"],
        sub_questions=state["sub_questions"],
        passages=state["retrieved_passages"],
        angle=state["analytical_angle"],
    )
    response = provider.generate(prompt=prompt, context="", max_tokens=1024)
    findings, confidence = _parse_deepen_response(response)
    state["deepened_findings"] = findings
    state["confidence"] = confidence
    state["trace"].append(
        {
            "node": "deepen",
            "iteration": state["iteration"],
            "findings_length": len(findings),
            "confidence": confidence,
        }
    )
    return state


def verify_node(state: RAIAState, corpus_ids: set[str]) -> RAIAState:
    """Check citations and confidence threshold. Write reflection on failure."""
    cited = _extract_citations(state["deepened_findings"])
    validity = {doc_id: doc_id in corpus_ids for doc_id in cited}
    all_valid = all(validity.values()) if validity else True
    confidence_met = state["confidence"] >= state["confidence_threshold"]

    state["citation_validity"] = validity
    state["verification_notes"] = _build_verify_notes(
        validity, all_valid, confidence_met
    )

    if not all_valid:
        invalid = [d for d, v in validity.items() if not v]
        state["reflection"] = (
            f"Cited non-existent document IDs: {', '.join(invalid)}. "
            "On the next iteration, only cite doc_ids that appear verbatim "
            "in the retrieved passages."
        )
    elif not confidence_met:
        state["reflection"] = (
            f"Confidence {state['confidence']:.2f} is below threshold "
            f"{state['confidence_threshold']:.2f}. "
            "Deepen the analysis: identify more specific evidence, "
            "cross-reference additional patterns, and make a stronger claim."
        )
    else:
        state["reflection"] = None

    state["trace"].append(
        {
            "node": "verify",
            "iteration": state["iteration"],
            "citations_found": len(cited),
            "citations_valid": all_valid,
            "confidence_met": confidence_met,
            "verification_notes": state["verification_notes"],
        }
    )
    state["iteration"] += 1
    return state


def finalize_node(state: RAIAState) -> RAIAState:
    """Compose final answer and record halt reason."""
    if state["reflection"] is not None:
        state["halt_reason"] = "max_iterations"
    else:
        state["halt_reason"] = "verify_passed"
    state["final_answer"] = state["deepened_findings"]
    state["trace"].append(
        {
            "node": "finalize",
            "halt_reason": state["halt_reason"],
            "final_iteration": state["iteration"],
            "final_confidence": state["confidence"],
        }
    )
    return state


def _should_continue(state: RAIAState) -> Literal["loop", "finalize"]:
    """Route after verify: loop back to analyze or proceed to finalize."""
    if state["iteration"] >= state["max_iterations"]:
        return "finalize"
    if state["reflection"] is None:
        return "finalize"
    return "loop"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_raia_graph(
    retriever: HybridRetriever,
    provider: BaseLLMProvider,
    corpus_ids: set[str],
) -> Any:
    """Construct and compile the R.A.I.A. LangGraph graph."""
    builder: StateGraph = StateGraph(RAIAState)

    builder.add_node("analyze", lambda s: analyze_node(s, provider))
    builder.add_node("cross_reference", lambda s: cross_reference_node(s, retriever))
    builder.add_node("deepen", lambda s: deepen_node(s, provider))
    builder.add_node("verify", lambda s: verify_node(s, corpus_ids))
    builder.add_node("finalize", finalize_node)

    builder.set_entry_point("analyze")
    builder.add_edge("analyze", "cross_reference")
    builder.add_edge("cross_reference", "deepen")
    builder.add_edge("deepen", "verify")
    builder.add_conditional_edges(
        "verify",
        _should_continue,
        {"loop": "analyze", "finalize": "finalize"},
    )
    builder.add_edge("finalize", END)

    return builder.compile()


def run_raia(
    query: str,
    retriever: HybridRetriever,
    provider: BaseLLMProvider,
    corpus_ids: set[str],
    max_iterations: int = 3,
    confidence_threshold: float = 0.75,
) -> RAIAState:
    """Run a single query through the R.A.I.A. graph. Returns final state."""
    graph = build_raia_graph(retriever, provider, corpus_ids)
    initial_state: RAIAState = {
        "query": query,
        "max_iterations": max_iterations,
        "confidence_threshold": confidence_threshold,
        "iteration": 0,
        "sub_questions": [],
        "analytical_angle": "",
        "retrieved_passages": [],
        "citation_pool": [],
        "deepened_findings": "",
        "confidence": 0.0,
        "citation_validity": {},
        "verification_notes": "",
        "reflection": None,
        "final_answer": "",
        "halt_reason": "",
        "trace": [],
    }
    return graph.invoke(initial_state)
