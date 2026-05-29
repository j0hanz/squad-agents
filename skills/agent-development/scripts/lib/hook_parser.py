"""Parse and validate Claude Code hooks.json configurations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional


VALID_EVENTS = frozenset(
    {
        "SessionStart",
        "InstructionsLoaded",
        "UserPromptSubmit",
        "PreToolUse",
        "PermissionRequest",
        "PermissionDenied",
        "PostToolUse",
        "PostToolUseFailure",
        "Notification",
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
        "SessionEnd",
    }
)

VALID_HANDLER_TYPES = frozenset({"command", "http", "prompt", "agent"})

# Events that do NOT support prompt/agent hook types
PROMPT_HOOK_SUPPORTED = frozenset(
    {
        "PermissionRequest",
        "PostToolUse",
        "PostToolUseFailure",
        "PreToolUse",
        "Stop",
        "SubagentStop",
        "TaskCompleted",
        "TaskCreated",
        "UserPromptSubmit",
    }
)


class HookConfigError(ValueError):
    """Raised when hooks.json is malformed or violates known constraints."""


@dataclass(frozen=True)
class ParsedHook:
    event: str
    matcher: Optional[str]
    handler_type: str
    raw: dict[str, Any]


def parse_hooks_config(config: dict, strict: bool = False) -> list[ParsedHook]:
    """Parse a hooks.json dict into a flat list of ParsedHook entries.

    Args:
        config: the loaded JSON object (must have top-level "hooks" key)
        strict: if True, raise on unknown events / invalid regex / unsupported handler types.
                If False, skip-with-warning behavior is up to the caller (returns only valid).

    Returns:
        list of ParsedHook, one per inner hook entry.

    Raises:
        HookConfigError: in strict mode, on first violation found.
    """
    if "hooks" not in config:
        raise HookConfigError("missing top-level 'hooks' key")

    parsed: list[ParsedHook] = []
    for event, entries in config["hooks"].items():
        if event not in VALID_EVENTS:
            if strict:
                raise HookConfigError(f"unknown event: {event}")
            continue
        for entry in entries:
            matcher = entry.get("matcher")
            if matcher:
                try:
                    re.compile(matcher)
                except re.error as e:
                    if strict:
                        raise HookConfigError(f"invalid regex in {event} matcher: {e}")
                    continue
            for handler in entry.get("hooks", []):
                htype = handler.get("type")
                if htype not in VALID_HANDLER_TYPES:
                    if strict:
                        raise HookConfigError(f"invalid handler type: {htype}")
                    continue
                if htype in {"prompt", "agent"} and event not in PROMPT_HOOK_SUPPORTED:
                    if strict:
                        raise HookConfigError(
                            f"event {event} does not support {htype} hooks"
                        )
                    continue
                parsed.append(
                    ParsedHook(
                        event=event,
                        matcher=matcher,
                        handler_type=htype,
                        raw=handler,
                    )
                )
    return parsed
