#!/usr/bin/env python3
"""Validate a Claude Code subagent definition (.claude/agents/*.md).

Dependency-free. Parses a minimal YAML-frontmatter subset and checks the
fields that cause silent misconfiguration: name format, required fields,
model value, tool/permission scoping, and an empty/aspirational body.

Usage:
    python validate_agent.py path/to/agent.md [more.md ...]

Exit code 0 = no errors (warnings allowed); 1 = at least one ERROR; 2 = usage/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FULL_MODEL_ID = re.compile(r"^claude-(opus|sonnet|haiku)-[0-9].*$")

MODEL_KEYWORDS = {"haiku", "sonnet", "opus", "inherit"}
PERMISSION_MODES = {
    "default",
    "plan",
    "acceptEdits",
    "auto",
    "dontAsk",
    "bypassPermissions",
}
EFFORT_LEVELS = {"low", "medium", "high", "xhigh", "max"}
# Tools a subagent can never use even if listed.
FORBIDDEN_TOOLS = {
    "AskUserQuestion",
    "EnterPlanMode",
    "ScheduleWakeup",
    "WaitForMcpServers",
}
# Capabilities that materially raise the blast radius — flagged for justification.
ESCALATION_TOOLS = {"Bash", "Write", "Edit", "NotebookEdit", "PowerShell", "computer"}
ASPIRATIONAL = re.compile(
    r"\b(you should|you might|you could|maybe|try to|if possible)\b", re.I
)


class Report:
    def __init__(self, path: str):
        self.path = path
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.infos: list[str] = []

    def error(self, code: str, msg: str) -> None:
        self.errors.append(f"{code}: {msg}")

    def warn(self, code: str, msg: str) -> None:
        self.warnings.append(f"{code}: {msg}")

    def info(self, code: str, msg: str) -> None:
        self.infos.append(f"{code}: {msg}")

    def print(self) -> None:
        status = "FAIL" if self.errors else ("WARN" if self.warnings else "OK")
        print(f"\n[{status}] {self.path}")
        for line in self.errors:
            print(f"  [ERROR] {line}")
        for line in self.warnings:
            print(f"  [WARN]  {line}")
        for line in self.infos:
            print(f"  [info]  {line}")


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_block, body). frontmatter is None if absent."""
    if not text.startswith("---"):
        return None, text
    # Find the closing --- on its own line.
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not m:
        return None, text
    return m.group(1), m.group(2)


def parse_frontmatter(block: str) -> dict[str, object]:
    """Minimal YAML subset: scalars, `key:` block scalars (| or >),
    inline `[a, b]` lists, and `- item` block lists."""
    data: dict[str, object] = {}
    lines = block.split("\n")
    i = 0
    key_re = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s?(.*)$")
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        m = key_re.match(raw)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        # A block-scalar indicator may carry a trailing inline comment.
        val_indicator = (
            val.split(" #", 1)[0].strip() if val[:1] not in ("'", '"') else val
        )
        if val_indicator in ("|", ">", "|-", ">-", "|+", ">+"):
            # Block scalar: gather more-indented following lines.
            collected, i = _gather_indented(lines, i + 1)
            data[key] = " ".join(s.strip() for s in collected).strip()
        elif val == "":
            # Possibly a block list (- item) following.
            items, ni = _gather_block_list(lines, i + 1)
            if items:
                data[key] = items
                i = ni
                continue
            data[key] = ""
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            data[key] = [_strip_scalar(x) for x in _split_csv(inner)] if inner else []
        else:
            data[key] = _strip_scalar(val)
        i += 1
    return data


def _gather_indented(lines: list[str], start: int) -> tuple[list[str], int]:
    out: list[str] = []
    i = start
    while i < len(lines):
        ln = lines[i]
        if ln.strip() == "":
            out.append("")
            i += 1
            continue
        if ln[:1] in (" ", "\t"):
            out.append(ln)
            i += 1
        else:
            break
    return out, i - 1


def _gather_block_list(lines: list[str], start: int) -> tuple[list[str], int]:
    out: list[str] = []
    i = start
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()
        if stripped.startswith("- "):
            out.append(_strip_scalar(stripped[2:]))
            i += 1
        elif stripped == "":
            i += 1
        else:
            break
    return out, i


def _split_csv(s: str) -> list[str]:
    """Split on commas at parenthesis-depth 0, so Agent(a, b) stays intact."""
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def _strip_scalar(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    # Drop trailing inline comment on unquoted scalars (YAML treats ' #' as a comment).
    hash_idx = s.find(" #")
    if hash_idx != -1:
        s = s[:hash_idx].strip()
    return s


def _tool_names(value: object) -> list[str]:
    """Extract bare tool names from a tools/disallowedTools value,
    stripping Agent(...) / Bash(...) argument parens."""
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = _split_csv(value)
    else:
        return []
    names = []
    for it in items:
        name = re.split(r"[(\s]", it.strip(), maxsplit=1)[0]
        if name:
            names.append(name)
    return names


def validate(path: Path) -> Report:
    rep = Report(str(path))
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        rep.error("IO", f"cannot read file: {e}")
        return rep

    block, body = split_frontmatter(text)
    if block is None:
        rep.error("FM001", "no YAML frontmatter found (file must start with '---').")
        return rep

    fm = parse_frontmatter(block)

    # --- name ---
    name = fm.get("name")
    if not name or not isinstance(name, str):
        rep.error("NAME001", "`name` is required.")
    else:
        if len(name) > 64:
            rep.error("NAME002", f"`name` exceeds 64 chars ({len(name)}).")
        if not KEBAB.match(name):
            rep.error(
                "NAME003",
                f"`name` must be kebab-case (lowercase, digits, single hyphens): got '{name}'.",
            )

    # --- description ---
    desc = fm.get("description")
    if not desc or not isinstance(desc, str):
        rep.error("DESC001", "`description` is required.")
    else:
        if len(desc) > 1024:
            rep.error("DESC002", f"`description` exceeds 1024 chars ({len(desc)}).")
        if "<" in desc or ">" in desc:
            rep.warn(
                "DESC003",
                "`description` contains angle brackets (< or >); some loaders reject these.",
            )
        if len(desc) < 30:
            rep.warn(
                "DESC004",
                "`description` is very short; make it pushy and concrete so the agent triggers reliably.",
            )

    # --- model ---
    model = fm.get("model")
    if isinstance(model, str) and model:
        if model not in MODEL_KEYWORDS and not FULL_MODEL_ID.match(model):
            rep.warn(
                "MODEL001",
                f"`model` value '{model}' is not a known keyword or model-ID pattern.",
            )

    # --- effort ---
    effort = fm.get("effort")
    if isinstance(effort, str) and effort and effort not in EFFORT_LEVELS:
        rep.error(
            "EFFORT001",
            f"`effort` must be one of {sorted(EFFORT_LEVELS)}; got '{effort}'.",
        )

    # --- permissionMode ---
    pmode = fm.get("permissionMode")
    if isinstance(pmode, str) and pmode:
        if pmode not in PERMISSION_MODES:
            rep.error(
                "PERM001",
                f"`permissionMode` must be one of {sorted(PERMISSION_MODES)}; got '{pmode}'.",
            )
        elif pmode == "bypassPermissions":
            rep.warn(
                "PERM002",
                "`permissionMode: bypassPermissions` removes all guardrails (allows writes to .git/.claude). Justify it.",
            )

    # --- isolation ---
    iso = fm.get("isolation")
    if isinstance(iso, str) and iso and iso != "worktree":
        rep.error("ISO001", f"`isolation` only supports 'worktree'; got '{iso}'.")

    # --- tools / disallowedTools ---
    tools = _tool_names(fm.get("tools")) if "tools" in fm else None
    if tools is not None:
        for t in tools:
            if t in FORBIDDEN_TOOLS:
                rep.warn(
                    "TOOL001",
                    f"tool '{t}' is unavailable to subagents and will be ignored.",
                )
        escal = sorted(set(tools) & ESCALATION_TOOLS)
        if escal:
            rep.info(
                "TOOL002",
                f"escalated tools granted ({', '.join(escal)}); confirm the job needs write/exec access.",
            )
    else:
        rep.warn(
            "TOOL003",
            "`tools` omitted — agent inherits ALL tools. Prefer an explicit least-privilege allowlist.",
        )

    disallowed = (
        _tool_names(fm.get("disallowedTools")) if "disallowedTools" in fm else []
    )
    if tools and disallowed:
        rep.info(
            "TOOL004",
            "both `tools` and `disallowedTools` set; `disallowedTools` is applied first.",
        )

    # --- body (system prompt) ---
    body_stripped = body.strip()
    if not body_stripped:
        rep.error("BODY001", "system prompt body is empty; the body IS the agent.")
    else:
        if len(body_stripped) < 80:
            rep.warn(
                "BODY002",
                "system prompt is very short; specify role, procedure, boundaries, and output contract.",
            )
        if ASPIRATIONAL.search(body_stripped):
            rep.warn(
                "BODY003",
                "aspirational phrasing detected ('you should'/'might'/'maybe'/'try to'); use imperative instructions.",
            )
        low = body_stripped.lower()
        if not any(k in low for k in ("output", "return", "report", "respond")):
            rep.warn(
                "BODY004",
                "no obvious output contract; the parent sees only the final message - define its shape.",
            )

    return rep


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Validate Claude Code subagent definition files."
    )
    ap.add_argument("paths", nargs="+", help="Path(s) to agent .md file(s).")
    args = ap.parse_args(argv)

    any_error = False
    for p in args.paths:
        rep = validate(Path(p))
        rep.print()
        any_error = any_error or bool(rep.errors)

    print()
    return 1 if any_error else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
