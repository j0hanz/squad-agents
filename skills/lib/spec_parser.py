"""Parse a spec.md document into a SpecDocument.

Shared by skills/create-plan and skills/create-specs scripts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SpecDocument:
    """Parsed representation of a spec markdown file."""

    sections: dict[str, str] = field(default_factory=dict)
    reqs: set[str] = field(default_factory=set)
    acs: set[str] = field(default_factory=set)
    vals: set[str] = field(default_factory=set)
    cons: set[str] = field(default_factory=set)
    raw_lines: list[str] = field(default_factory=list)


_HEADING_RE = re.compile(r"^(#+)\s+(?:\d+\.\s+)?(.+)$")
_REQ_RE = re.compile(r"\b(REQ|SEC|PERF|COMP)-\d+\b")
_AC_RE = re.compile(r"\bAC-\d+\b")
_VAL_RE = re.compile(r"\bVAL-\d+\b")
_CON_RE = re.compile(r"\bCON-\d+\b")


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
    content = Path(path).read_text(encoding="utf-8")
    lines = content.splitlines()

    doc = SpecDocument(raw_lines=lines)
    current_section: str | None = None
    section_lines: list[str] = []

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            if current_section is not None:
                doc.sections[current_section] = "\n".join(section_lines).strip()
            current_section = m.group(2).strip()
            section_lines = []
        elif current_section is not None:
            section_lines.append(line)

        for rm in _REQ_RE.finditer(line):
            doc.reqs.add(rm.group(0))
        for am in _AC_RE.finditer(line):
            doc.acs.add(am.group(0))
        for vm in _VAL_RE.finditer(line):
            doc.vals.add(vm.group(0))
        for cm in _CON_RE.finditer(line):
            doc.cons.add(cm.group(0))

    if current_section is not None:
        doc.sections[current_section] = "\n".join(section_lines).strip()

    return doc
