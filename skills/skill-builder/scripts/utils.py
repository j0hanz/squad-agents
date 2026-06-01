"""Shared utilities for skill-builder scripts."""

import re
from pathlib import Path
from typing import Any


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse a flat YAML-style frontmatter block into top-level key/value pairs."""
    try:
        import yaml

        result = yaml.safe_load(text) or {}
        if not isinstance(result, dict):
            return {}
        return {str(k): v for k, v in result.items()}
    except ImportError:
        pass

    # Fallback: hand-rolled parser for environments without PyYAML
    result: dict[str, Any] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*):\s*(.*)", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value in (">", "|", ">-", "|-", ">+", "|+", ""):
                i += 1
                block: list[str] = []
                while i < len(lines) and (
                    lines[i].startswith("  ") or lines[i].startswith("\t")
                ):
                    block.append(lines[i].strip())
                    i += 1
                sep = "\n" if value in ("|", "|-") else " "
                result[key] = sep.join(block)
                continue
            else:
                result[key] = value.strip('"').strip("'")
        i += 1
    return result


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    skill_md_path = skill_path / "SKILL.md"
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"SKILL.md not found in {skill_path}") from None

    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        raise ValueError(f"SKILL.md in {skill_path} missing frontmatter")

    fm = _parse_frontmatter(match.group(1))
    name = fm.get("name", "").strip()
    description = fm.get("description", "").strip()

    return name, description, content
