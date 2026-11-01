"""Reasoning mode scaffold for odia-v2 inference.

Implements the chain-of-thought scaffold from the 10-Day Challenge Day 1 spec.
When reasoning_mode is True, the RAG pipeline prepends a structured decomposition
prompt that instructs the model to externalize its reasoning before answering.

The scaffold follows the DeepSeek-R1 cold-start pattern: sub-question enumeration,
evidence mapping per sub-question, synthesis, then final answer. Output is wrapped
in <thinking>...</thinking> tags before the answer text.

Usage:
    from oraculus_di_auditor.interface.reasoning_mode import build_reasoning_prompt
    prompt = build_reasoning_prompt(base_prompt, question)
"""

from __future__ import annotations

REASONING_SCAFFOLD = """\
Before producing your answer, reason through the query step by step inside \
<thinking> tags. Structure your reasoning as follows:

1. Sub-questions: Break the query into the specific sub-questions that must be \
answered to address it fully.
2. Evidence mapping: For each sub-question, identify what specific evidence in the \
retrieved context would answer it. If the context does not contain evidence for a \
sub-question, state that explicitly.
3. Synthesis: State what the evidence collectively shows across the sub-questions.
4. Answer: Provide your final answer based solely on the synthesis above.

Format:
<thinking>
Sub-questions: ...
Evidence: ...
Synthesis: ...
</thinking>
[Your final answer here]
"""


def build_reasoning_prompt(base_prompt: str, question: str) -> str:
    """Inject the reasoning scaffold into a base RAG prompt.

    Inserts the scaffold between the context block and the question line so the
    model sees: context -> reasoning instruction -> question -> cue marker.

    Args:
        base_prompt: Formatted RAG prompt string (context and question already
            substituted via .format()).
        question: Original user question (used to locate insertion point).

    Returns:
        Modified prompt string with reasoning scaffold injected.
    """
    # Locate the question line to insert scaffold before it.
    question_marker = f"Question: {question}"
    if question_marker in base_prompt:
        return base_prompt.replace(
            question_marker,
            f"{REASONING_SCAFFOLD}\nQuestion: {question}",
            1,
        )
    # Fallback: append scaffold before the final line.
    return base_prompt + f"\n\n{REASONING_SCAFFOLD}"


def strip_thinking_tags(text: str) -> tuple[str, str]:
    """Separate <thinking> block from final answer.

    Args:
        text: Raw model output, may or may not contain <thinking>...</thinking>.

    Returns:
        Tuple of (thinking_content, answer). thinking_content is empty string
        if no <thinking> block is present.
    """
    import re

    match = re.search(r"<thinking>(.*?)</thinking>\s*", text, re.DOTALL | re.IGNORECASE)
    if match:
        thinking = match.group(1).strip()
        answer = text[match.end() :].strip()
        return thinking, answer
    return "", text.strip()
