import pytest
from lib.simulator import (
    parse_tool_calls_jsonl,
    evaluate_assertions,
    aggregate_runs,
    match_tool_pattern,
    ToolCall,
    RunResult,
)


def test_match_tool_pattern_exact_tool():
    assert match_tool_pattern(
        "Bash(*)", {"tool_name": "Bash", "tool_input": {"command": "ls"}}
    )
    assert not match_tool_pattern(
        "Bash(*)", {"tool_name": "Read", "tool_input": {"file_path": "x"}}
    )


def test_match_tool_pattern_glob():
    call = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}
    assert match_tool_pattern("Bash(rm *)", call)
    assert not match_tool_pattern("Bash(ls *)", call)


def test_parse_jsonl_handles_empty():
    assert parse_tool_calls_jsonl("") == []


def test_parse_jsonl_two_calls():
    text = (
        '{"tool_name": "Bash", "tool_input": {"command": "ls"}, "hook_event_name": "PreToolUse"}\n'
        '{"tool_name": "Read", "tool_input": {"file_path": "x"}, "hook_event_name": "PreToolUse"}\n'
    )
    calls = parse_tool_calls_jsonl(text)
    assert len(calls) == 2
    assert calls[0].tool_name == "Bash"


def test_must_not_call_violated():
    calls = [ToolCall(tool_name="Bash", tool_input={"command": "rm -rf x"})]
    result = evaluate_assertions(
        calls=calls,
        final_response="done",
        expect={"must_not_call": ["Bash(rm *)"]},
        duration_s=1.0,
    )
    assert not result.passed
    assert any("must_not_call" in r.reason for r in result.failures)


def test_must_call_one_of_satisfied():
    calls = [ToolCall(tool_name="WebFetch", tool_input={"url": "https://github.com/x"})]
    result = evaluate_assertions(
        calls=calls,
        final_response="...",
        expect={"must_call_one_of": ["WebFetch(*)", "WebSearch(*)"]},
        duration_s=1.0,
    )
    assert result.passed


def test_aggregate_runs_computes_flakiness():
    runs = [
        RunResult(passed=True, duration_ms=100, tokens_in=10, tokens_out=20),
        RunResult(passed=False, duration_ms=200, tokens_in=11, tokens_out=22),
        RunResult(passed=True, duration_ms=150, tokens_in=12, tokens_out=21),
    ]
    agg = aggregate_runs(runs)
    assert agg["pass_rate"] == pytest.approx(2 / 3, rel=0.01)
    assert 0.3 < agg["flakiness"] < 0.4
    assert agg["median_latency_ms"] == 150
