#!/usr/bin/env python3
"""
Wholesale-replacement-safe diff between two agent.md files or directories.
Usage: python scripts/diff.py <current> <proposed> [--json]
Exit: 0=no risk, 2=destructive deletions or permission downgrades
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_parser import parse_agent, ParseError
from lib.report import Finding, render_human, render_json, compute_exit_code


def diff_agents(cur, prop):
    findings = []
    label = f"{cur.path} -> {prop.path}"

    ct = {t.name: t for t in cur.tools}
    pt = {t.name: t for t in prop.tools}
    cs = {s.name: s for s in cur.skills}
    ps = {s.name: s for s in prop.skills}
    cm = {m.name: m for m in cur.mcp_servers}
    pm = {m.name: m for m in prop.mcp_servers}

    # Deletions (error)
    for name in sorted(set(ct) - set(pt)):
        findings.append(
            Finding(
                "error",
                "DIFF_DEL_TOOL",
                f"DELETION: tool '{name}' will be REMOVED by agents.update "
                f"(wholesale-array replacement).",
                label,
            )
        )

    for name in sorted(set(cs) - set(ps)):
        findings.append(
            Finding(
                "error",
                "DIFF_DEL_SKILL",
                f"DELETION: skill '{name}' will be REMOVED by agents.update "
                f"(wholesale-array replacement).",
                label,
            )
        )

    for name in sorted(set(cm) - set(pm)):
        findings.append(
            Finding(
                "error",
                "DIFF_DEL_MCP",
                f"DELETION: MCP server '{name}' will be REMOVED by agents.update "
                f"(wholesale-array replacement).",
                label,
            )
        )

    # Permission downgrades (error)
    for name in set(ct) & set(pt):
        if (
            ct[name].permission == "always_ask"
            and pt[name].permission == "always_allow"
        ):
            findings.append(
                Finding(
                    "error",
                    "DIFF_PERM_DOWNGRADE",
                    f"PERMISSION DOWNGRADE: tool '{name}' always_ask -> always_allow.",
                    label,
                )
            )

    for name in set(cm) & set(pm):
        if (
            cm[name].permission == "always_ask"
            and pm[name].permission == "always_allow"
        ):
            findings.append(
                Finding(
                    "error",
                    "DIFF_PERM_DOWNGRADE",
                    f"PERMISSION DOWNGRADE: MCP server '{name}' always_ask -> always_allow.",
                    label,
                )
            )

    # Skill version -> latest (error)
    for name, sk in ps.items():
        if sk.version == "latest":
            old_v = cs[name].version if name in cs else None
            if old_v != "latest":
                findings.append(
                    Finding(
                        "error",
                        "DIFF_VERSION_LATEST",
                        f"VERSION DRIFT: skill '{name}' -> 'latest' (production pinning violation).",
                        label,
                    )
                )

    # Model change (info)
    if cur.model != prop.model:
        _tiers = {"haiku": 0, "sonnet": 1, "opus": 2}
        ct_name = next((k for k in _tiers if k in cur.model.lower()), None)
        pt_name = next((k for k in _tiers if k in prop.model.lower()), None)
        if ct_name and pt_name:
            direction = "upgrade" if _tiers[pt_name] > _tiers[ct_name] else "downgrade"
        else:
            direction = "change"
        findings.append(
            Finding(
                "info",
                "DIFF_MODEL",
                f"MODEL CHANGE: {cur.model} -> {prop.model} ({direction}).",
                label,
            )
        )

    # Skill version bumps (info)
    for name in set(cs) & set(ps):
        cv, pv = cs[name].version, ps[name].version
        if cv != pv and pv != "latest":
            findings.append(
                Finding(
                    "info",
                    "DIFF_VERSION_BUMP",
                    f"VERSION BUMP: skill '{name}': {cv} -> {pv}.",
                    label,
                )
            )

    # Additions (info)
    for name in sorted(set(pt) - set(ct)):
        findings.append(
            Finding("info", "DIFF_ADD_TOOL", f"ADDITION: tool '{name}' added.", label)
        )

    for name in sorted(set(ps) - set(cs)):
        findings.append(
            Finding("info", "DIFF_ADD_SKILL", f"ADDITION: skill '{name}' added.", label)
        )

    for name in sorted(set(pm) - set(cm)):
        findings.append(
            Finding(
                "info", "DIFF_ADD_MCP", f"ADDITION: MCP server '{name}' added.", label
            )
        )

    # System-prompt diff (info)
    if cur.system_prompt != prop.system_prompt:
        ct_tok = len(cur.system_prompt) // 4
        pt_tok = len(prop.system_prompt) // 4
        delta = pt_tok - ct_tok
        sign = "+" if delta >= 0 else ""
        findings.append(
            Finding(
                "info",
                "DIFF_PROMPT",
                f"SYSTEM PROMPT CHANGED: {ct_tok} -> {pt_tok} tokens ({sign}{delta}).",
                label,
            )
        )

    return findings


def _diff_optional_files(a: Path, b: Path, label: str) -> dict:
    if not a.exists() and not b.exists():
        return {"status": "absent"}
    if not a.exists():
        return {"status": "added", "summary": f"{label} added in right"}
    if not b.exists():
        return {"status": "removed", "summary": f"{label} removed (DESTRUCTIVE)"}
    if a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8"):
        return {"status": "unchanged"}
    return {"status": "changed", "summary": f"{label} differs"}


def _exit_from_deltas(deltas: dict) -> int:
    for v in deltas.values():
        if v.get("status") == "removed":
            return 2
    return 0


def _diff_directories(a: Path, b: Path, args) -> int:
    deltas = {
        "agent_md": _diff_optional_files(a / "agent.md", b / "agent.md", "agent"),
        "plugin_manifest": _diff_optional_files(
            a / ".claude-plugin" / "plugin.json",
            b / ".claude-plugin" / "plugin.json",
            "plugin_manifest",
        ),
        "hooks": _diff_optional_files(
            a / "hooks" / "hooks.json",
            b / "hooks" / "hooks.json",
            "hooks",
        ),
    }
    if args.json:
        print(json.dumps(deltas, indent=2))
    else:
        for k, v in deltas.items():
            if v.get("status") != "unchanged":
                print(f"== {k} ==")
                print(v.get("summary", ""))
    return _exit_from_deltas(deltas)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Wholesale-replacement-safe diff between agent files or directories."
    )
    parser.add_argument("left", help="Left path (file or directory)")
    parser.add_argument("right", help="Right path (file or directory)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    a, b = Path(args.left), Path(args.right)
    if a.is_dir() and b.is_dir():
        sys.exit(_diff_directories(a, b, args))

    # File mode
    try:
        cur = parse_agent(args.left)
        prop = parse_agent(args.right)
    except (FileNotFoundError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    findings = diff_agents(cur, prop)

    if args.json:
        print(render_json(findings))
    else:
        print(render_human(findings, title=f"diff: {args.left} -> {args.right}"))

    sys.exit(compute_exit_code(findings))


if __name__ == "__main__":
    main()
