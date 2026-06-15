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
import ast
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class FileSignal:
    path: str
    last_commit: str = ""
    has_tests: bool = False
    test_file: str = ""


@dataclass
class ScanResult:
    feature_area: str
    related_files: list[FileSignal] = field(default_factory=list)
    terminology: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    design_docs: list[str] = field(default_factory=list)
    analogous_features: list[str] = field(default_factory=list)
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

# Adjacent synonyms for common domain verbs/nouns used in analogous feature detection
_SYNONYM_MAP: dict[str, list[str]] = {
    "search": ["query", "lookup", "filter", "find"],
    "query": ["search", "filter", "lookup", "fetch"],
    "filter": ["search", "query", "sort", "paginate"],
    "import": ["upload", "ingest", "load", "parse"],
    "export": ["download", "serialize", "dump", "emit"],
    "auth": ["login", "session", "token", "credential", "permission"],
    "user": ["account", "profile", "member", "identity"],
    "notify": ["alert", "email", "webhook", "event", "message"],
    "cache": ["store", "memoize", "persist", "ttl"],
    "log": ["audit", "trace", "event", "record"],
    "report": ["export", "summary", "aggregate", "dashboard"],
    "sync": ["push", "pull", "replicate", "merge"],
    "schedule": ["cron", "job", "task", "queue"],
    "upload": ["import", "ingest", "attach", "store"],
    "download": ["export", "fetch", "stream", "serve"],
}

# Regex patterns for extracting named types from non-Python source files
_LANG_TYPE_PATTERNS: dict[str, str] = {
    ".ts": r"(?:interface|type|class|enum)\s+(\w+)",
    ".tsx": r"(?:interface|type|class|enum)\s+(\w+)",
    ".go": r"type\s+(\w+)\s+(?:struct|interface)",
    ".rs": r"(?:struct|enum|trait|type)\s+(\w+)",
    ".java": r"(?:class|interface|enum)\s+(\w+)",
    ".cs": r"(?:class|interface|enum|record)\s+(\w+)",
    ".kt": r"(?:class|interface|object|data class)\s+(\w+)",
    ".swift": r"(?:class|struct|enum|protocol)\s+(\w+)",
}


def _is_skippable(path: Path) -> bool:
    return any(part in _SKIP_DIRS for part in path.parts)


def _expand_synonyms(nouns: list[str]) -> list[str]:
    """Return adjacent synonyms for well-known domain terms (deduped, originals first)."""
    expanded = list(nouns)
    seen = {n.lower() for n in nouns}
    for noun in nouns:
        for synonym in _SYNONYM_MAP.get(noun.lower(), []):
            if synonym not in seen:
                seen.add(synonym)
                expanded.append(synonym)
    return expanded


def _git_log(path: str, cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-5", "--", path],
            capture_output=True,
            text=True,
            cwd=str(cwd),
        )
    except FileNotFoundError:
        return "no history"
    if result.returncode != 0:
        return "no history"
    return result.stdout.strip() or "no history"


def _grep_files(pattern: str, cwd: Path) -> list[str]:
    """Return up to 5 file paths matching pattern (case-insensitive, ignores lock files)."""
    try:
        git_result = subprocess.run(
            ["git", "grep", "-ril", "-e", pattern],
            capture_output=True,
            text=True,
            cwd=str(cwd),
        )
        if git_result.returncode == 0:
            return [p for p in git_result.stdout.splitlines() if p][:5]
    except FileNotFoundError:
        pass

    # Fallback to rg
    try:
        rg_result = subprocess.run(
            [
                "rg",
                "--files-with-matches",
                "-i",
                "--glob",
                "!*.lock",
                "--glob",
                "!*.sum",
                "--",
                pattern,
                str(cwd),
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return []

    paths = [p for p in rg_result.stdout.splitlines() if p]
    normalized: list[str] = []
    for p in paths:
        try:
            normalized.append(str(Path(p).relative_to(cwd)))
        except ValueError:
            normalized.append(p)
    return normalized[:5]


def _find_doc_files(cwd: Path) -> list[str]:
    found: list[str] = []
    for pattern in _DOC_GLOBS:
        for p in cwd.glob(pattern):
            if not _is_skippable(p):
                found.append(str(p.relative_to(cwd)))
    return found[:5]


def _find_test_file(file_path: Path, cwd: Path) -> str:
    """Return the relative path of a test file for the given source file, or ''."""
    stem = file_path.stem
    suffix = file_path.suffix
    parent = file_path.parent

    candidates = [
        parent / f"test_{stem}{suffix}",
        parent / f"{stem}_test{suffix}",
        parent / f"{stem}.test{suffix}",
        parent / f"{stem}.spec{suffix}",
        cwd / "tests" / f"test_{stem}{suffix}",
        cwd / "test" / f"test_{stem}{suffix}",
        cwd / "__tests__" / f"{stem}.test{suffix}",
        cwd / "__tests__" / f"{stem}.spec{suffix}",
        cwd / "spec" / f"{stem}_spec{suffix}",
        cwd / "spec" / f"{stem}.spec{suffix}",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return str(candidate.relative_to(cwd))
            except ValueError:
                return str(candidate)
    return ""


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
    """Extract named types/classes from source files that match domain nouns.

    Uses Python AST for .py files; regex patterns for TypeScript, Go, Rust, and others.
    """
    suffix = file_path.suffix.lower()
    terms: list[str] = []

    if suffix == ".py":
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            return []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if any(noun in node.name.lower() for noun in nouns):
                    doc = ast.get_docstring(node)
                    entry = node.name + (f" — {doc[:80]}" if doc else "")
                    terms.append(entry)
        return terms[:5]

    pattern = _LANG_TYPE_PATTERNS.get(suffix)
    if not pattern:
        return []
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    for match in re.finditer(pattern, text):
        name = match.group(1)
        if any(noun in name.lower() for noun in nouns):
            terms.append(name)
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
        label = {"M": "L", "L": "XL"}.get(label, label)
    return label, f"{file_count} file(s) matched; boundary crossing: {crosses_boundary}"


def scan(nouns: list[str], cwd: Path) -> ScanResult:
    """Scan the codebase for context relevant to the given domain nouns.

    Returns a ScanResult with related files, terminology, constraints, design
    docs, analogous features, test coverage, scope estimate, and unknowns.
    """
    noun_set = {n.lower() for n in nouns}
    all_terms = _expand_synonyms(nouns)
    adjacent_nouns = all_terms[len(nouns) :]

    result = ScanResult(feature_area=" | ".join(nouns))

    # ── Phase 1: parallel grep + doc discovery ──────────────────────────────
    seen_paths: set[str] = set()
    adjacent_paths: set[str] = set()

    with ThreadPoolExecutor(max_workers=8) as pool:
        grep_futures = {pool.submit(_grep_files, noun, cwd): noun for noun in nouns}
        adjacent_futures = {
            pool.submit(_grep_files, noun, cwd): noun for noun in adjacent_nouns
        }
        doc_future = pool.submit(_find_doc_files, cwd)

        for fut in as_completed(grep_futures):
            for path_str in fut.result():
                if path_str not in seen_paths:
                    seen_paths.add(path_str)
                    result.related_files.append(FileSignal(path=path_str))

        for fut in as_completed(adjacent_futures):
            for path_str in fut.result():
                if path_str not in seen_paths and path_str not in adjacent_paths:
                    adjacent_paths.add(path_str)

        result.design_docs = doc_future.result()
        if not result.design_docs:
            result.unknowns.append("No glossary, ADR, or architecture docs found")

    # Cap to 5 most relevant files
    result.related_files = result.related_files[:5]

    # Record analogous features (files found only via adjacent synonyms)
    result.analogous_features = list(adjacent_paths)[:2]

    # ── Phase 2: parallel git log + constraints + term extraction + test files ──
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
        }
        test_futures = {
            pool.submit(_find_test_file, cwd / f.path, cwd): f
            for f in result.related_files
        }

        for fut in as_completed(log_futures):
            try:
                log_futures[fut].last_commit = fut.result()
            except Exception:
                log_futures[fut].last_commit = "no history"

        for fut in as_completed(constraint_futures):
            try:
                result.constraints.extend(fut.result())
            except Exception:
                pass

        for fut in as_completed(term_futures):
            try:
                result.terminology.extend(fut.result())
            except Exception:
                pass

        for fut in as_completed(test_futures):
            try:
                file_signal = test_futures[fut]
                test_path = fut.result()
                file_signal.has_tests = bool(test_path)
                file_signal.test_file = test_path
            except Exception:
                pass

    # ── Scope signal ─────────────────────────────────────────────────────────
    modules = {
        Path(f.path).parts[0]
        for f in result.related_files
        if len(Path(f.path).parts) > 1
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
    if result.related_files and not any(f.has_tests for f in result.related_files):
        result.unknowns.append(
            "No test files found for matched files — test coverage unknown"
        )

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

    cwd = args.cwd.resolve()
    if not cwd.is_dir():
        parser.error(f"--cwd path does not exist or is not a directory: {cwd}")
    result = scan(args.nouns, cwd)
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
