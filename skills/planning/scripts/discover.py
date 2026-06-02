#!/usr/bin/env python3
"""discover.py — Repository discovery helper for implementation plans.

Scans the repository for files matching glob patterns and/or symbol
names (functions, classes, components, exports, routes, tests, …)
and prints Markdown reference links ready to paste into a plan.

Targets Python 3.10+. Zero runtime dependencies; uses only stdlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

VERSION = "1.0.0"
MAX_FILE_BYTES = 2_000_000

IGNORED_DIRS: frozenset[str] = frozenset(
    {
        "node_modules",
        "dist",
        "build",
        "out",
        ".nuxt",
        ".turbo",
        ".cache",
        ".venv",
        "venv",
        "__pycache__",
        "coverage",
        ".pytest_cache",
        "target",
        "bin",
        "obj",
    }
)

BINARY_EXT: frozenset[str] = frozenset(
    {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
        "ico",
        "pdf",
        "zip",
        "tar",
        "gz",
        "exe",
        "dll",
        "so",
        "dylib",
        "wasm",
        "woff",
        "woff2",
        "ttf",
        "otf",
        "mp3",
        "mp4",
        "mov",
        "avi",
        "wav",
        "ogg",
        "bin",
    }
)

# Heuristic declaration patterns for JS/TS, Python, Go, Rust, Java/C#/Kotlin.
DECL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?:export\s+(?:default\s+)?(?:async\s+)?)?(?:function|class|interface|type|enum)\s+([A-Za-z_$][\w$]*)"
    ),
    re.compile(r"\b(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*[:=]"),
    re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)", re.MULTILINE),
    re.compile(r"^\s*class\s+([A-Za-z_]\w*)", re.MULTILINE),
    re.compile(r"\bfunc\s+(?:\([^)]*\)\s+)?([A-Za-z_]\w*)"),
    re.compile(r"\btype\s+([A-Za-z_]\w*)\s+(?:struct|interface)"),
    re.compile(r"\bfn\s+([A-Za-z_]\w*)"),
    re.compile(r"\b(?:struct|enum|trait|impl)\s+([A-Za-z_]\w*)"),
    re.compile(
        r"\b(?:public|private|protected|internal|static|final|abstract)\s+[\w<>\[\],\s]*?\s+([A-Za-z_]\w*)\s*\("
    ),
]

HELP = """\
discover.py — Repository discovery helper for implementation plans.

Usage:
  python skills/planning/scripts/discover.py [options]

Options:
  --root <dir>      Repo root to scan (default: cwd)
  --files <globs>   Comma-separated file globs (e.g. "src/**/*.{ts,tsx},**/*.md")
  --names <list>    Comma-separated symbol names or /regex/ patterns
  --ext  <list>     Comma-separated extensions filter (e.g. "ts,tsx,js")
  --max  <n>        Max matches per category (default: 200)
  --json            Emit JSON instead of Markdown
  --no-lines        Omit line numbers from symbol links
  -h, --help        Show this help
  --version         Print version info and exit

Examples:
  python skills/planning/scripts/discover.py --files "src/**/*.ts" --names "parseConfig,UserService"
  python skills/planning/scripts/discover.py --names "/^use[A-Z]/" --ext ts,tsx
  python skills/planning/scripts/discover.py --files "plan/**/*.md" --json

Notes:
  - Zero dependencies; uses only Python stdlib.
  - Brace expansion is supported in --files patterns (e.g. **/*.{ts,tsx}).
  - Skips node_modules, dist, build, out, .nuxt, .venv, __pycache__, coverage,
    target, bin, obj, and all dot-directories (.git, .github, .vscode, ...).
  - Symbol detection is heuristic across JS/TS, Python, Go, Rust, Java/Kotlin/C#.
    Treat results as candidates.
  - Read-only: no filesystem writes.
"""


# ── CLI ──────────────────────────────────────────────────────────────────────


def split_list(s: str | None) -> list[str]:
    """Split comma-separated values, preserving commas inside brace groups."""
    if not s:
        return []
    out: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in s:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            token = "".join(buf).strip()
            if token:
                out.append(token)
            buf = []
        else:
            buf.append(ch)
    token = "".join(buf).strip()
    if token:
        out.append(token)
    return out


def compile_name_pattern(token: str) -> re.Pattern[str]:
    """Compile a name token to a regex. Accepts /pattern/flags or plain word.

    Supported flags: i (IGNORECASE), m (MULTILINE), s (DOTALL).
    Flags g, u, y are accepted but silently ignored (not supported by Python re).
    """
    m = re.match(r"^/(.+)/([gimsuy]*)$", token)
    if m:
        flags = 0
        flag_str = m.group(2)
        if "i" in flag_str:
            flags |= re.IGNORECASE
        if "m" in flag_str:
            flags |= re.MULTILINE
        if "s" in flag_str:
            flags |= re.DOTALL
        return re.compile(m.group(1), flags)
    return re.compile(rf"\b{re.escape(token)}\b")


def parse_cli_args(raw: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="discover.py", add_help=False)
    parser.add_argument("--root", default=None)
    parser.add_argument("--files", default=None)
    parser.add_argument("--names", default=None)
    parser.add_argument("--ext", default=None)
    parser.add_argument("--max", type=int, default=200)
    parser.add_argument("--json", action="store_true", dest="json_out")
    parser.add_argument("--no-lines", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("--version", action="store_true")
    return parser.parse_args(raw)


# ── Path / file filtering ─────────────────────────────────────────────────────


def expand_braces(pattern: str) -> list[str]:
    """Expand {a,b} brace groups into separate glob patterns.

    Note: nested braces are not supported — only the outermost {} pair is expanded.
    """
    start = pattern.find("{")
    if start == -1:
        return [pattern]
    end = pattern.find("}", start)
    if end == -1:
        return [pattern]
    prefix = pattern[:start]
    suffix = pattern[end + 1 :]
    result: list[str] = []
    for alt in pattern[start + 1 : end].split(","):
        result.extend(expand_braces(prefix + alt + suffix))
    return result


def _should_exclude_part(name: str) -> bool:
    return bool(name) and name != "." and (name in IGNORED_DIRS or name.startswith("."))


def should_exclude_rel(rel: Path) -> bool:
    return any(_should_exclude_part(part) for part in rel.parts)


def _walk_all(root: Path) -> Iterator[Path]:
    """Yield every file under root, pruning ignored and dot-directories."""
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            for entry in current.iterdir():
                if _should_exclude_part(entry.name):
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(entry)
                elif entry.is_file(follow_symlinks=False):
                    yield entry
        except PermissionError:
            continue


def walk_glob_files(
    root: Path,
    patterns: list[str],
    ext_filter: frozenset[str],
    max_bytes: float = float("inf"),
) -> Iterator[tuple[str, Path]]:
    """Yield (rel_posix, abs_path) for files matching glob patterns."""
    seen: set[str] = set()
    for pattern in patterns:
        for expanded in expand_braces(pattern):
            for match in root.glob(expanded):
                if not match.is_file(follow_symlinks=False):
                    continue
                rel = match.relative_to(root)
                if should_exclude_rel(rel):
                    continue
                rel_posix = rel.as_posix()
                if rel_posix in seen:
                    continue
                ext = match.suffix.lstrip(".").lower()
                if ext in BINARY_EXT:
                    continue
                if ext_filter and ext not in ext_filter:
                    continue
                try:
                    if match.stat().st_size > max_bytes:
                        continue
                except OSError:
                    continue
                seen.add(rel_posix)
                yield rel_posix, match


# ── Symbol detection ──────────────────────────────────────────────────────────


def find_decl_names_on_line(line: str) -> list[str]:
    names: list[str] = []
    for pattern in DECL_PATTERNS:
        for m in pattern.finditer(line):
            if m.group(1):
                names.append(m.group(1))
    return names


def find_symbols(
    content: str,
    name_patterns: list[re.Pattern[str]],
    file_path: str,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(content.splitlines()):
        matching = [p for p in name_patterns if p.search(line)]
        if not matching:
            continue
        decl_names = find_decl_names_on_line(line)
        if not decl_names:
            continue
        # Emit at most one hit per (file, line) regardless of how many patterns match
        if any(any(pat.search(n) for n in decl_names) for pat in matching):
            hits.append({"file": file_path, "line": i + 1, "match": line.strip()[:200]})
    return hits


def extract_name(line: str) -> str | None:
    names = find_decl_names_on_line(line)
    return names[0] if names else None


# ── Collection ────────────────────────────────────────────────────────────────


def collect_matched_files(
    root: Path,
    file_patterns: list[str],
    ext_filter: frozenset[str],
    max_results: int,
) -> list[str]:
    if not file_patterns:
        return []
    out: list[str] = []
    for rel, _ in walk_glob_files(root, file_patterns, ext_filter, MAX_FILE_BYTES):
        out.append(rel)
        if len(out) >= max_results:
            break
    return out


def collect_matched_symbols(
    root: Path,
    name_patterns: list[re.Pattern[str]],
    ext_filter: frozenset[str],
    max_results: int,
) -> list[dict[str, Any]]:
    if not name_patterns:
        return []
    out: list[dict[str, Any]] = []
    for abs_path in _walk_all(root):
        if len(out) >= max_results:
            break
        ext = abs_path.suffix.lstrip(".").lower()
        if ext in BINARY_EXT:
            continue
        if ext_filter and ext not in ext_filter:
            continue
        try:
            if abs_path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        rel_posix = abs_path.relative_to(root).as_posix()
        try:
            content = abs_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for hit in find_symbols(content, name_patterns, rel_posix):
            out.append(hit)
            if len(out) >= max_results:
                break
    return out


# ── Rendering ─────────────────────────────────────────────────────────────────


def render_markdown(
    matched_files: list[str],
    matched_symbols: list[dict[str, Any]],
    with_lines: bool,
) -> str:
    lines: list[str] = []
    for f in matched_files:
        lines.append(f"- [{f}]({f})")
    if matched_files:
        lines.append("")
    for s in matched_symbols:
        name = extract_name(s["match"]) or s["match"][:60]
        anchor = f"{s['file']}#L{s['line']}" if with_lines else s["file"]
        lines.append(f"- [{name}]({anchor}) — `{s['file']}:{s['line']}`")
    if matched_symbols:
        lines.append("")
    if not lines:
        lines.append("No matches.")
    return "\n".join(lines)


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> int:
    args = parse_cli_args(sys.argv[1:])

    if args.help:
        print(HELP, end="")
        return 0
    if args.version:
        print(f"discover.py {VERSION} (python {sys.version.split()[0]})")
        return 0

    root = Path(args.root) if args.root else Path.cwd()
    file_patterns = split_list(args.files)
    names = split_list(args.names)
    ext_filter = frozenset(e.lstrip(".").lower() for e in split_list(args.ext))
    max_results = args.max if args.max > 0 else 200
    with_lines = not args.no_lines

    if not file_patterns and not names:
        print(
            "Provide at least one of --files or --names. Use --help for usage.",
            file=sys.stderr,
        )
        return 2

    name_patterns = [compile_name_pattern(n) for n in names]
    matched_files = collect_matched_files(root, file_patterns, ext_filter, max_results)
    matched_symbols = collect_matched_symbols(
        root, name_patterns, ext_filter, max_results
    )

    matched_files.sort()
    matched_symbols.sort(key=lambda s: (s["file"], s["line"]))

    if args.json_out:
        print(
            json.dumps({"files": matched_files, "symbols": matched_symbols}, indent=2)
        )
        return 0

    print(render_markdown(matched_files, matched_symbols, with_lines), end="")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"discover.py: {e}", file=sys.stderr)
        sys.exit(1)
