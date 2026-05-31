"""Parse a spec.md document into a SpecDocument.

Bundled copy — kept in sync with lib/spec_parser.py so this skill is self-contained.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class SpecDocument:
    """Parsed representation of a spec markdown file."""

    sections: dict[str, str] = field(default_factory=dict)
    reqs: set[str] = field(default_factory=set)
    acs: set[str] = field(default_factory=set)
    vals: set[str] = field(default_factory=set)
    cons: set[str] = field(default_factory=set)
    raw_lines: list[str] = field(default_factory=list)


_HEADING_RE = re.compile(r"^(#+)\s+(?:\d+\.\s+)?(.+)$")
_IDS_RE = re.compile(r"\b((?:REQ|SEC|PERF|COMP|AC|VAL|CON)-\d+)\b")


def parse_spec(path: str | Path) -> SpecDocument:
    """Parse a spec markdown file.

    Args:
        path: Path to the spec .md file.

    Returns:
        SpecDocument with sections, reqs, acs, vals, cons, raw_lines populated.

    Raises:
        FileNotFoundError: If the path doesn't exist.
        OSError: If the file cannot be read.
    """
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    doc = SpecDocument(raw_lines=lines)
    current_section: str | None = None
    section_lines: list[str] = []

    def _flush_section():
        if current_section is not None:
            doc.sections[current_section] = "\n".join(section_lines).strip()

    for line in lines:
        if m := _HEADING_RE.match(line):
            _flush_section()
            current_section = m.group(2).strip()
            section_lines = []
        elif current_section is not None:
            section_lines.append(line)

        for match in _IDS_RE.finditer(line):
            id_str = match.group(1)
            if id_str.startswith("AC-"):
                doc.acs.add(id_str)
            elif id_str.startswith("VAL-"):
                doc.vals.add(id_str)
            elif id_str.startswith("CON-"):
                doc.cons.add(id_str)
            else:
                doc.reqs.add(id_str)

    _flush_section()

    return doc
