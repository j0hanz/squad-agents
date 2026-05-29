"""
Parse an agent.md file into an AgentSpec dataclass.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .frontmatter import parse_frontmatter


@dataclass
class Tool:
    name: str
    permission: Optional[str] = None  # 'always_ask' | 'always_allow' | None


@dataclass
class SkillPin:
    name: str
    version: Optional[str] = None  # None = field absent, 'latest' = pinned to latest


@dataclass
class McpServer:
    name: str
    permission: Optional[str] = None


@dataclass
class AgentSpec:
    path: str
    name: str
    description: str
    model: str
    color: Optional[str]
    tools: List[Tool]
    skills: List[SkillPin]
    mcp_servers: List[McpServer]
    system_prompt: str
    raw_frontmatter: Dict[str, Any] = field(default_factory=dict)


class ParseError(Exception):
    pass


def parse_agent(path: str) -> AgentSpec:
    """
    Read an agent.md file and return a fully populated AgentSpec.
    Raises FileNotFoundError if the path doesn't exist.
    Raises ParseError if the file has no valid frontmatter.
    """
    content = Path(path).read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)

    if not fm:
        raise ParseError(f"No valid frontmatter found in {path}")

    def _str(key: str) -> str:
        v = fm.get(key, "")
        return str(v).strip() if v is not None else ""

    tools = []
    for t in fm.get("tools") or []:
        if isinstance(t, dict):
            tools.append(
                Tool(name=t.get("name", "").strip(), permission=t.get("permission"))
            )
        elif isinstance(t, str):
            tools.append(Tool(name=t.strip(), permission=None))
    skills = [
        SkillPin(name=s.get("name", "").strip(), version=s.get("version"))
        for s in (fm.get("skills") or [])
    ]
    mcp_servers = [
        McpServer(name=m.get("name", "").strip(), permission=m.get("permission"))
        for m in (fm.get("mcp_servers") or [])
    ]

    return AgentSpec(
        path=path,
        name=_str("name"),
        description=_str("description"),
        model=_str("model"),
        color=fm.get("color"),
        tools=tools,
        skills=skills,
        mcp_servers=mcp_servers,
        system_prompt=body.strip(),
        raw_frontmatter=fm,
    )


def detect_agent_kind(frontmatter: dict) -> str:
    """Detect whether a frontmatter is a Managed Agent or CC Subagent.

    Heuristics:
      - mcp_servers OR skills with version OR color field → Managed Agent
      - tools as flat list of strings (allowlist) OR model field alone → CC Subagent
      - Tools as list of dicts with `permission` key → Managed Agent
    Returns one of: "managed", "cc_subagent", "unknown".
    """
    if not isinstance(frontmatter, dict):
        return "unknown"
    if "mcp_servers" in frontmatter:
        return "managed"
    if "color" in frontmatter:
        return "managed"
    tools = frontmatter.get("tools")
    if isinstance(tools, list):
        if tools and isinstance(tools[0], dict) and "permission" in tools[0]:
            return "managed"
        if tools and all(isinstance(t, str) for t in tools):
            return "cc_subagent"
    skills = frontmatter.get("skills")
    if (
        isinstance(skills, list)
        and skills
        and isinstance(skills[0], dict)
        and "version" in skills[0]
    ):
        return "managed"
    if "model" in frontmatter and "tools" in frontmatter:
        return "cc_subagent"
    return "unknown"
