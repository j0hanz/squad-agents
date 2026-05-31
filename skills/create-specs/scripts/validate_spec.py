#!/usr/bin/env python3
import re
import sys
import argparse
from pathlib import Path

# Use bundled spec_parser — self-contained, no external lib dependency
sys.path.insert(0, str(Path(__file__).parent))
from spec_parser import parse_spec

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
    "sketch": [
        "Goal",
        "Requirements",
        "Interfaces",
    ],
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


def validate(spec, level: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Structural Checks
    for section in SECTIONS_BY_LEVEL[level]:
        if section not in spec.sections or not spec.sections[section]:
            errors.append(f"Missing mandatory section: {section}")

    # 2. Requirement Linter
    # Match only actual requirement statements (label at line start), not prose
    # references to requirement IDs that appear mid-line in analysis text.
    # Pattern: optional whitespace, dash, optional whitespace, optional backtick,
    # then the label (e.g. REQ-001, SEC-002), optional backtick, then a colon.
    _REQ_STMT_RE = re.compile(r"^\s*-\s*`?(REQ|SEC|PERF|COMP)-\d+`?\s*:")
    req_lines = [line for line in spec.raw_lines if _REQ_STMT_RE.match(line)]
    for line in req_lines:
        # Atomicity check
        if " and " in line.lower() and not contains_code_block(line):
            warnings.append(
                f"Requirement might not be atomic (contains 'and'): {line.strip()}"
            )

        # Active voice hint (very basic check)
        if "be " in line.lower() and (
            "ed " in line.lower() or line.lower().endswith("ed")
        ):
            warnings.append(f"Requirement might be in passive voice: {line.strip()}")

        # Vague adjectives
        for adj in VAGUE_ADJECTIVES:
            if adj in line.lower():
                warnings.append(
                    f"Requirement contains vague adjective '{adj}': {line.strip()}"
                )

    # 3. Traceability Checks (skip for sketch — ACs and VALs are optional)
    if spec.reqs and level != "sketch":
        if not spec.acs:
            errors.append(
                "Requirements found but no Acceptance Criteria (AC-###) defined."
            )
        if not spec.vals:
            errors.append(
                "Requirements found but no Validation steps (VAL-###) defined."
            )

        if len(spec.acs) < len(spec.reqs) * 0.5:  # Heuristic
            warnings.append(
                f"Low AC density: {len(spec.acs)} ACs for {len(spec.reqs)} Requirements."
            )

    # 4. Constraints (skip for sketch — CONs are optional)
    if level != "sketch" and not spec.cons:
        warnings.append(
            "No constraints (CON-###) defined. SKILL.md recommends defining what the solution does NOT do."
        )

    return errors, warnings


def contains_code_block(line: str) -> bool:
    return "`" in line


def main():
    parser = argparse.ArgumentParser(
        description="Validate a specification Markdown file."
    )
    parser.add_argument("file", help="Path to the spec.md file")
    parser.add_argument(
        "--level",
        choices=["sketch", "contract", "blueprint"],
        default="contract",
        help="Spec maturity level — controls which sections are mandatory (default: contract)",
    )
    args = parser.parse_args()

    try:
        spec = parse_spec(args.file)
        errors, warnings = validate(spec, args.level)
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error ({type(e).__name__}): {e}")
        sys.exit(1)

    print(f"Audit Results for: {args.file} [level={args.level}]\n")

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  [!] {w}")
        print()

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  [X] {e}")
        print("\nSpec is INVALID.")
        sys.exit(1)
    else:
        print("Spec is VALID.")
        sys.exit(0)


if __name__ == "__main__":
    main()
