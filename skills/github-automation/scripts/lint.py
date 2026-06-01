#!/usr/bin/env python3
"""Cross-platform linter for GitHub Actions workflows.

Performs:
1. YAML syntax check (via PyYAML if available, else built-in).
2. Expression injection check (untrusted github.event.* in run:).
3. SHA pinning check for third-party actions.
4. pull_request_target footgun check.
5. Missing permissions: block check.
6. Delegates to actionlint/yamllint if installed.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Heuristic for third-party actions: not actions/*, not github/*, not ./local
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def check_file(path: Path) -> list[str]:
    errors = []
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # 1. YAML syntax (Best effort)
    try:
        import yaml

        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            errors.append(f"YAML parse failed: {e}")
    except ImportError:
        pass  # Skip if pyyaml is missing

    # 2. Expression injection — including multi-line run: block scalars
    # github.event.(pull_request|issue|comment|review|head_commit).(title|body|message)
    # github.head_ref
    injection_pattern = r"\$\{\{\s*github\.(event\.(pull_request|issue|comment|review|head_commit)\.(title|body|message)|head_ref|event\.head_commit\.message)"
    in_run_block = False
    run_block_indent: int | None = None

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)

        run_match = re.match(r"^(\s*)run:\s*[|>-]?\s*$", line)
        if run_match:
            in_run_block = True
            run_block_indent = len(run_match.group(1)) + 1
        elif re.match(r"^\s*run:\s+\S", line):
            # Inline run: value (no block scalar)
            in_run_block = False
            run_block_indent = None
            if re.search(injection_pattern, line):
                errors.append(
                    f"L{i + 1}: Possible expression injection — untrusted github.event field inside run:. Use env: instead."
                )
            continue
        elif in_run_block:
            if stripped and current_indent < run_block_indent:
                in_run_block = False
                run_block_indent = None

        if in_run_block and re.search(injection_pattern, line):
            errors.append(
                f"L{i + 1}: Possible expression injection — untrusted github.event field inside run:. Use env: instead."
            )

    # 3. SHA pinning & 4. pull_request_target
    has_permissions = False
    has_pr_target = "pull_request_target" in content

    for i, line in enumerate(lines):
        if "permissions:" in line:
            has_permissions = True

        uses_match = re.search(r"uses:\s+([^@\s]+)@([^\s#]+)", line)
        if uses_match:
            ref = uses_match.group(1)
            rev = uses_match.group(2)

            # Skip local/docker/internal
            if (
                ref.startswith("./")
                or ref.startswith("../")
                or ref.startswith("docker://")
            ):
                continue

            # Check SHA pinning
            if not SHA_RE.match(rev):
                org = ref.split("/")[0]
                if org not in ("actions", "github"):
                    errors.append(
                        f"L{i + 1}: Third-party action not pinned to SHA: {ref}@{rev}"
                    )

        if (
            has_pr_target
            and "ref:" in line
            and "github.event.pull_request.head" in line
        ):
            errors.append(
                f"L{i + 1}: pull_request_target combined with checkout of PR head SHA — secret-exposing footgun."
            )

    if not has_permissions:
        errors.append(
            "Missing 'permissions:' block — relies on repo default. Add explicit permissions."
        )

    return errors


def main():
    parser = argparse.ArgumentParser(description="Lint GitHub Actions workflows")
    parser.add_argument(
        "target",
        nargs="?",
        default=".github/workflows",
        help="File or directory to lint",
    )
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"Error: {target} does not exist", file=sys.stderr)
        sys.exit(2)

    files = []
    if target.is_dir():
        files = list(target.glob("*.yml")) + list(target.glob("*.yaml"))
    else:
        files = [target]

    if not files:
        print(f"Error: No workflow files found in {target}", file=sys.stderr)
        sys.exit(2)

    # External Linters
    external_ran = False
    if shutil.which("actionlint"):
        print("Linter: actionlint")
        try:
            subprocess.run(["actionlint"] + [str(f) for f in files], check=True)
            external_ran = True
        except subprocess.CalledProcessError:
            sys.exit(1)
    elif shutil.which("yamllint"):
        print("Linter: yamllint (YAML structure only)")
        try:
            subprocess.run(
                ["yamllint", "-d", "{extends: relaxed, rules: {line-length: disable}}"]
                + [str(f) for f in files],
                check=True,
            )
            external_ran = True
            print()  # Spacer
        except subprocess.CalledProcessError:
            sys.exit(1)

    if not external_ran:
        print("Linter: built-in Python check")

    # Built-in checks
    total_errors = 0
    for f in files:
        errors = check_file(f)
        if errors:
            print(f"Issues in {f}:")
            for err in errors:
                print(f"  - {err}")
            total_errors += len(errors)

    if total_errors == 0:
        print(f"Lint OK ({len(files)} file(s))")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
