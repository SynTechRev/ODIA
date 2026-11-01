"""Tests for Day 01: reasoning_mode scaffold (interface/reasoning_mode.py)."""

from __future__ import annotations

from oraculus_di_auditor.interface.reasoning_mode import (
    REASONING_SCAFFOLD,
    build_reasoning_prompt,
    strip_thinking_tags,
)

# ---------------------------------------------------------------------------
# REASONING_SCAFFOLD constant
# ---------------------------------------------------------------------------


def test_scaffold_non_empty():
    assert REASONING_SCAFFOLD.strip()


def test_scaffold_contains_thinking_instruction():
    assert "<thinking>" in REASONING_SCAFFOLD


def test_scaffold_contains_sub_questions():
    assert (
        "sub-question" in REASONING_SCAFFOLD.lower()
        or "Sub-question" in REASONING_SCAFFOLD
    )


def test_scaffold_contains_synthesis():
    assert (
        "synthesis" in REASONING_SCAFFOLD.lower() or "Synthesis" in REASONING_SCAFFOLD
    )


# ---------------------------------------------------------------------------
# build_reasoning_prompt
# ---------------------------------------------------------------------------

_BASE_PROMPT = """\
Context:
Some retrieved audit text here.

Question: What are the unsigned instrument findings?

Your audit analysis:"""


def test_build_inserts_scaffold_before_question():
    result = build_reasoning_prompt(
        _BASE_PROMPT, "What are the unsigned instrument findings?"
    )
    scaffold_pos = result.find(REASONING_SCAFFOLD)
    question_pos = result.find("Question: What are the unsigned instrument findings?")
    assert scaffold_pos != -1
    assert scaffold_pos < question_pos


def test_build_preserves_context():
    result = build_reasoning_prompt(
        _BASE_PROMPT, "What are the unsigned instrument findings?"
    )
    assert "Some retrieved audit text here." in result


def test_build_preserves_cue_marker():
    result = build_reasoning_prompt(
        _BASE_PROMPT, "What are the unsigned instrument findings?"
    )
    assert "Your audit analysis:" in result


def test_build_fallback_when_question_not_found():
    base = "Context: something\n\nFinal answer:"
    result = build_reasoning_prompt(base, "What is missing?")
    assert REASONING_SCAFFOLD in result


def test_build_does_not_duplicate_scaffold():
    result = build_reasoning_prompt(
        _BASE_PROMPT, "What are the unsigned instrument findings?"
    )
    assert result.count(REASONING_SCAFFOLD) == 1


# ---------------------------------------------------------------------------
# strip_thinking_tags
# ---------------------------------------------------------------------------


def test_strip_returns_empty_thinking_when_no_tags():
    thinking, answer = strip_thinking_tags("This is a plain answer.")
    assert thinking == ""
    assert answer == "This is a plain answer."


def test_strip_separates_thinking_from_answer():
    raw = "<thinking>Sub-questions: ...</thinking>\nThe answer is here."
    thinking, answer = strip_thinking_tags(raw)
    assert "Sub-questions:" in thinking
    assert answer == "The answer is here."


def test_strip_handles_multiline_thinking():
    raw = "<thinking>\nLine 1\nLine 2\n</thinking>\nFinal answer."
    thinking, answer = strip_thinking_tags(raw)
    assert "Line 1" in thinking
    assert "Line 2" in thinking
    assert answer == "Final answer."


def test_strip_case_insensitive():
    raw = "<THINKING>reasoning here</THINKING> answer here"
    thinking, answer = strip_thinking_tags(raw)
    assert "reasoning here" in thinking
    assert answer == "answer here"


def test_strip_empty_thinking_block():
    raw = "<thinking></thinking>Just the answer."
    thinking, answer = strip_thinking_tags(raw)
    assert thinking == ""
    assert answer == "Just the answer."


def test_strip_answer_not_empty_when_thinking_present():
    raw = "<thinking>some reasoning</thinking>Meaningful answer text."
    _, answer = strip_thinking_tags(raw)
    assert answer
