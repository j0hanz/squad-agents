#!/usr/bin/env python3
"""Pin every `uses: org/repo@<ref>` in a workflow (or directory of workflows) to a
full 40-char SHA, preserving the original ref as a trailing comment.

Resolves refs via `gh api` (preferred) or `git ls-remote` (fallback). Requires
network access. Idempotent: an already-SHA-pinned line is left untouched, and
the version-tag comment is updated only when missing.

Usage:
    python pin_actions.py .github/workflows/ci.yml
    python pin_actions.py .github/workflows/         # whole directory
    python pin_actions.py .github/workflows/ --dry-run

Skips:
    - Local actions (uses: ./...)
    - Docker actions (uses: docker://...)
    - Same-repo references (uses: ./.github/actions/foo)
    - Lines already pinned to a 40-char hex SHA
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Matches: optional leading whitespace, "uses:", spaces, the ref, optional comment.
# Captures: prefix (everything up to and including "uses: "), ref (org/repo@thing
# or ./local or docker://...), trailing (rest of line after the ref token).
USES_RE = re.compile(r"^(?P<prefix>\s*-?\s*uses:\s+)(?P<ref>\S+)(?P<trailing>.*)$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def is_skippable(ref: str) -> bool:
    if ref.startswith("./") or ref.startswith("../"):
        return True
    if ref.startswith("docker://"):
        return True
    if "@" not in ref:
        # No ref at all (e.g., `uses: foo`) — not valid syntax, leave alone.
        return True
    return False


def split_ref(ref: str) -> tuple[str, str, str]:
    """Split `org/repo@rev` or `org/repo/path@rev` into (repo, subpath, rev).

    repo is `org/repo`; subpath is `path` (may be empty); rev is the ref after `@`.
    """
    repo_and_path, _, rev = ref.partition("@")
    parts = repo_and_path.split("/", 2)
    if len(parts) < 2:
        return repo_and_path, "", rev
    repo = f"{parts[0]}/{parts[1]}"
    subpath = parts[2] if len(parts) == 3 else ""
    return repo, subpath, rev


def resolve_via_gh(repo: str, rev: str) -> str | None:
    if not shutil.which("gh"):
        return None
    try:
        # Refs API handles both branches and tags. Try tag first, then branch.
        for ref_kind in ("tags", "heads"):
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/git/refs/{ref_kind}/{rev}"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0 and '"sha"' in result.stdout:
                sha = _extract_sha(result.stdout)
                if sha:
                    # For annotated tags, the ref points at a tag object; dereference.
                    deref = subprocess.run(
                        ["gh", "api", f"repos/{repo}/git/tags/{sha}"],
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                    if deref.returncode == 0 and '"object"' in deref.stdout:
                        commit_sha = _extract_object_sha(deref.stdout)
                        if commit_sha:
                            return commit_sha
                    return sha
        # Fall back: maybe rev IS already a SHA prefix; resolve to full.
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits/{rev}"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return _extract_sha(result.stdout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return None


def resolve_via_ls_remote(repo: str, rev: str) -> str | None:
    if not shutil.which("git"):
        return None
    url = f"https://github.com/{repo}"
    try:
        result = subprocess.run(
            ["git", "ls-remote", url, rev, f"refs/tags/{rev}", f"refs/heads/{rev}"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return None
        # ls-remote may return multiple lines (tag + dereferenced tag with ^{}).
        # Prefer the dereferenced one for annotated tags.
        deref, plain = None, None
        for line in result.stdout.splitlines():
            sha, _, ref = line.partition("\t")
            if not SHA_RE.match(sha):
                continue
            if ref.endswith("^{}"):
                deref = sha
            else:
                plain = sha
        return deref or plain
    except (subprocess.TimeoutExpired, OSError):
        return None


def _extract_sha(json_text: str) -> str | None:
    m = re.search(r'"sha"\s*:\s*"([0-9a-f]{40})"', json_text)
    return m.group(1) if m else None


def _extract_object_sha(json_text: str) -> str | None:
    # `repos/.../git/tags/<sha>` returns {"object": {"sha": "..."}} for annotated tags.
    m = re.search(r'"object"\s*:\s*\{[^}]*"sha"\s*:\s*"([0-9a-f]{40})"', json_text)
    return m.group(1) if m else None


def resolve(repo: str, rev: str) -> str | None:
    return resolve_via_gh(repo, rev) or resolve_via_ls_remote(repo, rev)


def process_line(
    line: str, cache: dict[tuple[str, str], str]
) -> tuple[str, str | None]:
    """Return (new_line, status). status is one of: 'pinned', 'skipped', 'already', 'failed'."""
    m = USES_RE.match(line)
    if not m:
        return line, None
    ref = m.group("ref")
    trailing = m.group("trailing")
    prefix = m.group("prefix")
    if is_skippable(ref):
        return line, "skipped"

    repo, subpath, rev = split_ref(ref)
    if SHA_RE.match(rev):
        return line, "already"

    key = (repo, rev)
    sha = cache.get(key)
    if not sha:
        sha = resolve(repo, rev)
        if sha:
            cache[key] = sha
    if not sha:
        sys.stderr.write(f"  ! could not resolve {repo}@{rev}\n")
        return line, "failed"

    new_ref_path = f"{repo}/{subpath}" if subpath else repo
    new_ref = f"{new_ref_path}@{sha}"

    # Preserve existing trailing comment if it already has the version tag;
    # otherwise append ` # <rev>`. Trailing typically begins with optional spaces
    # and then `#` (or is empty).
    stripped = trailing.strip()
    if stripped.startswith("#"):
        # Already has a comment — keep it unless it has no version info.
        comment = stripped
    else:
        comment = f"# {rev}"
    new_line = f"{prefix}{new_ref} {comment}\n"
    return new_line, "pinned"


def process_file(
    path: Path, dry_run: bool, cache: dict[tuple[str, str], str]
) -> dict[str, int]:
    counts = {"pinned": 0, "skipped": 0, "already": 0, "failed": 0}
    original = path.read_text(encoding="utf-8").splitlines(keepends=True)
    updated: list[str] = []
    changed = False
    for line in original:
        new_line, status = process_line(line, cache)
        if status:
            counts[status] += 1
            if status == "pinned":
                changed = True
        updated.append(new_line)
    if changed and not dry_run:
        path.write_text("".join(updated), encoding="utf-8")
    return counts


def iter_workflow_files(target: Path):
    if target.is_file():
        yield target
        return
    if target.is_dir():
        for p in sorted(target.glob("*.yml")):
            yield p
        for p in sorted(target.glob("*.yaml")):
            yield p


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "target", type=Path, help="Workflow file or directory of workflows."
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="Print what would change; don't write."
    )
    args = ap.parse_args()

    if not args.target.exists():
        sys.stderr.write(f"error: {args.target} does not exist\n")
        return 2

    cache: dict[tuple[str, str], str] = {}
    totals = {"pinned": 0, "skipped": 0, "already": 0, "failed": 0}
    files = list(iter_workflow_files(args.target))
    if not files:
        sys.stderr.write(f"error: no .yml/.yaml files under {args.target}\n")
        return 2

    for f in files:
        counts = process_file(f, args.dry_run, cache)
        action = "would pin" if args.dry_run else "pinned"
        print(
            f"{f}: {action}={counts['pinned']} already={counts['already']} skipped={counts['skipped']} failed={counts['failed']}"
        )
        for k in totals:
            totals[k] += counts[k]

    print(
        f"\ntotal: pinned={totals['pinned']} already={totals['already']} skipped={totals['skipped']} failed={totals['failed']}"
    )
    return 1 if totals["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
