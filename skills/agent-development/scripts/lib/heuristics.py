"""
Heuristic functions for token estimation and model-tier scoring.
All functions are pure (no I/O) so they're easy to unit-test.
"""

from __future__ import annotations
from typing import List, Tuple

from .agent_parser import AgentSpec
from .constants import SHELL_TOOLS

# Token estimation constants
CHARS_PER_TOKEN = 4  # industry rule-of-thumb for English prose
TOOL_SCHEMA_TOKENS = 150  # flat budget per tool schema

# Keyword sets for score_complexity
_HIGH_KW = frozenset(
    {
        "adversarial",
        "root cause",
        "security",
        "audit",
        "reason about",
        "deeply",
        "diagnose",
        "investigate",
        "analyze",
        "complex",
        "nuanced",
    }
)
_LOW_KW = frozenset(
    {
        "classify",
        "extract",
        "dispatch",
        "route",
        "label",
        "categorize",
        "lookup",
        "retrieve",
        "fetch",
        "format",
    }
)
_ORCH_VERBS = frozenset(
    {
        "then",
        "afterwards",
        "iterate",
        "retry",
        "loop",
        "repeat",
    }
)


def estimate_tokens(text: str) -> int:
    """Heuristic: chars // 4, minimum 1."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def estimate_input_tokens(spec: AgentSpec) -> int:
    """
    Estimate total input tokens for one invocation.
    Skill bodies are NOT counted (unknown statically) — callers
    should surface this limitation as a caveat in output.
    """
    return estimate_tokens(spec.system_prompt) + len(spec.tools) * TOOL_SCHEMA_TOKENS


def has_shell_tool(spec: AgentSpec) -> bool:
    return any(t.name.lower() in SHELL_TOOLS for t in spec.tools)


def score_complexity(spec: AgentSpec) -> Tuple[int, List[str]]:
    """
    Compute a complexity score and a list of human-readable reason strings.
    Positive → higher tier; negative → lower tier.
    """
    score = 0
    reasons: List[str] = []

    if len(spec.tools) > 5:
        score += 1
        reasons.append(f"+1: {len(spec.tools)} tools (> 5)")

    if len(spec.skills) > 2:
        score += 1
        reasons.append(f"+1: {len(spec.skills)} skills (> 2)")

    if len(spec.system_prompt) > 2000:
        score += 1
        reasons.append(f"+1: system prompt {len(spec.system_prompt)} chars (> 2000)")

    corpus = (spec.system_prompt + " " + spec.description).lower()

    for kw in sorted(_HIGH_KW):
        if kw in corpus:
            score += 2
            reasons.append(f"+2: keyword '{kw}'")

    for kw in sorted(_LOW_KW):
        if kw in corpus:
            score -= 2
            reasons.append(f"-2: keyword '{kw}'")

    orch_count = sum(1 for v in _ORCH_VERBS if v in corpus)
    if orch_count > 3:
        score += 1
        reasons.append(f"+1: orchestration verbs (count={orch_count})")

    return score, reasons


def score_to_tier(score: int, spec: AgentSpec) -> str:
    """
    Map a complexity score to 'haiku' | 'sonnet' | 'opus'.
    Applies override rules before the score mapping.
    """
    # Override: trivially simple agent → always Haiku
    if len(spec.tools) == 0 and len(spec.skills) == 0 and len(spec.system_prompt) < 500:
        return "haiku"

    # Override: shell-class tool → minimum Sonnet
    if has_shell_tool(spec) and score <= 0:
        return "sonnet"

    if score >= 5:
        return "opus"
    if score >= 1:
        return "sonnet"
    return "haiku"
