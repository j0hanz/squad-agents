#!/usr/bin/env python3
"""Observer hook for simulate.py — append hook input to JSONL, exit 0."""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


def main() -> None:
    """Read hook data from stdin and log it to a JSONL file."""
    try:
        data: Dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse stdin, we can't do much.
        # But we must not crash the hook runner, so we exit 0.
        sys.exit(0)

    run_id = os.environ.get("SIMULATE_RUN_ID", "default")
    out_dir_str = os.environ.get("SIMULATE_OUT_DIR", ".simulate/runs")

    out_dir = Path(out_dir_str) / run_id
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        log_file = out_dir / "tool-calls.jsonl"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except (OSError, PermissionError):
        # Fail silently to not disrupt the main Claude process
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
