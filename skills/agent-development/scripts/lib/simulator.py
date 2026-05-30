"""Pure functions backing simulate.py. Orchestration lives in the script."""

from __future__ import annotations

import fnmatch
import json
import re
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union


@dataclass(frozen=True)
class ToolCall:
    """Represents a single tool call captured during simulation."""

    tool_name: str
    tool_input: Dict[str, Any]


@dataclass(frozen=True)
class AssertionResult:
    """Represents the result of a single assertion."""

    name: str
    passed: bool
    reason: str


@dataclass
class CaseEvaluation:
    """Represents the full evaluation of a test case."""

    passed: bool
    failures: List[AssertionResult] = field(default_factory=list)
    successes: List[AssertionResult] = field(default_factory=list)


@dataclass(frozen=True)
class RunResult:
    """Represents the results of a single execution run."""

    passed: bool
    duration_ms: int
    tokens_in: int
    tokens_out: int


# Pattern syntax: "ToolName(arg-glob)" where arg-glob uses fnmatch syntax
_PATTERN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\((.*)\)$")


def match_tool_pattern(pattern: str, call: Union[Dict[str, Any], ToolCall]) -> bool:
    """Check if a tool call matches a Tool(arg-glob) pattern."""
    if isinstance(call, ToolCall):
        tool_name = call.tool_name
        tool_input = call.tool_input
    else:
        tool_name = str(call.get("tool_name", ""))
        tool_input = call.get("tool_input", {})

    m = _PATTERN_RE.match(pattern)
    if not m:
        return tool_name == pattern
    expected_tool, arg_glob = m.group(1), m.group(2)
    if tool_name != expected_tool:
        return False
    if arg_glob in {"", "*"}:
        return True
    # Match against primary arg by tool
    primary_arg = (
        tool_input.get("command")
        or tool_input.get("file_path")
        or tool_input.get("url")
        or tool_input.get("query")
        or tool_input.get("pattern")
        or ""
    )
    return fnmatch.fnmatchcase(str(primary_arg), arg_glob)


def parse_tool_calls_jsonl(text: str) -> List[ToolCall]:
    """Parse the observer JSONL into ToolCall list (PreToolUse entries only)."""
    out: List[ToolCall] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj: Dict[str, Any] = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("hook_event_name") != "PreToolUse":
            continue
        out.append(
            ToolCall(
                tool_name=str(obj.get("tool_name", "")),
                tool_input=obj.get("tool_input", {}),
            )
        )
    return out


def evaluate_assertions(
    calls: List[ToolCall],
    final_response: str,
    expect: Dict[str, Any],
    duration_s: float,
) -> CaseEvaluation:
    """Evaluate a set of assertions against captured tool calls and response."""
    successes: List[AssertionResult] = []
    failures: List[AssertionResult] = []

    def _record(name: str, ok: bool, reason: str) -> None:
        (successes if ok else failures).append(AssertionResult(name, ok, reason))

    # must_not_call
    for pat in expect.get("must_not_call", []):
        violated = any(match_tool_pattern(pat, c) for c in calls)
        _record(
            "must_not_call",
            not violated,
            f"must_not_call({pat}) — {'violated' if violated else 'ok'}",
        )

    # must_call
    for pat in expect.get("must_call", []):
        seen = any(match_tool_pattern(pat, c) for c in calls)
        _record("must_call", seen, f"must_call({pat}) — {'ok' if seen else 'missing'}")

    # must_call_one_of
    pats: List[str] = expect.get("must_call_one_of", [])
    if pats:
        any_seen = any(match_tool_pattern(p, c) for p in pats for c in calls)
        _record(
            "must_call_one_of",
            any_seen,
            f"must_call_one_of({pats}) — {'ok' if any_seen else 'none seen'}",
        )

    # max_tool_calls
    if "max_tool_calls" in expect:
        cap = int(expect["max_tool_calls"])
        ok = len(calls) <= cap
        _record("max_tool_calls", ok, f"{len(calls)} calls (cap {cap})")

    # max_duration_s
    if "max_duration_s" in expect:
        cap = float(expect["max_duration_s"])
        ok = duration_s <= cap
        _record("max_duration_s", ok, f"{duration_s:.1f}s (cap {cap})")

    # final_response_must_contain
    for s in expect.get("final_response_must_contain", []):
        ok = s in final_response
        _record("final_response_must_contain", ok, f"contains {s!r}: {ok}")

    # final_response_must_not_contain
    for s in expect.get("final_response_must_not_contain", []):
        ok = s not in final_response
        _record("final_response_must_not_contain", ok, f"absent of {s!r}: {ok}")

    # final_response_must_match
    rx = expect.get("final_response_must_match")
    if rx:
        # Allow /pattern/flags form
        m = re.match(r"^/(.*)/([gimsux]*)$", rx)
        if m:
            pat, flags = m.group(1), m.group(2)
            flag_val = 0
            if "i" in flags:
                flag_val |= re.IGNORECASE
            if "m" in flags:
                flag_val |= re.MULTILINE
            if "s" in flags:
                flag_val |= re.DOTALL
            ok = re.search(pat, final_response, flag_val) is not None
        else:
            ok = re.search(rx, final_response) is not None
        _record("final_response_must_match", ok, f"regex {rx!r}: {ok}")

    # domain_allowlist
    for tool_name, allowed in expect.get("domain_allowlist", {}).items():
        for c in calls:
            if c.tool_name != tool_name:
                continue
            url = str(c.tool_input.get("url", ""))
            domain_ok = any(d in url for d in allowed)
            _record(
                "domain_allowlist",
                domain_ok,
                f"{tool_name} call to {url!r} allowed={domain_ok}",
            )

    return CaseEvaluation(
        passed=not failures,
        successes=successes,
        failures=failures,
    )


def aggregate_runs(runs: List[RunResult]) -> Dict[str, Any]:
    """Aggregate results from multiple simulation runs."""
    if not runs:
        return {"pass_rate": 0.0, "flakiness": 1.0, "n": 0}
    n = len(runs)
    n_pass = sum(1 for r in runs if r.passed)
    pass_rate = n_pass / n
    durs = [r.duration_ms for r in runs]
    return {
        "n": n,
        "pass_rate": pass_rate,
        "flakiness": 1.0 - pass_rate,
        "median_latency_ms": int(statistics.median(durs)),
        "p95_latency_ms": int(sorted(durs)[max(0, int(0.95 * n) - 1)]),
        "mean_tokens_in": int(statistics.mean(r.tokens_in for r in runs)),
        "mean_tokens_out": int(statistics.mean(r.tokens_out for r in runs)),
    }
