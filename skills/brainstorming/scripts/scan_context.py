#!/usr/bin/env python3
"""
Parallel codebase scanner for brainstorming Phase 1.

Replaces sequential Glob/Grep/git-log tool calls with one script invocation.
Returns a JSON Codebase Context Report on stdout.

Usage:
    python scan_context.py NOUN [NOUN ...] [--cwd PATH]

Example:
    python scan_context.py search catalog --cwd /path/to/project
"""

from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class FileSignal:
    path: str
    last_commit: str = ""


@dataclass
class ScanResult:
    feature_area: str
    related_files: list[FileSignal] = field(default_factory=list)
    terminology: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    design_docs: list[str] = field(default_factory=list)
    scope: str = "M"
    scope_reasoning: str = ""
    unknowns: list[str] = field(default_factory=list)


# Directories that are never useful to scan
_SKIP_DIRS = frozenset(
    {"venv", ".venv", "node_modules", "__pycache__", ".git", "dist", "build"}
)

_DOC_GLOBS = [
    "**/glossary.md",
    "**/CONTEXT.md",
    "**/ARCHITECTURE.md",
    "**/docs/adr/*.md",
    "**/decisions/*.md",
    "**/docs/design/*.md",
]
_CONSTRAINT_PATTERNS = ["TODO", "FIXME", "HACK", "rate.limit", "timeout", "max_size"]


def _is_skippable(path: Path) -> bool:
    return any(part in _SKIP_DIRS for part in path.parts)


def _git_log(path: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", "log", "--oneline", "-5", "--", path],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    return result.stdout.strip() or "no history"


def _grep_files(pattern: str, cwd: Path) -> list[str]:
    """Return up to 5 file paths matching pattern (case-insensitive, ignores lock files)."""
    result = subprocess.run(
        ["git", "grep", "-ril", "--", pattern],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    if result.returncode != 0:
        # Fallback to rg if available
        result = subprocess.run(
            [
                "rg",
                "--files-with-matches",
                "-i",
                pattern,
                str(cwd),
                "--glob",
                "!*.lock",
                "--glob",
                "!*.sum",
            ],
            capture_output=True,
            text=True,
        )
    return [p for p in result.stdout.splitlines() if p][:5]


def _find_doc_files(cwd: Path) -> list[str]:
    found: list[str] = []
    for pattern in _DOC_GLOBS:
        for p in cwd.glob(pattern):
            if not _is_skippable(p):
                found.append(str(p.relative_to(cwd)))
    return found[:5]


def _scan_constraints(file_path: Path) -> list[str]:
    """Scan a file for constraint signals (TODOs, rate limits, timeouts)."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    hits: list[str] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if any(pat.lower() in line.lower() for pat in _CONSTRAINT_PATTERNS):
            hits.append(f"{file_path.name}:{line_no}: {line.strip()[:120]}")
    return hits[:3]


def _extract_code_terms(file_path: Path, nouns: set[str]) -> list[str]:
    """Extract class/type names from source files that match domain nouns."""
    try:
        import ast

        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, OSError):
        return []
    terms: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if any(noun in node.name.lower() for noun in nouns):
                doc = ast.get_docstring(node)
                entry = node.name + (f" — {doc[:80]}" if doc else "")
                terms.append(entry)
    return terms[:5]


def _estimate_scope(file_count: int, crosses_boundary: bool) -> tuple[str, str]:
    if file_count <= 2:
        return "S", f"{file_count} file(s), isolated change"
    if file_count <= 5:
        label = "M"
    elif file_count <= 10:
        label = "L"
    else:
        label = "XL"
    if crosses_boundary:
        label = {"S": "M", "M": "L", "L": "XL"}.get(label, label)
    return label, f"{file_count} file(s) matched; boundary crossing: {crosses_boundary}"


def scan(nouns: list[str], cwd: Path) -> ScanResult:
    noun_set = {n.lower() for n in nouns}
    result = ScanResult(feature_area=" | ".join(nouns))

    # ── Phase 1: parallel grep + doc discovery ──────────────────────────────
    seen_paths: set[str] = set()

    with ThreadPoolExecutor(max_workers=8) as pool:
        grep_futures = {pool.submit(_grep_files, noun, cwd): noun for noun in nouns}
        doc_future = pool.submit(_find_doc_files, cwd)

        for fut in as_completed(grep_futures):
            for path_str in fut.result():
                if path_str not in seen_paths:
                    seen_paths.add(path_str)
                    result.related_files.append(FileSignal(path=path_str))

        result.design_docs = doc_future.result()
        if not result.design_docs:
            result.unknowns.append("No glossary, ADR, or architecture docs found")

    # Cap to 5 most relevant files
    result.related_files = result.related_files[:5]

    # ── Phase 2: parallel git log + constraint scan + term extraction ────────
    with ThreadPoolExecutor(max_workers=8) as pool:
        log_futures = {
            pool.submit(_git_log, f.path, cwd): f for f in result.related_files
        }
        constraint_futures = {
            pool.submit(_scan_constraints, cwd / f.path): f.path
            for f in result.related_files
        }
        term_futures = {
            pool.submit(_extract_code_terms, cwd / f.path, noun_set): f.path
            for f in result.related_files
            if (cwd / f.path).suffix == ".py"
        }

        for fut in as_completed(log_futures):
            log_futures[fut].last_commit = fut.result()

        for fut in as_completed(constraint_futures):
            result.constraints.extend(fut.result())

        for fut in as_completed(term_futures):
            result.terminology.extend(fut.result())

    # ── Scope signal ─────────────────────────────────────────────────────────
    modules = {
        Path(f.path).parts[0]
        for f in result.related_files
        if "/" in f.path or "\\" in f.path
    }
    crosses_boundary = len(modules) > 1
    result.scope, result.scope_reasoning = _estimate_scope(
        len(result.related_files), crosses_boundary
    )

    # ── Unknowns ──────────────────────────────────────────────────────────────
    if not result.terminology:
        result.unknowns.append("No typed definitions found for domain nouns")
    if not any(
        f.last_commit and f.last_commit != "no history" for f in result.related_files
    ):
        result.unknowns.append("No git history found for matched files")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parallel codebase scanner for brainstorming Phase 1"
    )
    parser.add_argument(
        "nouns", nargs="+", help="Domain nouns from the feature description"
    )
    parser.add_argument(
        "--cwd",
        default=".",
        type=Path,
        help="Project root (default: current directory)",
    )
    args = parser.parse_args()

    result = scan(args.nouns, args.cwd.resolve())
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
