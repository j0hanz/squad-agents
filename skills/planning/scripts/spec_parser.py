"""Unified parser for spec and plan markdown files.

Shared by all scripts in skills/planning/scripts/.
Zero non-stdlib imports.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "SpecDocument",
    "PlanDocument",
    "PlanTask",
    "parse_spec",
    "parse_plan",
    "feature_name",
    "PLAN_MANDATORY_FIELDS",
    "IMPL_PREFIXES",
]


def feature_name(spec_path: str | Path) -> str:
    """Derive the feature stem from a <name>.specs.md path (strips '.specs')."""
    return Path(spec_path).stem.replace(".specs", "")


# Prefixes that require implementation tasks (not CON/AC/VAL — those don't need impl tasks)
IMPL_PREFIXES: tuple[str, ...] = ("REQ-", "SEC-", "PERF-", "COMP-")


# ---------------------------------------------------------------------------
# Spec document
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class SpecDocument:
    """Parsed representation of a <name>.specs.md file."""

    sections: dict[str, str] = field(default_factory=dict)
    reqs: set[str] = field(default_factory=set)
    acs: set[str] = field(default_factory=set)
    vals: set[str] = field(default_factory=set)
    cons: set[str] = field(default_factory=set)
    raw_lines: list[str] = field(default_factory=list)
    # (heading, id) pairs found under a heading that didn't match any known
    # section category — these IDs were NOT added to reqs/acs/vals/cons.
    unclassified: list[tuple[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Plan document
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class PlanTask:
    """One ### TASK-NNN block from a plan file."""

    id: str  # e.g. "TASK-003"
    title: str  # text after the colon on the header line
    satisfies: set[str] = field(default_factory=set)  # IDs from Satisfies: line
    fields: dict[str, str] = field(default_factory=dict)  # other field→value pairs


@dataclass(slots=True)
class PlanDocument:
    """Parsed representation of a <name>.plan.md file."""

    tasks: list[PlanTask] = field(default_factory=list)
    phases: list[str] = field(default_factory=list)
    satisfied_ids: set[str] = field(default_factory=set)  # union of all satisfies sets
    raw_lines: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Shared regexes
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#+)\s+(?:\d+\.\s+)?(.+)$")
_IDS_RE = re.compile(r"\b((?:REQ|SEC|PERF|COMP|AC|VAL|CON)-\d+)\b")
_TASK_HEADER_RE = re.compile(r"^###\s+(TASK-\d+)(?::\s*(.*))?$")
_PHASE_HEADER_RE = re.compile(r"^##\s+(PHASE-\S+)")
_FIELD_RE = re.compile(
    r"^(Depends on|Files|Symbols|Action|Validate|Expected result|Satisfies)\s*:\s*(.*)"
)


# ---------------------------------------------------------------------------
# Spec parser
# ---------------------------------------------------------------------------


def parse_spec(path: str | Path) -> SpecDocument:
    """Parse a <name>.specs.md file.

    Returns:
        SpecDocument with sections, reqs, acs, vals, cons, raw_lines populated.

    Raises:
        FileNotFoundError: If the path doesn't exist.
        OSError: If the file cannot be read.
    """
    p = Path(path)
    content = p.read_text(encoding="utf-8")
    lines = content.splitlines()

    doc = SpecDocument(raw_lines=lines)
    current_section: str | None = None
    section_lines: list[str] = []

    def _flush_section() -> None:
        if current_section is not None:
            doc.sections[current_section] = "\n".join(section_lines).strip()

    def _add_unclass(sec: str, idx: str) -> None:
        pair = (sec, idx)
        if pair not in doc.unclassified:
            doc.unclassified.append(pair)

    for line in lines:
        if m := _HEADING_RE.match(line):
            _flush_section()
            current_section = m.group(2).strip()
            section_lines = []
        elif current_section is not None:
            section_lines.append(line)

        if current_section:
            sec_lower = current_section.lower()
            for match in _IDS_RE.finditer(line):
                id_str = match.group(1)
                if "requirements" in sec_lower:
                    if not (
                        id_str.startswith("AC-")
                        or id_str.startswith("VAL-")
                        or id_str.startswith("CON-")
                    ):
                        doc.reqs.add(id_str)
                    else:
                        _add_unclass(current_section, id_str)
                elif "constraints" in sec_lower:
                    if id_str.startswith("CON-"):
                        doc.cons.add(id_str)
                    else:
                        _add_unclass(current_section, id_str)
                elif "acceptance criteria" in sec_lower or "validation" in sec_lower:
                    if id_str.startswith("AC-"):
                        doc.acs.add(id_str)
                    elif id_str.startswith("VAL-"):
                        doc.vals.add(id_str)
                    else:
                        _add_unclass(current_section, id_str)
                else:
                    _add_unclass(current_section, id_str)

    _flush_section()
    return doc


# ---------------------------------------------------------------------------
# Plan parser
# ---------------------------------------------------------------------------

PLAN_MANDATORY_FIELDS: frozenset[str] = frozenset(
    {
        "Depends on",
        "Files",
        "Symbols",
        "Action",
        "Validate",
        "Expected result",
    }
)


def parse_plan(path: str | Path) -> PlanDocument:
    """Parse a <name>.plan.md file.

    Returns:
        PlanDocument with tasks (each carrying satisfies IDs), phases, and the
        union satisfied_ids set.

    Raises:
        FileNotFoundError: If the path doesn't exist.
        OSError: If the file cannot be read.
    """
    p = Path(path)
    content = p.read_text(encoding="utf-8")
    lines = content.splitlines()

    doc = PlanDocument(raw_lines=lines)
    current_task: PlanTask | None = None
    current_field: str | None = None

    for line in lines:
        # Phase headers
        if pm := _PHASE_HEADER_RE.match(line):
            if current_task is not None:
                doc.tasks.append(current_task)
            doc.phases.append(pm.group(1))
            current_task = None
            current_field = None
            continue

        # Task headers
        if tm := _TASK_HEADER_RE.match(line):
            if current_task is not None:
                doc.tasks.append(current_task)
            task_id = tm.group(1)
            title = (tm.group(2) or "").strip()
            current_task = PlanTask(id=task_id, title=title)
            current_field = None
            continue

        if current_task is None:
            continue

        # Field lines
        if fm := _FIELD_RE.match(line):
            field_name = fm.group(1)
            field_value = fm.group(2).strip()
            current_field = field_name
            if field_name == "Satisfies":
                ids = {m.group(1) for m in _IDS_RE.finditer(field_value)}
                current_task.satisfies |= ids
                doc.satisfied_ids |= ids
            else:
                current_task.fields[field_name] = field_value
        else:
            if current_field is not None:
                if current_field == "Satisfies":
                    stripped = line.strip()
                    if stripped:
                        ids = {m.group(1) for m in _IDS_RE.finditer(stripped)}
                        current_task.satisfies |= ids
                        doc.satisfied_ids |= ids
                else:
                    existing = current_task.fields.get(current_field, "")
                    current_task.fields[current_field] = existing + "\n" + line

    if current_task is not None:
        doc.tasks.append(current_task)

    # Strip whitespace/newlines from all parsed task fields
    for task in doc.tasks:
        for k, v in task.fields.items():
            task.fields[k] = v.strip()

    return doc
