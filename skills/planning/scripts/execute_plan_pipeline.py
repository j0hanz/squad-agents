#!/usr/bin/env python3
"""execute_plan_pipeline.py — Run the validate -> sync -> validate -> cross-validate
pipeline for a scaffolded spec/plan pair.

Usage:
    python execute_plan_pipeline.py --name <name> [--dir plan]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_INVALID_NAME_CHARS = ("/", "\\", "\x00")


def _validate_name(name: str) -> None:
    if not name or name.startswith(".") or any(c in name for c in _INVALID_NAME_CHARS):
        raise ValueError(f"Invalid --name {name!r}: must be a plain filename stem")


def _run_step(label: str, scripts_dir: Path, script: str, *extra: str) -> None:
    print(f"[*] {label}...")
    res = subprocess.run([sys.executable, str(scripts_dir / script), *extra])
    if res.returncode != 0:
        print(f"\n[!] {label} failed.")
        sys.exit(res.returncode)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--dir", default="plan", metavar="DIR")
    args = parser.parse_args()
    name = args.name
    _validate_name(name)

    scripts_dir = Path(__file__).resolve().parent
    plan_dir = Path(args.dir).resolve()

    spec_path = plan_dir / f"{name}.specs.md"
    plan_path = plan_dir / f"{name}.plan.md"

    # Pre-flight: both artifacts must already exist (Step 2 scaffolds + authors them)
    for path_obj in (spec_path, plan_path):
        if not path_obj.exists():
            print(f"[!] {path_obj} not found. Run scaffold.py and author it first.")
            sys.exit(1)

    _run_step("Validating Spec", scripts_dir, "validate.py", str(spec_path), "--spec")
    _run_step("Syncing", scripts_dir, "sync.py", str(spec_path))
    _run_step("Validating Plan", scripts_dir, "validate.py", str(plan_path), "--plan")
    _run_step("Cross-Validating", scripts_dir, "validate.py", str(spec_path), "--cross")

    print("\n[+] Pipeline completed successfully. All validations passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"execute_plan_pipeline.py: {e}", file=sys.stderr)
        sys.exit(1)
