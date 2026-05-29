#!/usr/bin/env python3
"""
Heuristic model-tier advisor for agent.md files.
Usage: python scripts/recommend.py <agent.md> [--json]
Exit: always 0 (advisory tool)
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_parser import parse_agent, ParseError
from lib.heuristics import score_complexity, score_to_tier, has_shell_tool

_TIER_MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-7",
}


def recommend(spec) -> dict:
    score, reasons = score_complexity(spec)
    tier = score_to_tier(score, spec)

    current_tier = next((k for k in _TIER_MODELS if k in spec.model.lower()), None)
    drift = None
    if current_tier and current_tier != tier:
        drift = (
            f"Your config uses {spec.model} ({current_tier}) but heuristic "
            f"suggests {tier}. Review if intentional."
        )

    return {
        "recommended_tier": tier,
        "recommended_model": _TIER_MODELS[tier],
        "score": score,
        "reasons": reasons,
        "has_shell_tool": has_shell_tool(spec),
        "current_model": spec.model,
        "drift_notice": drift,
    }


def render_human_rec(r: dict) -> str:
    lines = [
        "=== Model recommendation ===",
        f"  Recommended: {r['recommended_tier'].upper()} ({r['recommended_model']})",
        f"  Score:       {r['score']}",
        "",
        "  Reasoning trail:",
    ]
    if r["reasons"]:
        for reason in r["reasons"]:
            lines.append(f"    {reason}")
    else:
        lines.append("    (no signals fired -- trivially simple agent)")

    if r["has_shell_tool"]:
        lines.append("    [override] shell-class tool detected -- minimum Sonnet")

    if r["drift_notice"]:
        lines += ["", f"  !! Drift: {r['drift_notice']}"]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Heuristic model-tier advisor for agent.md files."
    )
    parser.add_argument("agent_file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        spec = parse_agent(args.agent_file)
    except (FileNotFoundError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    result = recommend(spec)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_human_rec(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
