#!/usr/bin/env python3
"""
Static safety and permission audit for agent.md files.
Usage: python scripts/audit.py <agent.md> [--json] [--strict]
Exit: 0=clean, 1=warnings, 2=errors
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_parser import parse_agent, ParseError, detect_agent_kind, AgentSpec
from lib.report import Finding, render_human, render_json, compute_exit_code
from lib.constants import SHELL_TOOLS

_MUST_NOT: List[str] = ["never", "must not", "do not", "don't", "cannot", "prohibited"]
_ERR_HANDLING: List[str] = [
    "if you encounter",
    "if there is an error",
    "if the tool",
    "when an error",
    "on failure",
    "if it fails",
]

_SKILL_TASK_HINTS: Dict[str, List[str]] = {
    "code-review": [
        r"review\s+(?:my\s+|the\s+|this\s+)?(?:pr|pull request|diff|code)",
        r"code\s+review",
    ],
    "github-automation": [
        r"\bgh\s+api\b",
        r"github\s+cli",
        r"create\s+(?:a\s+)?release",
        r"pr\s+automation",
    ],
    "delivery-manager": [
        r"create\s+(?:a\s+)?pr\b",
        r"finish\s+the\s+feature",
        r"wrap\s+up",
    ],
    "diagnose": [r"\bdebug(?:ging)?\b", r"why\s+is\s+(?:it|this)\s+slow", r"diagnose"],
    "diagrams": [r"\b(?:c4|sequence|erd)\s+diagram\b", r"visualize\s+architecture"],
    "create-specs": [r"draft\s+(?:a\s+)?spec", r"write\s+requirements"],
    "create-plan": [r"create\s+(?:an?\s+)?(?:implementation\s+)?plan"],
    "test-driven-development": [r"\btdd\b", r"test[- ]driven\s+development"],
    "research": [r"deep\s+research", r"investigate\s+the"],
    "refactor": [r"\brefactor(?:ing)?\b"],
}


def check_skill_composition(frontmatter: Dict[str, Any], body: str) -> List[Finding]:
    """Detect strong task-phrase hints without matching pinned skills.
    Returns a list of Finding objects.
    Suppressible via `skill_composition: declined` frontmatter flag.
    """
    if frontmatter.get("skill_composition") == "declined":
        return []

    pinned: set[str] = set()
    for s in frontmatter.get("skills") or []:
        if isinstance(s, dict):
            pinned.add(s.get("name", ""))
        elif isinstance(s, str):
            pinned.add(s)

    findings: List[Finding] = []
    text = body.lower()
    for skill_name, patterns in _SKILL_TASK_HINTS.items():
        if skill_name in pinned:
            continue
        for pat in patterns:
            if re.search(pat, text):
                findings.append(
                    Finding(
                        "warn",
                        "SKILL001",
                        f"agent prompt suggests work that aligns with sibling skill "
                        f"`{skill_name}` (matched: {pat!r}), but no pin found. "
                        f"Run scripts/recommend-skills.py for candidates. "
                        f"Suppress with `skill_composition: declined` in frontmatter.",
                        "",
                    )
                )
                break  # one finding per skill is enough
    return findings


def check_cc_subagent_specific(frontmatter: Dict[str, Any], body: str) -> List[Finding]:
    """CC subagent-specific validation (CCSA001, CCSA002)."""
    findings: List[Finding] = []
    tools = frontmatter.get("tools") or []
    if not all(isinstance(t, str) for t in tools):
        findings.append(
            Finding(
                "error",
                "CCSA001",
                "CC subagent `tools:` must be a flat list of tool name strings",
                "",
            )
        )
    if (
        "Skill" in tools
        and "Skills this" not in body
        and "skills this" not in body.lower()
    ):
        findings.append(
            Finding(
                "warn",
                "CCSA002",
                "CC subagent allows `Skill` tool but the body does not document "
                "which sibling skills are expected. Add a section listing them "
                "so users know what to install.",
                "",
            )
        )
    return findings


def audit(spec: AgentSpec, strict: bool = False) -> List[Finding]:
    findings: List[Finding] = []
    p = spec.path

    for tool in spec.tools:
        if tool.permission == "always_allow":
            findings.append(
                Finding(
                    "error",
                    "PERM001",
                    f"Tool '{tool.name}' has permission 'always_allow' — use 'always_ask' instead.",
                    p,
                )
            )

    for tool in spec.tools:
        if tool.name.lower() in SHELL_TOOLS and tool.permission != "always_ask":
            findings.append(
                Finding(
                    "error",
                    "PERM002",
                    f"Shell-class tool '{tool.name}' must have permission 'always_ask' "
                    f"(found: {tool.permission!r}).",
                    p,
                )
            )

    for mcp in spec.mcp_servers:
        if mcp.permission is None:
            findings.append(
                Finding(
                    "warn",
                    "PERM003",
                    f"MCP server '{mcp.name}' has no explicit 'permission' field.",
                    p,
                )
            )

    for skill in spec.skills:
        if skill.version == "latest":
            findings.append(
                Finding(
                    "error" if strict else "warn",
                    "PIN001",
                    f"Skill '{skill.name}' is pinned to 'latest' — use an explicit version in production.",
                    p,
                )
            )

    for skill in spec.skills:
        if skill.version is None:
            findings.append(
                Finding(
                    "warn",
                    "PIN002",
                    f"Skill '{skill.name}' has no 'version' field — pin to an explicit version.",
                    p,
                )
            )

    prompt_l = spec.system_prompt.lower()

    if not any(kw in prompt_l for kw in _MUST_NOT):
        findings.append(
            Finding(
                "warn",
                "PROMPT001",
                "System prompt has no 'never'/'must not'/'do not' clause — "
                "add explicit behavioral restrictions.",
                p,
            )
        )

    if not any(kw in spec.system_prompt for kw in ("You are", "You will", "Your ")):
        findings.append(
            Finding(
                "warn",
                "PROMPT002",
                "System prompt does not address the agent in second person "
                "('You are...', 'You will...', 'Your ...').",
                p,
            )
        )

    if len(spec.system_prompt) < 100:
        findings.append(
            Finding(
                "info",
                "PROMPT003",
                f"System prompt is {len(spec.system_prompt)} chars — "
                "likely underspecified (< 100 chars).",
                p,
            )
        )

    if not any(kw in prompt_l for kw in _ERR_HANDLING):
        findings.append(
            Finding(
                "info",
                "PROMPT004",
                "System prompt has no error-handling guidance "
                "('if you encounter...', 'on failure...').",
                p,
            )
        )

    if "<example>" not in spec.description:
        findings.append(
            Finding(
                "warn",
                "DESC001",
                "Agent description has no <example> block — add one to improve triggering accuracy.",
                p,
            )
        )

    if "use this agent when" not in spec.description.lower():
        findings.append(
            Finding(
                "warn",
                "DESC002",
                "Agent description does not include 'Use this agent when' trigger phrase.",
                p,
            )
        )

    if "managed-agents-2026-04-01" not in (spec.description + " " + spec.system_prompt):
        findings.append(
            Finding(
                "info",
                "BETA001",
                "No mention of 'managed-agents-2026-04-01' beta header — "
                "ensure your API client sets it.",
                p,
            )
        )

    # Detect agent kind and route to subagent-specific checks
    kind = detect_agent_kind(spec.raw_frontmatter)
    if kind == "cc_subagent":
        for finding in check_cc_subagent_specific(
            spec.raw_frontmatter, spec.system_prompt
        ):
            finding.path = p
            findings.append(finding)

    # Append skill composition check to findings (works for both managed and cc_subagent)
    for finding in check_skill_composition(spec.raw_frontmatter, spec.system_prompt):
        finding.path = p
        findings.append(finding)

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Static safety/permission audit for agent.md files."
    )
    parser.add_argument("agent_file")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (e.g. PIN001 becomes error)",
    )
    args = parser.parse_args()

    try:
        spec = parse_agent(args.agent_file)
    except FileNotFoundError:
        print(f"File not found: {args.agent_file}", file=sys.stderr)
        sys.exit(2)
    except ParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(2)

    findings = audit(spec, strict=args.strict)

    if args.json:
        print(render_json(findings))
    else:
        print(render_human(findings, title=f"audit: {args.agent_file}"))

    sys.exit(compute_exit_code(findings, strict=args.strict))


if __name__ == "__main__":
    main()
