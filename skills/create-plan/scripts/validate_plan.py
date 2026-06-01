#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path


def validate_plan(plan_path: str | Path) -> tuple[list[str], list[str]]:
    content = Path(plan_path).read_text(encoding="utf-8")
    lines = content.splitlines()

    errors = []
    warnings = []

    # 1. Check for Mandatory Task Structure
    task_headers = [line for line in lines if line.startswith("### TASK-")]
    if not task_headers:
        errors.append(
            "No tasks found in the plan. Tasks must start with '### TASK-###'."
        )

    # For each task, check fields
    current_task = None
    fields_found = set()
    mandatory_fields = {
        "Depends on",
        "Files",
        "Symbols",
        "Action",
        "Validate",
        "Expected result",
    }

    for line in lines:
        if line.startswith("### TASK-"):
            if current_task:
                missing = mandatory_fields - fields_found
                if missing:
                    errors.append(
                        f"Task {current_task} is missing fields: {', '.join(missing)}"
                    )

            current_task = line.split(":")[0].strip()
            fields_found = set()
            continue

        if current_task:
            for field in mandatory_fields:
                if line.startswith(f"{field}:"):
                    fields_found.add(field)

                    # Check for markdown links in Files/Symbols
                    if field in ["Files", "Symbols"]:
                        if (
                            "[" not in line
                            and "]" not in line
                            and "none" not in line.lower()
                        ):
                            errors.append(
                                f"Task {current_task} field '{field}' contains bare paths. Use markdown links."
                            )

                    # Check for prose in Validate
                    if (
                        field == "Validate"
                        and "none" not in line.lower()
                        and "`" not in line
                    ):
                        warnings.append(
                            f"Task {current_task} 'Validate' field should contain a command in backticks."
                        )

    # Final task check
    if current_task:
        missing = mandatory_fields - fields_found
        if missing:
            errors.append(
                f"Task {current_task} is missing fields: {', '.join(missing)}"
            )

    # 2. Global Anti-Patterns
    if "|" in content and "--|" in content:
        warnings.append("Plan contains markdown tables. SKILL.md advises against them.")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an implementation plan.")
    parser.add_argument("plan", help="Path to the plan.md file")
    args = parser.parse_args()

    try:
        errors, warnings = validate_plan(args.plan)
    except FileNotFoundError:
        print(f"Error: Plan file {args.plan} not found.")
        sys.exit(1)

    print(f"Plan Audit Results for: {args.plan}\n")

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  [!] {w}")
        print()

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  [X] {e}")
        print("\nPlan is INVALID.")
        sys.exit(1)
    else:
        print("Plan is VALID.")
        sys.exit(0)


if __name__ == "__main__":
    main()
