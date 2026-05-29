#!/usr/bin/env python3
"""Emit an agent's dependency graph as JSON or minimal Mermaid.

Hand off Mermaid output to the `diagrams` sibling skill for refinement.

Usage:
  python scripts/diagram.py <agent.md> [--include-hooks <hooks.json>] [--format json|mermaid] [--out <path>]

Exit codes:
  0 — graph emitted
  2 — invalid agent spec
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.frontmatter import parse_frontmatter
from lib.mermaid import AgentGraph, Node, Edge, emit_mermaid
from lib.hook_parser import parse_hooks_config


def build_graph(agent_path: Path, hooks_path: Path | None) -> AgentGraph:
    fm, _body = parse_frontmatter(agent_path.read_text(encoding="utf-8"))
    agent_name = fm.get("name") or agent_path.stem
    nodes: list[Node] = [Node(id="agent", label=str(agent_name), kind="agent")]
    edges: list[Edge] = []

    # Tools — handle two shapes:
    #   tools: ["Read", "Grep", ...]                    (CC subagent flat)
    #   tools: [{name: "bash", permission: "always_ask"}, ...]   (Managed)
    tools = fm.get("tools") or []
    for t in tools:
        if isinstance(t, str):
            tname, perm = t, ""
        elif isinstance(t, dict):
            tname, perm = t.get("name", ""), t.get("permission", "")
        else:
            continue
        nid = f"tool_{tname}"
        label = f"{tname} ({perm})" if perm else tname
        nodes.append(Node(id=nid, label=label, kind="tool"))
        edges.append(Edge(src="agent", dst=nid, label="uses"))

    # Skills
    for s in fm.get("skills", []) or []:
        sname = s.get("name") if isinstance(s, dict) else str(s)
        version = s.get("version", "") if isinstance(s, dict) else ""
        nid = f"skill_{sname}"
        label = f"{sname}@{version}" if version else sname
        nodes.append(Node(id=nid, label=label, kind="skill"))
        edges.append(Edge(src="agent", dst=nid, label="pins"))

    # MCP servers
    for m in fm.get("mcp_servers", []) or []:
        mname = m.get("name") if isinstance(m, dict) else str(m)
        perm = m.get("permission", "") if isinstance(m, dict) else ""
        nid = f"mcp_{mname}"
        label = f"{mname} ({perm})" if perm else mname
        nodes.append(Node(id=nid, label=label, kind="mcp"))
        edges.append(Edge(src="agent", dst=nid, label="uses"))

    # Hook bindings
    if hooks_path:
        hooks_cfg = json.loads(hooks_path.read_text(encoding="utf-8"))
        parsed_hooks = parse_hooks_config(hooks_cfg)
        for i, h in enumerate(parsed_hooks):
            hid = f"hook_{i}"
            cmd = h.raw.get("command") or h.raw.get("url") or h.handler_type
            nodes.append(Node(id=hid, label=str(cmd)[:40], kind="hook"))
            # Edge: tool/event → hook
            if h.matcher and h.event in {
                "PreToolUse",
                "PostToolUse",
                "PostToolUseFailure",
            }:
                tool_id = f"tool_{h.matcher}"
                if any(n.id == tool_id for n in nodes):
                    edges.append(Edge(src=tool_id, dst=hid, label=h.event, kind="hook"))
                    continue
            edges.append(Edge(src="agent", dst=hid, label=h.event, kind="hook"))

    return AgentGraph(nodes=nodes, edges=edges)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("agent_file")
    p.add_argument("--include-hooks", default=None)
    p.add_argument("--format", choices=["json", "mermaid"], default="json")
    p.add_argument("--out", default=None)
    args = p.parse_args(argv)

    agent_path = Path(args.agent_file)
    if not agent_path.exists():
        print(f"error: agent file not found: {agent_path}", file=sys.stderr)
        return 2

    hooks_path = Path(args.include_hooks) if args.include_hooks else None
    if hooks_path and not hooks_path.exists():
        print(f"error: hooks file not found: {hooks_path}", file=sys.stderr)
        return 2

    g = build_graph(agent_path, hooks_path)

    if args.format == "json":
        out = json.dumps(
            {
                "nodes": [asdict(n) for n in g.nodes],
                "edges": [asdict(e) for e in g.edges],
            },
            indent=2,
        )
    else:
        out = emit_mermaid(g)
        out += "\n\n%% For diagram refinement, hand off to the `diagrams` skill.\n"

    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
