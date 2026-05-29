import json
from pathlib import Path
import pytest

from lib.hook_parser import (
    parse_hooks_config,
    VALID_EVENTS,
    ParsedHook,
    HookConfigError,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_valid_config():
    cfg = json.load(open(FIXTURES / "valid-hook-config.json"))
    parsed = parse_hooks_config(cfg)
    assert len(parsed) == 2
    events = {h.event for h in parsed}
    assert events == {"PreToolUse", "SubagentStop"}


def test_unknown_event_rejected():
    cfg = json.load(open(FIXTURES / "malicious-hook-config.json"))
    with pytest.raises(HookConfigError) as exc:
        parse_hooks_config(cfg, strict=True)
    assert "NonexistentEvent" in str(exc.value)


def test_invalid_regex_rejected():
    cfg = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "[bad(", "hooks": [{"type": "command", "command": "x"}]}
            ]
        }
    }
    with pytest.raises(HookConfigError) as exc:
        parse_hooks_config(cfg, strict=True)
    assert "regex" in str(exc.value).lower()


def test_valid_events_complete():
    # Spot check: must include the 28 documented events
    must_have = {
        "SessionStart",
        "SessionEnd",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "PermissionRequest",
        "PermissionDenied",
        "SubagentStart",
        "SubagentStop",
        "TaskCreated",
        "TaskCompleted",
        "Stop",
        "StopFailure",
        "TeammateIdle",
        "ConfigChange",
        "CwdChanged",
        "FileChanged",
        "WorktreeCreate",
        "WorktreeRemove",
        "PreCompact",
        "PostCompact",
        "Elicitation",
        "ElicitationResult",
        "InstructionsLoaded",
        "Notification",
    }
    assert must_have.issubset(VALID_EVENTS)


def test_parsed_hook_shape():
    cfg = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "x"}]}]}}
    parsed = parse_hooks_config(cfg)
    h = parsed[0]
    assert isinstance(h, ParsedHook)
    assert h.event == "Stop"
    assert h.handler_type == "command"
    assert h.matcher is None or h.matcher == ""
