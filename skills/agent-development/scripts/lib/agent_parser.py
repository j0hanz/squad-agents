"""
Parse an agent.md file into an AgentSpec dataclass.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

from .frontmatter import parse_frontmatter


@dataclass(frozen=True)
class Tool:
    """Represents a tool available to an agent."""

    name: str
    permission: Optional[Literal["always_ask", "always_allow"]] = None


@dataclass(frozen=True)
class SkillPin:
    """Represents a pinned skill for an agent."""

    name: str
    version: Optional[str] = None  # None = field absent, 'latest' = pinned to latest


@dataclass(frozen=True)
class McpServer:
    """Represents an MCP server used by an agent."""

    name: str
    permission: Optional[Literal["always_ask", "always_allow"]] = None


@dataclass(frozen=True)
class AgentSpec:
    """Consolidated specification for an agent."""

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
    """Raised when an agent.md file cannot be parsed."""

    pass


def parse_agent(path: str | Path) -> AgentSpec:
    """
    Read an agent.md file and return a fully populated AgentSpec.

    Args:
        path: Path to the agent.md file.

    Returns:
        An AgentSpec object containing the parsed data.

    Raises:
        FileNotFoundError: If the path doesn't exist.
        ParseError: If the file has no valid frontmatter or is malformed.
    """
    path_obj = Path(path)
    try:
        content = path_obj.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise ParseError(f"Failed to read agent file at {path}: {e}") from e

    fm, body = parse_frontmatter(content)

    if not fm:
        raise ParseError(f"No valid frontmatter found in {path}")

    def _str(key: str) -> str:
        v = fm.get(key, "")
        return str(v).strip() if v is not None else ""

    tools: List[Tool] = []
    for t in fm.get("tools") or []:
        if isinstance(t, dict):
            name = t.get("name", "").strip()
            perm = t.get("permission")
            if perm not in (None, "always_ask", "always_allow"):
                # We could raise an error here or just log it, let's be strict
                raise ParseError(
                    f"Invalid permission '{perm}' for tool '{name}' in {path}"
                )
            tools.append(Tool(name=name, permission=perm))
        elif isinstance(t, str):
            tools.append(Tool(name=t.strip(), permission=None))
        else:
            raise ParseError(f"Invalid tool entry in {path}: {t}")

    skills = [
        SkillPin(name=str(s.get("name", "")).strip(), version=s.get("version"))
        for s in (fm.get("skills") or [])
        if isinstance(s, dict)
    ]

    mcp_servers = []
    for m in fm.get("mcp_servers") or []:
        if isinstance(m, dict):
            name = str(m.get("name", "")).strip()
            perm = m.get("permission")
            if perm not in (None, "always_ask", "always_allow"):
                raise ParseError(
                    f"Invalid permission '{perm}' for MCP server '{name}' in {path}"
                )
            mcp_servers.append(McpServer(name=name, permission=perm))

    return AgentSpec(
        path=str(path),
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


def detect_agent_kind(
    frontmatter: Dict[str, Any],
) -> Literal["managed", "cc_subagent", "unknown"]:
    """Detect whether a frontmatter represents a Managed Agent or CC Subagent.

    Heuristics:
      - mcp_servers OR skills with version OR color field → Managed Agent
      - tools as flat list of strings (allowlist) OR model field alone → CC Subagent
      - Tools as list of dicts with `permission` key → Managed Agent

    Returns:
        "managed", "cc_subagent", or "unknown".
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
