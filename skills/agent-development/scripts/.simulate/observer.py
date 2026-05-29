#!/usr/bin/env python3
"""Observer hook for simulate.py — append hook input to JSONL, exit 0."""

import json
import os
import sys

data = json.load(sys.stdin)
run_id = os.environ.get("SIMULATE_RUN_ID", "default")
out_dir = os.environ.get("SIMULATE_OUT_DIR", ".simulate/runs")
os.makedirs(f"{out_dir}/{run_id}", exist_ok=True)
with open(f"{out_dir}/{run_id}/tool-calls.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(data) + "\n")
sys.exit(0)
