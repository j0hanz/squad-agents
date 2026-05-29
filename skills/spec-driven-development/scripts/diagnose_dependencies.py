#!/usr/bin/env python3
"""
Diagnose missing SDD prerequisites and provide setup guidance.
Exit code: 0 if all present, 1 if any missing.
"""

import subprocess
import sys
from pathlib import Path


def check_command(cmd):
    """Check if a command exists in PATH or as a file."""
    try:
        subprocess.run(cmd, capture_output=True, check=True, shell=True, timeout=5)
        return True, None
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as e:
        return False, str(e)


def check_file(path):
    """Check if a file exists."""
    return Path(path).exists()


# Define prerequisites
PREREQUISITES = {
    "create-specs skill": {
        "check": lambda: check_file("../create-specs/SKILL.md"),
        "fix": "Contact workspace admin or verify create-specs is installed in ../create-specs/",
    },
    "create-plan skill": {
        "check": lambda: check_file("../create-plan/SKILL.md"),
        "fix": "Contact workspace admin or verify create-plan is installed in ../create-plan/",
    },
    "validate_spec.py": {
        "check": lambda: (
            check_file("tools/validate_spec.py")
            or check_command("python validate_spec.py --help")[0]
        ),
        "fix": "Run: python tools/setup.py",
    },
    "validate_plan.py": {
        "check": lambda: (
            check_file("tools/validate_plan.py")
            or check_command("python validate_plan.py --help")[0]
        ),
        "fix": "Run: python tools/setup.py",
    },
    "generate_plan.py": {
        "check": lambda: (
            check_file("tools/generate_plan.py")
            or check_command("python generate_plan.py --help")[0]
        ),
        "fix": "Run: python tools/setup.py",
    },
    "discover.mjs": {
        "check": lambda: (
            check_file("tools/discover.mjs")
            or check_command("node tools/discover.mjs --help")[0]
        ),
        "fix": "Run: npm run setup",
    },
}


def main():
    all_ok = True
    print("=" * 70)
    print("Spec-Driven Development: Dependency Diagnostic")
    print("=" * 70)
    print()

    for name, spec in PREREQUISITES.items():
        try:
            present = spec["check"]()
        except Exception as e:
            present = False
            print(f"[✗ ERROR] {name}")
            print(f"          Could not check: {str(e)}")
            print()
            all_ok = False
            continue

        status = "✓ OK" if present else "✗ MISSING"
        print(f"[{status}] {name}")

        if not present:
            all_ok = False
            print(f"     Fix: {spec['fix']}")
        print()

    print("=" * 70)
    if all_ok:
        print("✓ All prerequisites present. Ready to use spec-driven-development.")
        print()
        return 0
    else:
        print("✗ Some prerequisites are missing. Fix them above, then retry.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
