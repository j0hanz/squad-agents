"""Emit Mermaid graph syntax from an agent graph data model.

This module owns only string emission. For diagram refinement,
hand off to the `diagrams` sibling skill.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    id: str
    label: str
    kind: str  # "agent" | "tool" | "mcp" | "hook" | "skill"


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    label: str = ""
    kind: str = "default"  # "default" | "hook" | "permission"


@dataclass(frozen=True)
class AgentGraph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)


def _escape(s: str) -> str:
    return s.replace('"', "#quot;")


def emit_mermaid(g: AgentGraph) -> str:
    lines = ["graph LR"]
    for n in g.nodes:
        lines.append(f'  {n.id}["{_escape(n.label)}"]')
    for e in g.edges:
        if e.kind == "hook":
            if e.label:
                lines.append(f"  {e.src} -.{_escape(e.label)}.-> {e.dst}")
            else:
                lines.append(f"  {e.src} -.-> {e.dst}")
        elif e.label:
            lines.append(f"  {e.src} -->|{_escape(e.label)}| {e.dst}")
        else:
            lines.append(f"  {e.src} --> {e.dst}")
    return "\n".join(lines)
