#!/usr/bin/env python3
"""
Diagnose missing SDD prerequisites and provide setup guidance.
Exit code: 0 if all present, 1 if any missing.
"""

import subprocess
import sys
from pathlib import Path

# Resolve paths relative to the project root (two levels up from this script)
_SCRIPT_DIR = Path(__file__).parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent.parent
_SKILLS_DIR = _PROJECT_ROOT / "skills"


def check_command(cmd: str) -> tuple[bool, str | None]:
    """Check if a command exists in PATH or as a file."""
    try:
        # shell=False: commands are internal constants, not user input
        subprocess.run(cmd.split(), capture_output=True, check=True, timeout=5)
        return True, None
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as e:
        return False, str(e)


def check_file(path: str | Path) -> bool:
    """Check if a file exists."""
    return Path(path).exists()


# Define prerequisites
PREREQUISITES = {
    "planning skill": {
        "check": lambda: check_file(_SKILLS_DIR / "planning" / "SKILL.md"),
        "fix": "Verify planning is installed under skills/planning/",
    },
    "scaffold.py": {
        "check": lambda: check_file(
            _SKILLS_DIR / "planning" / "scripts" / "scaffold.py"
        ),
        "fix": "Verify planning skill is installed (contains scripts/scaffold.py)",
    },
    "sync.py": {
        "check": lambda: check_file(_SKILLS_DIR / "planning" / "scripts" / "sync.py"),
        "fix": "Verify planning skill is installed (contains scripts/sync.py)",
    },
    "validate.py": {
        "check": lambda: check_file(
            _SKILLS_DIR / "planning" / "scripts" / "validate.py"
        ),
        "fix": "Verify planning skill is installed (contains scripts/validate.py)",
    },
}


def main() -> int:
    all_ok = True
    print("=" * 70)
    print("Spec-Driven Development: Dependency Diagnostic")
    print("=" * 70)
    print()

    for name, spec in PREREQUISITES.items():
        try:
            present = spec["check"]()
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            present = False
            print(f"[ERROR] {name}")
            print(f"          Could not check: {e}")
            print()
            all_ok = False
            continue

        status = "OK" if present else "MISSING"
        print(f"[{status}] {name}")

        if not present:
            all_ok = False
            print(f"     Fix: {spec['fix']}")
        print()

    print("=" * 70)
    if all_ok:
        print("OK: All prerequisites present. Ready to use spec-driven-development.")
        print()
        return 0
    else:
        print("FAIL: Some prerequisites are missing. Fix them above, then retry.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
