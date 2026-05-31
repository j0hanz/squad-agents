#!/usr/bin/env python3
import re
import sys
import argparse
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))
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


def validate(spec) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Structural Checks
    mandatory_sections = [
        "Goal",
        "Requirements",
        "Constraints",
        "Interfaces",
        "Context",
        "Acceptance Criteria & Validation",
        "Examples & Edge Cases",
    ]
    # Notes & Risks is optional according to SKILL.md for Sketch/Contract, but good to check

    for section in mandatory_sections:
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

    # 3. Traceability Checks
    if spec.reqs:
        if not spec.acs:
            errors.append(
                "Requirements found but no Acceptance Criteria (AC-###) defined."
            )
        if not spec.vals:
            errors.append(
                "Requirements found but no Validation steps (VAL-###) defined."
            )

        # Check if every REQ is mentioned in AC/VAL (Basic mapping check)
        # Note: SKILL.md doesn't strictly require REQ-001 in AC-001,
        # but self-check says "At least one AC per core requirement".
        # We'll just check if the counts are reasonable for now.
        if len(spec.acs) < len(spec.reqs) * 0.5:  # Heuristic
            warnings.append(
                f"Low AC density: {len(spec.acs)} ACs for {len(spec.reqs)} Requirements."
            )

    # 4. Constraints
    if not spec.cons:
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
    args = parser.parse_args()

    try:
        spec = parse_spec(args.file)
        errors, warnings = validate(spec)
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error ({type(e).__name__}): {e}")
        sys.exit(1)

    print(f"Audit Results for: {args.file}\n")

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
