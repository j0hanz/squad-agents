"""Shared utilities for skill-builder scripts."""

import re
from pathlib import Path


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a flat YAML-style frontmatter block into top-level key/value pairs."""
    try:
        import yaml

        result = yaml.safe_load(text) or {}
        return {k: str(v) for k, v in result.items() if isinstance(k, str)}
    except ImportError:
        pass

    # Fallback: hand-rolled parser for environments without PyYAML
    result: dict[str, str] = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*):\s*(.*)", lines[i])
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value in (">", "|", ">-", "|-", ""):
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
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")

    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md missing frontmatter")

    frontmatter_text = match.group(1)

    try:
        import yaml

        fm = yaml.safe_load(frontmatter_text) or {}
        name = str(fm.get("name", "")).strip()
        description = fm.get("description", "")
        if isinstance(description, list):
            description = " ".join(description)
        description = str(description).strip()
    except ImportError:
        fm = _parse_frontmatter(frontmatter_text)
        name = fm.get("name", "").strip().strip('"').strip("'")
        description = fm.get("description", "").strip().strip('"').strip("'")

    return name, description, content
