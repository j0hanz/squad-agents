#!/usr/bin/env python3
"""
Heuristic cost-per-run estimator for agent.md files.
Usage: python scripts/cost.py <agent.md> [--runs N] [--output-tokens K] [--json]
Exit: always 0 (advisory tool)
See references/pricing.md for methodology.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_parser import parse_agent, ParseError
from lib.heuristics import estimate_input_tokens, estimate_tokens, TOOL_SCHEMA_TOKENS
from lib.pricing import cost_usd, PRICING_DATE, PRICING_URL

_SMELL_INPUT_THRESHOLD = 10_000
_SMELL_COST_THRESHOLD = 5.00


def estimate_cost(spec, runs: int = 3, output_tokens: int = 500) -> dict:
    input_tokens = estimate_input_tokens(spec)
    prompt_tokens = estimate_tokens(spec.system_prompt)
    tool_tokens = len(spec.tools) * TOOL_SCHEMA_TOKENS
    run_cost, is_fallback = cost_usd(input_tokens, output_tokens, spec.model)
    suite_cost = run_cost * runs

    smells = []
    if input_tokens > _SMELL_INPUT_THRESHOLD:
        smells.append(
            f"Input > {_SMELL_INPUT_THRESHOLD:,} tokens -- consider trimming system prompt "
            f"or tool count."
        )
    if suite_cost > _SMELL_COST_THRESHOLD:
        smells.append(
            f"Projected suite cost ${suite_cost:.2f} > ${_SMELL_COST_THRESHOLD:.2f} -- "
            f"consider a cheaper model tier for initial eval runs."
        )
    if spec.skills:
        smells.append(
            f"Skill bodies not counted ({len(spec.skills)} skill(s)) -- "
            f"actual cost will be higher when skills load."
        )

    return {
        "model": spec.model,
        "is_fallback_pricing": is_fallback,
        "pricing_date": PRICING_DATE,
        "pricing_url": PRICING_URL,
        "prompt_tokens": prompt_tokens,
        "tool_tokens": tool_tokens,
        "total_input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_per_run_usd": round(run_cost, 6),
        "runs": runs,
        "suite_cost_usd": round(suite_cost, 6),
        "smells": smells,
    }


def render_human_cost(r: dict) -> str:
    tool_count = r["tool_tokens"] // 150 if r["tool_tokens"] else 0
    lines = [
        f"=== Cost estimate: {r['model']} ===",
        f"  Pricing snapshot: {r['pricing_date']}  ({r['pricing_url']})",
    ]
    if r["is_fallback_pricing"]:
        lines.append("  !! Unrecognised model -- using Sonnet-tier fallback rates")
    lines += [
        "",
        f"  System prompt:   {r['prompt_tokens']:>8,} tokens (heuristic)",
        f"  Tool schemas:    {r['tool_tokens']:>8,} tokens ({tool_count} tool(s) x 150)",
        f"  Output budget:   {r['output_tokens']:>8,} tokens (per run)",
        "",
        f"  Cost per run:    ${r['cost_per_run_usd']:.4f}",
        f"  Suite ({r['runs']} runs):  ${r['suite_cost_usd']:.4f}",
        "",
    ]
    for smell in r["smells"]:
        lines.append(f"  !! {smell}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Heuristic cost estimator. See references/pricing.md for methodology."
    )
    parser.add_argument("agent_file")
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of eval runs to project (default: 3)",
    )
    parser.add_argument(
        "--output-tokens",
        type=int,
        default=500,
        help="Estimated output tokens per run (default: 500)",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        spec = parse_agent(args.agent_file)
    except (FileNotFoundError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    result = estimate_cost(spec, runs=args.runs, output_tokens=args.output_tokens)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_human_cost(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
