#!/usr/bin/env python3
"""validate.py — Unified validator for planning artifacts.

Modes (default: --spec --plan --cross):
  --spec   Validate <name>.specs.md structural integrity and traceability
  --plan   Validate <name>.plan.md task structure and markdown links
  --cross  Validate spec↔plan traceability coverage matrix
  --review Validate <name>.review.md exists with ready_for_execution: true

Usage:
    python validate.py <name>              # runs --spec --plan --cross
    python validate.py <name> --spec       # spec only
    python validate.py <name> --plan       # plan only
    python validate.py <name> --cross      # cross-check only
    python validate.py <name> --review     # review gate only

<name> can be:
  - a bare stem: validate.py auth-jwt  (looks for plan/auth-jwt.specs.md etc.)
  - a full path to either artifact: validate.py plan/auth-jwt.specs.md
    (strips suffix and dir to find both files)

Exit code: 0 = all selected checks pass, 1 = errors found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

# Bundled parser — no external deps; append to avoid shadowing stdlib modules
sys.path.append(str(Path(__file__).parent))
from spec_parser import parse_spec, parse_plan  # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VAGUE_ADJECTIVES = [
    "lightweight",
    "clean",
    "robust",
    "fast",
    "performant",
    "easy",
    "simple",
]

SECTIONS_BY_LEVEL: dict[str, list[str]] = {
    "sketch": ["Goal", "Requirements", "Interfaces"],
    "contract": [
        "Goal",
        "Requirements",
        "Constraints",
        "Interfaces",
        "Context",
        "Acceptance Criteria & Validation",
        "Examples & Edge Cases",
    ],
    "blueprint": [
        "Goal",
        "Requirements",
        "Constraints",
        "Interfaces",
        "Context",
        "Acceptance Criteria & Validation",
        "Examples & Edge Cases",
        "Notes & Risks",
    ],
}

_REQ_STMT_RE = re.compile(r"^[ ]{0,2}-\s+`?(REQ|SEC|PERF|COMP)-\d+`?[\s:]*")
_IMPL_PREFIXES = ("REQ-", "SEC-", "PERF-", "COMP-")

PLAN_MANDATORY_FIELDS = {
    "Depends on",
    "Files",
    "Symbols",
    "Action",
    "Validate",
    "Expected result",
}


# ---------------------------------------------------------------------------
# Spec validation
# ---------------------------------------------------------------------------


def _contains_code(line: str) -> bool:
    return "`" in line


def validate_spec(
    spec_path: Path, level: str = "contract"
) -> tuple[list[str], list[str]]:
    """Validate structural integrity and traceability of a <name>.specs.md file."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        spec = parse_spec(spec_path)
    except FileNotFoundError:
        return [f"Spec file not found: {spec_path}"], []

    # 1. Required sections
    for section in SECTIONS_BY_LEVEL[level]:
        if section not in spec.sections or not spec.sections[section]:
            errors.append(f"[SPEC] Missing mandatory section: {section}")

    # 2. Requirement linter
    req_lines = [line for line in spec.raw_lines if _REQ_STMT_RE.match(line)]
    for line in req_lines:
        if " and " in line.lower() and not _contains_code(line):
            warnings.append(
                f"[SPEC] Requirement may not be atomic (contains 'and'): {line.strip()}"
            )
        if "be " in line.lower() and (
            "ed " in line.lower() or line.lower().endswith("ed")
        ):
            warnings.append(f"[SPEC] Requirement may be passive voice: {line.strip()}")
        for adj in VAGUE_ADJECTIVES:
            if adj in line.lower():
                warnings.append(f"[SPEC] Vague adjective '{adj}' in: {line.strip()}")

    # 3. Traceability (skip for sketch)
    if spec.reqs and level != "sketch":
        if not spec.acs:
            errors.append(
                "[SPEC] Requirements found but no Acceptance Criteria (AC-###) defined."
            )
        if not spec.vals:
            errors.append(
                "[SPEC] Requirements found but no Validation steps (VAL-###) defined."
            )
        if len(spec.acs) < len(spec.reqs) * 0.5:
            warnings.append(
                f"[SPEC] Low AC density: {len(spec.acs)} ACs for {len(spec.reqs)} requirements."
            )

    # 4. Constraints
    if level != "sketch" and not spec.cons:
        warnings.append("[SPEC] No constraints (CON-###) defined.")

    return errors, warnings


# ---------------------------------------------------------------------------
# Plan validation
# ---------------------------------------------------------------------------


def validate_plan(plan_path: Path) -> tuple[list[str], list[str]]:
    """Validate structural integrity of a <name>.plan.md file."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        plan = parse_plan(plan_path)
    except FileNotFoundError:
        return [f"Plan file not found: {plan_path}"], []

    if not plan.tasks:
        errors.append("[PLAN] No tasks found. Tasks must start with '### TASK-###'.")
        return errors, warnings

    for task in plan.tasks:
        # Satisfies is recommended but not yet a hard error — warn until widely adopted
        missing = PLAN_MANDATORY_FIELDS - set(task.fields.keys())
        if not task.satisfies:
            warnings.append(
                f"[PLAN] {task.id}: missing Satisfies: field — traceability spine not set."
            )
        if missing:
            errors.append(
                f"[PLAN] {task.id}: missing mandatory fields: {', '.join(sorted(missing))}"
            )

        files_val = task.fields.get("Files", "")
        syms_val = task.fields.get("Symbols", "")
        for field_name, val in [("Files", files_val), ("Symbols", syms_val)]:
            if val and "none" not in val.lower() and "[" not in val:
                errors.append(
                    f"[PLAN] {task.id} '{field_name}': bare path — use markdown links."
                )

        validate_val = task.fields.get("Validate", "")
        if (
            validate_val
            and "none" not in validate_val.lower()
            and "`" not in validate_val
        ):
            warnings.append(
                f"[PLAN] {task.id} 'Validate': should contain a command in backticks."
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# Cross validation (coverage matrix)
# ---------------------------------------------------------------------------


def validate_cross(
    spec_path: Path, plan_path: Path, level: str = "contract"
) -> tuple[list[str], list[str], dict[str, Any]]:
    """Check spec↔plan traceability: every requirement covered, no orphan tasks."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        spec = parse_spec(spec_path)
    except FileNotFoundError:
        return [f"Spec file not found: {spec_path}"], [], {}

    try:
        plan = parse_plan(plan_path)
    except FileNotFoundError:
        return [f"Plan file not found: {plan_path}"], [], {}

    impl_ids = {
        id_ for id_ in spec.reqs if any(id_.startswith(p) for p in _IMPL_PREFIXES)
    }
    ac_ids = spec.acs

    # All IDs that appear in plan Satisfies fields
    all_satisfied: set[str] = set()
    for task in plan.tasks:
        all_satisfied |= task.satisfies

    # 1. Uncovered requirements — impl IDs in spec with no task covering them
    uncovered = impl_ids - all_satisfied
    for id_ in sorted(uncovered):
        errors.append(
            f"[CROSS] Uncovered requirement: {id_} has no task with Satisfies: {id_}"
        )

    # 2. Orphan tasks — task Satisfies IDs not in spec
    all_spec_ids = spec.reqs | spec.acs | spec.vals | spec.cons
    for task in plan.tasks:
        for sid in sorted(task.satisfies):
            if sid not in all_spec_ids:
                errors.append(
                    f"[CROSS] Orphan task: {task.id} satisfies '{sid}' which is not in spec."
                )

    # 3. AC coverage — ACs should be mapped to at least one task
    uncovered_acs = ac_ids - all_satisfied
    for ac in sorted(uncovered_acs):
        warnings.append(f"[CROSS] AC {ac} has no corresponding task in plan.")

    # Coverage matrix summary
    matrix = {
        "spec_impl_ids": sorted(impl_ids),
        "spec_ac_ids": sorted(ac_ids),
        "covered": sorted(impl_ids & all_satisfied),
        "uncovered": sorted(uncovered),
        "orphan_count": sum(
            1 for t in plan.tasks for sid in t.satisfies if sid not in all_spec_ids
        ),
        "ac_covered": sorted(ac_ids & all_satisfied),
        "ac_uncovered": sorted(uncovered_acs),
    }

    return errors, warnings, matrix


# ---------------------------------------------------------------------------
# Review validation (gates handoff)
# ---------------------------------------------------------------------------


def validate_review(spec_path: Path) -> tuple[list[str], list[str]]:
    """Check that review file exists and ready_for_execution is true."""
    errors: list[str] = []
    warnings: list[str] = []

    # Infer review path from spec path
    review_path = spec_path.parent / f"{spec_path.stem.replace('.specs', '')}.review.md"

    if not review_path.exists():
        errors.append(
            f"[REVIEW] Review file not found: {review_path}. Spawn agents/reviewer.md before handoff."
        )
        return errors, warnings

    try:
        content = review_path.read_text(encoding="utf-8")
    except OSError as e:
        errors.append(f"[REVIEW] Cannot read review file: {e}")
        return errors, warnings

    if (
        "ready_for_execution: true" not in content
        and "ready_for_execution:true" not in content
    ):
        errors.append(
            "[REVIEW] Field 'ready_for_execution: true' not found in review file. Reviewer must approve before handoff."
        )

    return errors, warnings


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _print_results(
    label: str,
    errors: list[str],
    warnings: list[str],
    matrix: dict | None = None,
) -> None:
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  [!] {w}")
    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  [X] {e}")
    if matrix:
        covered = len(matrix["covered"])
        total = len(matrix["spec_impl_ids"])
        ac_cov = len(matrix["ac_covered"])
        ac_total = len(matrix["spec_ac_ids"])
        print("\nCoverage matrix:")
        print(f"  Requirements covered : {covered}/{total}")
        print(f"  ACs covered          : {ac_cov}/{ac_total}")
        print(f"  Orphan Satisfies IDs : {matrix['orphan_count']}")
    status = "INVALID" if errors else "VALID"
    print(f"\n{label}: {status}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _resolve_paths(name_or_path: str) -> tuple[Path, Path]:
    """Resolve stem to (spec_path, plan_path) regardless of input form."""
    p = Path(name_or_path).resolve()
    stem = p.name
    for suf in (".specs.md", ".plan.md", ".md"):
        if stem.endswith(suf):
            stem = stem[: -len(suf)]
            break
    base = p.parent
    return base / f"{stem}.specs.md", base / f"{stem}.plan.md"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate planning artifacts (spec, plan, cross-check, or review gate)."
    )
    parser.add_argument(
        "name",
        help="Stem name or path to either artifact (e.g. 'plan/auth-jwt' or 'plan/auth-jwt.specs.md')",
    )
    parser.add_argument("--spec", action="store_true", help="Run spec validation only")
    parser.add_argument("--plan", action="store_true", help="Run plan validation only")
    parser.add_argument(
        "--cross", action="store_true", help="Run cross-coverage check only"
    )
    parser.add_argument(
        "--review", action="store_true", help="Run review gate check only"
    )
    parser.add_argument(
        "--level",
        choices=["sketch", "contract", "blueprint"],
        default="contract",
        help="Spec maturity level for --spec and --cross (default: contract)",
    )
    args = parser.parse_args()

    spec_path, plan_path = _resolve_paths(args.name)

    run_all = not (args.spec or args.plan or args.cross or args.review)
    run_spec = args.spec or run_all
    run_plan = args.plan or run_all
    run_cross = args.cross or run_all
    run_review = args.review

    all_errors: list[str] = []

    if run_spec:
        print(f"\n--- Spec: {spec_path} [level={args.level}] ---")
        errs, warns = validate_spec(spec_path, args.level)
        _print_results("Spec", errs, warns)
        all_errors.extend(errs)

    if run_plan:
        print(f"\n--- Plan: {plan_path} ---")
        errs, warns = validate_plan(plan_path)
        _print_results("Plan", errs, warns)
        all_errors.extend(errs)

    if run_cross:
        print(f"\n--- Cross: {spec_path.name} <-> {plan_path.name} ---")
        errs, warns, matrix = validate_cross(spec_path, plan_path, args.level)
        _print_results("Cross", errs, warns, matrix)
        all_errors.extend(errs)

    if run_review:
        print(f"\n--- Review: {spec_path.stem.replace('.specs', '')}.review.md ---")
        errs, warns = validate_review(spec_path)
        _print_results("Review", errs, warns)
        all_errors.extend(errs)

    if all_errors:
        print(f"\nTotal errors: {len(all_errors)} - INVALID")
        sys.exit(1)
    else:
        print("\nAll checks passed - VALID")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"validate.py: {e}", file=sys.stderr)
        sys.exit(1)
