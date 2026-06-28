#!/usr/bin/env python3
"""project-init engine.

Deterministic core for the `project-init` skill. The skill fans out blind
read-only Researcher agents that emit *evidence-cited claims* (JSON); this
script is the SOLE writer of AGENTS.md and the stubs. It never executes any
discovered command — claims are data, not instructions.

Subcommands:
  prescan   walk the repo (bounded) -> packages + file count (drives serial vs fan-out)
  generate  verify+merge claims + survey answers -> render AGENTS.md
  wire      write one-line redirect stubs (CLAUDE.md / GEMINI.md)
  lint      validate an AGENTS.md against the hard format rules
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

MARKER_VERSION = "v1"
MAX_LINES = 100
MATCH_FILE_SIZE_CAP = 5 * 1024 * 1024  # don't scan blobs/binaries for a match string
PRESCAN_MAX_DEPTH = 2
PRESCAN_SKIP_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "dist",
    "build",
    "target",
    "Pods",
    ".next",
    "out",
}
MANIFEST_FILES = {
    "package.json",
    "pnpm-workspace.yaml",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "Gemfile",
    "*.csproj",
}

# ── Hard Rules text (carried verbatim from the old codebase-init engine) ──────
HARD_RULES_TEXT: dict[str, dict[str, str]] = {
    "commit": {
        "strict": "Conventional Commits format (`type(scope): subject`) required; every AI commit MUST include a `Co-Authored-By:` trailer",
        "relaxed": "free-form commit messages allowed; every AI commit MUST include a `Co-Authored-By:` trailer",
        "minimal": "no enforced message format, no required attribution trailer",
    },
    "maturity": {
        "production": "stability first — avoid breaking changes, prefer additive changes, flag breaking changes explicitly before making them",
        "development": "breaking changes are fine — never add fallback/legacy-compat shims, rewrite to the better approach directly",
    },
    "testing": {
        "always": "every change must have passing tests before being called done",
        "touched-files": "test/typecheck files you changed; don't require full-suite runs",
        "not-enforced": "no automatic testing requirement, rely on existing CI",
    },
    "ci": {
        "github-actions": "automated CI running on GitHub Actions",
        "gitlab-ci": "automated CI running on GitLab CI",
        "local-only": "no automated CI, local-only test execution and deployment",
    },
}

# ── Canonical key vocabulary (CLOSED) ────────────────────────────────────────
# This is the one piece that needs human judgment — too narrow drops real signal,
# too broad reverts the noise/budget problem. The balance:
#   - command buckets (cmd.*, file.*) are a CLOSED set + alias map, so two lanes
#     emitting `cmd.test` and `cmd.tests` collapse to one key instead of bloating.
#   - repo-specific buckets (dep.*, conv.*) keep an OPEN suffix but are COUNT-CAPPED
#     so they can't blow the line budget.
# To widen: add a task to CMD_KEYS/FILE_KEYS, or an alias to CMD_ALIASES.
FIXED_KEYS = {"purpose", "pm", "stack"}
CMD_KEYS = {
    "install",
    "build",
    "dev",
    "start",
    "run",
    "test",
    "lint",
    "format",
    "typecheck",
    "validate",
    "release",
}
FILE_KEYS = {"lint", "test", "typecheck", "format"}
# Common variants normalized to a canonical task so they don't fragment.
CMD_ALIASES = {
    "tests": "test",
    "unit": "test",
    "fmt": "format",
    "types": "typecheck",
    "tsc": "typecheck",
    "tc": "typecheck",
    "serve": "start",
    "watch": "dev",
    "compile": "build",
    "check": "validate",
    "setup": "install",
}
OPEN_PREFIXES = ("dep.", "conv.")
CAPS = {"conv.": 7, "dep.": 6}  # max lines per open bucket — protects the budget
_SUFFIX_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,31}$")


def normalize_key(raw_key: str) -> str | None:
    """Map a claimed key onto the canonical vocabulary, or None if out-of-vocab.

    cmd.*/file.* suffixes are aliased then validated against the closed task set;
    dep.*/conv.* suffixes are kept verbatim (sanitized). Everything else drops.
    """
    key = raw_key.strip()
    if key in FIXED_KEYS:
        return key
    if "." not in key:
        return None
    prefix, suffix = key.split(".", 1)
    prefix, suffix = prefix.strip().lower(), suffix.strip().lower()
    if prefix in ("cmd", "file"):
        suffix = CMD_ALIASES.get(suffix, suffix)
        allowed = CMD_KEYS if prefix == "cmd" else FILE_KEYS
        return f"{prefix}.{suffix}" if suffix in allowed else None
    if prefix in ("dep", "conv"):
        return f"{prefix}.{suffix}" if _SUFFIX_RE.match(suffix) else None
    return None


# Keys whose value is a runnable command / version string MUST cite a literal
# match, or the claim is dropped (anti-hallucination — the dangerous keys).
def match_required(key: str) -> bool:
    return key == "pm" or key.startswith(("cmd.", "file."))


# Protected from budget trimming (never silently dropped if a winner exists).
REQUIRED_KEYS = {"purpose", "pm", "cmd.build", "cmd.test"}
# Static priority — higher wins the <100-line budget.
PRIORITY = {
    "purpose": 100,
    "stack": 96,
    "pm": 95,
    "cmd.validate": 92,
    "cmd.build": 90,
    "cmd.test": 90,
    "cmd.install": 80,
    "cmd.dev": 75,
    "cmd.start": 74,
    "cmd.run": 73,
    "cmd.lint": 70,
    "cmd.typecheck": 70,
    "cmd.format": 65,
    "cmd.release": 60,
}
PREFIX_PRIORITY = {"cmd.": 60, "file.": 50, "conv.": 40, "dep.": 30}


def _priority(key: str) -> int:
    if key in PRIORITY:
        return PRIORITY[key]
    for pre, p in PREFIX_PRIORITY.items():
        if key.startswith(pre):
            return p
    return 0


def safe_print(text: str, file: IO[str] = sys.stdout) -> None:
    """Print, surviving consoles whose codec can't encode a character (Windows)."""
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        codec = getattr(file, "encoding", None) or "ascii"
        print(text.encode(codec, "replace").decode(codec), file=file)


# ── Evidence tier: derived deterministically from the cited path, never agent-set
_LOCKFILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "cargo.lock",
    "go.sum",
    "go.mod",
    "uv.lock",
    "poetry.lock",
    "gemfile.lock",
}
_CONFIG_HINTS = (
    "package.json",
    "pyproject.toml",
    "cargo.toml",
    "pom.xml",
    "build.gradle",
    "tsconfig.json",
    "biome.json",
    "ruff.toml",
    ".eslintrc",
    "makefile",
    "composer.json",
    ".csproj",
)


def evidence_tier(path: str) -> int:
    """4 = lockfile, 3 = manifest/config, 1 = prose/docs, 2 = anything else."""
    name = Path(path).name.lower()
    if name in _LOCKFILES:
        return 4
    if (
        any(h in name for h in _CONFIG_HINTS)
        or "/.github/workflows/" in path.replace("\\", "/").lower()
    ):
        return 3
    if name.endswith((".md", ".rst", ".txt")):
        return 1
    return 2


def _sanitize_value(value: str) -> str:
    """Collapse to one line; strip control chars. Prevents forged kv via newline
    or `key:` injection from untrusted repo content."""
    value = str(value).replace("\r", " ").replace("\n", " ")
    value = "".join(ch for ch in value if ch >= " " or ch == "\t")
    return value.strip()[:200]


@dataclass
class Evidence:
    path: str
    match: str | None = None


@dataclass
class Claim:
    key: str
    value: str
    tier: int
    confidence: float
    evidence: Evidence | None = None


def _read_text_safe(p: Path) -> str | None:
    """Read a small text file; None if missing, too big, or binary."""
    try:
        if not p.is_file() or p.stat().st_size > MATCH_FILE_SIZE_CAP:
            return None
        return p.read_text(encoding="utf-8-sig", errors="strict")
    except (OSError, UnicodeDecodeError):
        return None


def verify_claim(raw: dict[str, Any], root: Path) -> tuple[Claim | None, str]:
    """Validate one untrusted claim. Returns (Claim or None, reason-if-dropped)."""
    raw_key = str(raw.get("key", "")).strip()
    key = normalize_key(raw_key)
    if key is None:
        return None, f"out-of-vocab key: {raw_key!r}"

    value = _sanitize_value(raw.get("value", ""))
    if not value:
        return None, f"{key}: empty value"

    ev = raw.get("evidence") or {}
    ev_path = str(ev.get("path", "")).strip()
    match = ev.get("match")
    if not ev_path:
        return None, f"{key}: no evidence path"

    # Containment: resolve symlinks/.. then require inside repo root (read guard).
    # Normalize backslashes to forward slashes for cross-platform resolution
    is_abs = os.path.isabs(ev_path)
    norm_ev_path = ev_path.replace("\\", "/")
    resolved = (
        Path(norm_ev_path).resolve() if is_abs else (root / norm_ev_path).resolve()
    )
    if not resolved.is_relative_to(root):
        return None, f"{key}: evidence path escapes repo root: {ev_path}"

    text = _read_text_safe(resolved)
    if text is None:
        return None, f"{key}: evidence not a readable text file: {ev_path}"

    if match_required(key) and not match:
        return None, f"{key}: command/version key requires a literal evidence match"
    if match and str(match) not in text:
        return None, f"{key}: match {str(match)!r} not found in {ev_path}"

    try:
        confidence = float(raw.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    relative_path = resolved.relative_to(root).as_posix()
    return Claim(
        key,
        value,
        evidence_tier(ev_path),
        confidence,
        Evidence(path=relative_path, match=match),
    ), ""


def merge_claims(
    raws: list[dict[str, Any]], root: Path
) -> tuple[dict[str, Claim], list[str]]:
    """Verify all claims, keep one winner per key by (tier, confidence)."""
    winners: dict[str, Claim] = {}
    dropped: list[str] = []
    for raw in raws:
        claim, reason = verify_claim(raw, root)
        if claim is None:
            dropped.append(reason)
            continue
        cur = winners.get(claim.key)
        if cur is None or (claim.tier, claim.confidence) > (cur.tier, cur.confidence):
            if cur is not None:
                dropped.append(
                    f"{claim.key}: superseded (tier {cur.tier} -> {claim.tier})"
                )
            winners[claim.key] = claim

    # Cap the open buckets so repo-specific conventions/deps can't blow the budget.
    for prefix, limit in CAPS.items():
        keys = [k for k in winners if k.startswith(prefix)]
        if len(keys) <= limit:
            continue
        ranked = sorted(
            keys, key=lambda k: (winners[k].tier, winners[k].confidence), reverse=True
        )
        for k in ranked[limit:]:
            dropped.append(f"{k}: exceeded {prefix}* cap of {limit}")
            del winners[k]
    return winners, dropped


def render_agents_md(
    winners: dict[str, Claim],
    commit: str,
    maturity: str,
    testing: str,
    ci: str,
    model: str = "<Model Name>",
    package: str | None = None,
) -> str:
    """Assemble the markdown-kv AGENTS.md from verified winners + survey answers."""
    purpose = (
        winners["purpose"].value
        if "purpose" in winners
        else "<one sentence — what this repo does>"
    )

    pkg_normalized = package.strip().replace("\\", "/").rstrip("/") if package else None

    if pkg_normalized:
        lines = [f"# Agent Instructions: {pkg_normalized}", "", f"purpose: {purpose}"]
    else:
        lines = ["# Agent Instructions", "", f"purpose: {purpose}"]

    if "stack" in winners:
        lines.append(f"stack: {winners['stack'].value}")

    if pkg_normalized:
        lines += [
            "",
            f"<!-- project-init:package-scoped {pkg_normalized} -->",
        ]
    else:
        lines += [
            "",
            "## Hard Rules",
            "",
            f"commit: {HARD_RULES_TEXT['commit'][commit]}",
            f"maturity: {HARD_RULES_TEXT['maturity'][maturity]}",
            f"testing: {HARD_RULES_TEXT['testing'][testing]}",
            f"ci: {HARD_RULES_TEXT['ci'][ci]}",
            "",
            f"<!-- project-init:hard-rules {MARKER_VERSION} commit={commit} maturity={maturity} testing={testing} ci={ci} -->",
        ]

    def section(title: str, keys: list[str]) -> None:
        rows = [(k, winners[k].value) for k in keys if k in winners]
        if not rows:
            return
        lines.extend(["", f"## {title}", ""])
        for k, v in rows:
            label = k.split(".", 1)[1] if "." in k else k
            lines.append(f"{label}: {v}")

    cmd_keys = ["pm"] + sorted(k for k in winners if k.startswith("cmd."))
    section("Package Manager", cmd_keys)
    section("Dependency Locations", sorted(k for k in winners if k.startswith("dep.")))
    section("Key Conventions", sorted(k for k in winners if k.startswith("conv.")))

    file_keys = sorted(k for k in winners if k.startswith("file."))
    if file_keys:
        lines.extend(
            ["", "## File-Scoped Commands", "", "| Task | Command |", "| --- | --- |"]
        )
        for k in file_keys:
            lines.append(f"| {k.split('.', 1)[1]} | `{winners[k].value}` |")

    if not package:
        lines.extend(["", "## Commit Attribution", "", f"Co-Authored-By: {model}", ""])
    return "\n".join(lines)


def _trim_to_budget(
    winners: dict[str, Claim], package: str | None = None
) -> tuple[dict[str, Claim], list[str]]:
    """Drop lowest-priority non-required keys until the rendered file fits MAX_LINES.

    Returns (kept, dropped-reasons). The caller still lints; if required keys
    alone overflow, the lint FAILs loudly rather than silently truncating.
    """
    dropped: list[str] = []
    kept = dict(winners)
    # Render with placeholder survey values just to count lines.
    while True:
        body = render_agents_md(
            kept,
            "minimal",
            "development",
            "not-enforced",
            "local-only",
            package=package,
        )
        if len(body.splitlines()) <= MAX_LINES - 1:
            return kept, dropped
        candidates = [k for k in kept if k not in REQUIRED_KEYS]
        if not candidates:
            return kept, dropped  # only required keys left — let lint surface FAIL
        victim = min(candidates, key=_priority)
        del kept[victim]
        dropped.append(f"{victim}: trimmed to fit <{MAX_LINES}-line budget")


# ── Linter ───────────────────────────────────────────────────────────────────
_MARKER_RE = re.compile(
    r"<!--\s*project-init:hard-rules\s+v1\s+commit=\S+\s+maturity=\S+\s+testing=\S+\s+ci=\S+\s*-->"
)
_TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)
_FILLER_RE = re.compile(
    r"(welcome to|this document explains|you should|be sure to|make sure)",
    re.IGNORECASE,
)
_PKG_MARKER_RE = re.compile(r"<!--\s*project-init:package-scoped\s+(\S+)\s*-->")


def lint_agents_md(content: str) -> list[str]:
    """Return a list of FAIL messages; empty list == valid."""
    fails: list[str] = []
    lines = content.lstrip("\ufeff").splitlines()
    if len(lines) > MAX_LINES:
        fails.append(f"{len(lines)} lines exceeds the {MAX_LINES}-line budget")
    if not lines or not lines[0].startswith("# "):
        fails.append("must start with an H1 header")

    is_package_scoped = bool(re.search(r"<!--\s*project-init:package-scoped", content))

    if is_package_scoped:
        if not _PKG_MARKER_RE.search(content):
            fails.append("missing/malformed project-init:package-scoped marker")
    else:
        if "## Hard Rules" not in content:
            fails.append('missing "## Hard Rules" section')
        if not _MARKER_RE.search(content):
            fails.append("missing/malformed project-init:hard-rules v1 marker")
        if "Co-Authored-By:" not in content:
            fails.append('missing "Co-Authored-By:" attribution')
        if "## Commit Attribution" not in content:
            fails.append('missing "## Commit Attribution" section')

    if "<Model Name>" in content:
        fails.append('unresolved "<Model Name>" placeholder')

    in_code = False
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or s.startswith("<!--"):
            continue
        if _TODO_RE.search(line):
            fails.append(f'unresolved TODO (line {i}): "{s}"')
        if _FILLER_RE.search(line):
            fails.append(f'filler text (line {i}): "{s}"')
    return fails


def wire_stubs(source: Path, targets: list[Path]) -> int:
    """Write one-line redirect stubs pointing at *source*. Containment-guarded
    on every WRITE path. Never copies content."""
    root = Path.cwd().resolve()
    source = source.resolve()
    if not source.is_relative_to(root) or not source.exists():
        safe_print(
            f"FAIL: source missing or outside repo: {source.name}", file=sys.stderr
        )
        return 1
    rc = 0
    for target in targets:
        resolved = target.resolve()
        if not resolved.is_relative_to(root):
            safe_print(f"FAIL: target outside repo, skipped: {target}", file=sys.stderr)
            rc = 1
            continue
        if resolved == source:
            safe_print(
                f"FAIL: target equals source, skipped: {target}", file=sys.stderr
            )
            rc = 1
            continue
        try:
            if resolved.is_dir() and not resolved.is_symlink():
                raise IsADirectoryError(resolved)
            if resolved.exists() or resolved.is_symlink():
                resolved.unlink()
            rel = os.path.relpath(source, resolved.parent).replace(os.sep, "/")
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(
                f"# See [{source.name}]({rel})\n", encoding="utf-8", newline="\n"
            )
            safe_print(f"Stubbed: {resolved.name} -> {rel}")
        except (OSError, ValueError) as e:
            safe_print(f"FAIL: could not wire {target}: {e}", file=sys.stderr)
            rc = 1
    return rc


def prescan(root: Path) -> dict[str, Any]:
    """Bounded walk: count files and detect package dirs (manifest at depth <= 2)."""
    packages: list[str] = []
    file_count = 0
    manifest_globs = [m for m in MANIFEST_FILES if "*" in m]
    manifest_exact = {m for m in MANIFEST_FILES if "*" not in m}

    def walk(d: Path, depth: int) -> None:
        nonlocal file_count
        try:
            entries = list(d.iterdir())
        except OSError:
            return
        names = {e.name for e in entries if e.is_file()}
        has_manifest = bool(names & manifest_exact) or any(
            any(Path(n).match(g) for g in manifest_globs) for n in names
        )
        if has_manifest:
            rel = str(d.relative_to(root)).replace(os.sep, "/")
            packages.append(rel if rel != "." else ".")
        for e in entries:
            if e.is_file():
                file_count += 1
            elif (
                e.is_dir()
                and e.name not in PRESCAN_SKIP_DIRS
                and depth < PRESCAN_MAX_DEPTH
            ):
                walk(e, depth + 1)

    walk(root, 0)
    return {
        "packages": packages,
        "package_count": len(packages),
        "file_count": file_count,
        "is_monorepo": len(packages) >= 3,
        "has_manifest": len(packages) > 0,
    }


# ── Subcommands ───────────────────────────────────────────────────────────────
def _cmd_prescan(args: argparse.Namespace) -> int:
    root = (args.target_dir or Path.cwd()).resolve()
    safe_print(json.dumps(prescan(root), indent=2))
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    if args.package:
        pkg_path = (root / args.package).resolve()
        if not pkg_path.is_relative_to(root) or not pkg_path.is_dir():
            safe_print(
                f"FAIL: --package path does not exist or escapes repo root: {args.package}",
                file=sys.stderr,
            )
            return 1

    try:
        raws = json.loads(args.claims.read_text(encoding="utf-8"))
        if not isinstance(raws, list):
            raise ValueError("claims file must be a JSON array")
    except (OSError, ValueError, json.JSONDecodeError) as e:
        safe_print(f"FAIL: could not load claims: {e}", file=sys.stderr)
        return 1

    winners, dropped = merge_claims(raws, root)
    if args.purpose:
        winners["purpose"] = Claim("purpose", _sanitize_value(args.purpose), 4, 1.0)

    if args.package:
        pkg_prefix = args.package.strip().replace("\\", "/").rstrip("/") + "/"
        winners = {
            k: v
            for k, v in winners.items()
            if not v.evidence
            or v.evidence.path.replace("\\", "/").startswith(pkg_prefix)
        }

    winners, trimmed = _trim_to_budget(winners, package=args.package)
    dropped += trimmed

    content = render_agents_md(
        winners,
        args.commit,
        args.maturity,
        args.testing,
        args.ci,
        model=args.model or "<Model Name>",
        package=args.package,
    )
    fails = lint_agents_md(content)
    # Preview (no --out, no --model): the unresolved attribution placeholder is
    # expected — the skill substitutes it on the approved final write.
    if args.model is None and args.out is None:
        fails = [f for f in fails if "<Model Name>" not in f]

    # Side report (stderr) — what was discarded and why; the user is never blind.
    if dropped:
        safe_print("### Dropped / unverified claims", file=sys.stderr)
        for d in dropped:
            safe_print(f"  - {d}", file=sys.stderr)
    if fails:
        safe_print("FAIL: generated AGENTS.md failed lint:", file=sys.stderr)
        for f in fails:
            safe_print(f"  - {f}", file=sys.stderr)
        return 1

    if args.out:
        out = args.out.resolve()
        if not out.is_relative_to(root):
            safe_print(f"FAIL: --out escapes repo root: {args.out}", file=sys.stderr)
            return 1
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8", newline="\n")
        os.replace(tmp, out)  # atomic — a crash never leaves a half-written file
        safe_print(f"Wrote {out.relative_to(root)} ({len(content.splitlines())} lines)")
    else:
        safe_print(content)
    return 0


def _cmd_wire(args: argparse.Namespace) -> int:
    return wire_stubs(args.source, args.targets)


def _cmd_lint(args: argparse.Namespace) -> int:
    try:
        content = args.file_path.read_text(encoding="utf-8")
    except OSError as e:
        safe_print(f"FAIL: {e}", file=sys.stderr)
        return 1
    fails = lint_agents_md(content)
    for f in fails:
        safe_print(f"FAIL: {f}", file=sys.stderr)
    if not fails:
        safe_print("PASS: AGENTS.md is valid.")
    return 1 if fails else 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="project-init deterministic engine.")
    sub = p.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("prescan", help="Detect packages and size (bounded walk).")
    pre.add_argument("target_dir", type=Path, nargs="?", default=None)

    gen = sub.add_parser("generate", help="Verify+merge claims into AGENTS.md.")
    gen.add_argument("--claims", type=Path, required=True, help="JSON array of claims.")
    gen.add_argument(
        "--commit", required=True, choices=sorted(HARD_RULES_TEXT["commit"])
    )
    gen.add_argument(
        "--maturity", required=True, choices=sorted(HARD_RULES_TEXT["maturity"])
    )
    gen.add_argument(
        "--testing", required=True, choices=sorted(HARD_RULES_TEXT["testing"])
    )
    gen.add_argument("--ci", required=True, choices=sorted(HARD_RULES_TEXT["ci"]))
    gen.add_argument("--purpose", default=None)
    gen.add_argument(
        "--model", default=None, help="Active model name for the attribution trailer."
    )
    gen.add_argument(
        "--package",
        default=None,
        help="Relative path to package directory (e.g. 'packages/api').",
    )
    gen.add_argument("--out", type=Path, default=None)

    w = sub.add_parser("wire", help="Write one-line redirect stubs.")
    w.add_argument("source", type=Path)
    w.add_argument("targets", type=Path, nargs="+")

    lint = sub.add_parser("lint", help="Validate an AGENTS.md.")
    lint.add_argument("file_path", type=Path, nargs="?", default=Path("AGENTS.md"))
    return p


def main() -> int:
    args = _build_parser().parse_args()
    return {
        "prescan": _cmd_prescan,
        "generate": _cmd_generate,
        "wire": _cmd_wire,
        "lint": _cmd_lint,
    }[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
