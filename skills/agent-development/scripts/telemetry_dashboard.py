#!/usr/bin/env python3
"""
telemetry_dashboard.py
Visualizes the telemetry metrics emitted by the Subagent Telemetry Pipeline pattern.
Reads `.claude/telemetry.jsonl` and prints a summary to the console.
"""

import json
import os
import sys
from collections import defaultdict

TELEMETRY_FILE = ".claude/telemetry.jsonl"


def main():
    if not os.path.exists(TELEMETRY_FILE):
        print(f"Error: Telemetry file {TELEMETRY_FILE} not found.")
        print("Run an agent with the Subagent Telemetry Pipeline hooks first.")
        sys.exit(1)

    print("--- Subagent Telemetry Dashboard ---")
    print(f"Reading from: {TELEMETRY_FILE}\n")

    events_by_subagent = defaultdict(list)
    total_events = 0

    with open(TELEMETRY_FILE, "r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                subagent_type = event.get("subagent_type", "unknown")
                events_by_subagent[subagent_type].append(event)
                total_events += 1
            except json.JSONDecodeError:
                continue

    if total_events == 0:
        print("No valid telemetry events found.")
        sys.exit(0)

    print(f"Total events recorded: {total_events}")
    print(f"Unique subagent types: {len(events_by_subagent)}\n")

    for subagent_type, events in events_by_subagent.items():
        print(f"Subagent Type: [{subagent_type}]")
        print(f"  Total Invocations: {len(events)}")

        # Calculate avg prompt length if start events exist
        start_events = [e for e in events if e.get("event") == "start"]
        if start_events:
            avg_prompt = sum(int(e.get("prompt_len", 0)) for e in start_events) / len(
                start_events
            )
            print(f"  Avg Prompt Length: {avg_prompt:.0f} chars")
        else:
            print("  Avg Prompt Length: N/A")

        print()


if __name__ == "__main__":
    main()
