#!/usr/bin/env python3
"""
Compile an agent.md file into the JSON payload for agents.create or agents.update.
Usage: python scripts/compile.py <agent.md> [--for create|update] [--out payload.json] [--json]
Exit: 0=valid, 2=schema error
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_parser import parse_agent, detect_agent_kind, ParseError
from lib.report import Finding, render_human, render_json, compute_exit_code
from lib.constants import KNOWN_MODELS, KNOWN_FRONTMATTER_KEYS


def _compile_cc_subagent(frontmatter: dict, body: str) -> dict:
    required = {"name", "description"}
    missing = required - set(frontmatter.keys())
    if missing:
        raise ValueError(f"CC subagent missing required keys: {sorted(missing)}")
    return {
        "kind": "cc_subagent",
        "name": frontmatter["name"],
        "description": frontmatter["description"],
        "model": frontmatter.get("model"),
        "tools": frontmatter.get("tools") or [],
        "body_preview": body.strip().splitlines()[:3],
    }


def validate(spec, mode: str):
    findings = []
    p = spec.path

    if not spec.name:
        findings.append(
            Finding("error", "COMPILE_REQ", "Required field 'name' is empty.", p)
        )

    if mode == "create":
        if not spec.description:
            findings.append(
                Finding(
                    "error",
                    "COMPILE_REQ",
                    "Required field 'description' is empty (needed for create).",
                    p,
                )
            )
        if not spec.model:
            findings.append(
                Finding(
                    "error",
                    "COMPILE_REQ",
                    "Required field 'model' is empty (needed for create).",
                    p,
                )
            )

    if spec.model and spec.model not in KNOWN_MODELS:
        findings.append(
            Finding(
                "warn",
                "COMPILE_MODEL",
                f"Unknown model '{spec.model}'. "
                f"Known: {sorted(KNOWN_MODELS)}. May still be valid.",
                p,
            )
        )

    unknown_keys = set(spec.raw_frontmatter.keys()) - KNOWN_FRONTMATTER_KEYS
    for key in sorted(unknown_keys):
        findings.append(
            Finding(
                "warn",
                "COMPILE_UNKNOWN_KEY",
                f"Unknown frontmatter key '{key}' will be ignored by the API.",
                p,
            )
        )

    return findings


def to_payload(spec, mode: str) -> dict:
    payload: dict = {"name": spec.name}
    if spec.description:
        payload["description"] = spec.description
    if spec.model:
        payload["model"] = spec.model
    if spec.color:
        payload["color"] = spec.color
    if spec.tools:
        payload["tools"] = [
            {"name": t.name, **({"permission": t.permission} if t.permission else {})}
            for t in spec.tools
        ]
    if spec.skills:
        payload["skills"] = [
            {"name": s.name, **({"version": s.version} if s.version else {})}
            for s in spec.skills
        ]
    if spec.mcp_servers:
        payload["mcp_servers"] = [
            {"name": m.name, **({"permission": m.permission} if m.permission else {})}
            for m in spec.mcp_servers
        ]
    if spec.system_prompt:
        payload["system_prompt"] = spec.system_prompt
    return payload


def render_preview(payload: dict, mode: str) -> str:
    lines = [f"=== Compiled payload for agents.{mode} ==="]
    if mode == "update":
        array_keys = [k for k in ("tools", "skills", "mcp_servers") if k in payload]
        if array_keys:
            lines += [
                "",
                "!! WHOLESALE REPLACEMENT: these arrays will be fully replaced:",
            ]
            for k in array_keys:
                lines.append(f"     {k}: {len(payload[k])} item(s)")
            lines.append(
                "   Any item NOT present here will be DELETED from the live agent."
            )
    lines += ["", json.dumps(payload, indent=2)]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compile agent.md -> JSON payload.")
    parser.add_argument("agent_file")
    parser.add_argument(
        "--for", dest="mode", choices=["create", "update"], default="update"
    )
    parser.add_argument("--out", help="Write payload to this path")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit just the JSON payload on stdout (no preview)",
    )
    args = parser.parse_args()

    try:
        spec = parse_agent(args.agent_file)
    except (FileNotFoundError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    kind = detect_agent_kind(spec.raw_frontmatter)
    if kind == "cc_subagent":
        try:
            payload = _compile_cc_subagent(spec.raw_frontmatter, spec.system_prompt)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        findings = validate(spec, args.mode)
        code = compute_exit_code(findings)

        if findings:
            if args.json:
                print(render_json(findings), file=sys.stderr)
            else:
                print(render_human(findings), file=sys.stderr)
            if code == 2:
                sys.exit(2)

        payload = to_payload(spec, args.mode)

    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        if not args.json:
            print(render_preview(payload, args.mode))
    else:
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(render_preview(payload, args.mode))

    sys.exit(0)


if __name__ == "__main__":
    main()
