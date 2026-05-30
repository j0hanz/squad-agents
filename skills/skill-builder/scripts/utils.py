"""Shared utilities for skill-builder scripts."""

from pathlib import Path


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")

    match = __import__("re").match(r"^---\n(.*?)\n---\n", content, __import__("re").DOTALL)
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
        # Fallback: hand-rolled parser (no PyYAML)
        name = ""
        description = ""
        lines = frontmatter_text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("name:"):
                name = line[len("name:"):].strip().strip('"').strip("'")
            elif line.startswith("description:"):
                value = line[len("description:"):].strip()
                if value in (">", "|", ">-", "|-"):
                    continuation_lines: list[str] = []
                    i += 1
                    while i < len(lines) and (
                        lines[i].startswith("  ") or lines[i].startswith("\t")
                    ):
                        continuation_lines.append(lines[i].strip())
                        i += 1
                    sep = "\n" if value in ("|", "|-") else " "
                    description = sep.join(continuation_lines)
                    continue
                else:
                    description = value.strip('"').strip("'")
            i += 1

    return name, description, content
