#!/usr/bin/env python3
"""Recommend sibling skills to compose into an agent.

Usage:
  python scripts/recommend-skills.py <agent.md> [--skill-dirs <path>...] [--top-k 5] [--json]

Exit codes:
  0 — at least one high-confidence candidate found
  1 — no high-confidence matches (still emits empty candidates list)
  2 — invalid input (missing/unreadable agent file)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.skill_index import recommend_skills
from lib.frontmatter import parse_frontmatter


def _default_skill_dirs() -> list[Path]:
    out: list[Path] = []
    # workspace skills/ (relative to agent file)
    candidates = [
        Path.cwd() / "skills",
        Path.home() / ".claude" / "skills",
    ]
    plugins = Path.home() / ".claude" / "plugins"
    if plugins.exists():
        for p in plugins.glob("*/skills"):
            candidates.append(p)
    for c in candidates:
        if c.exists():
            out.append(c)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Recommend sibling skills for an agent.")
    p.add_argument("agent_file", help="Path to agent markdown file")
    p.add_argument("--skill-dirs", nargs="+", default=None, help="Directories to scan")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--include-disabled", action="store_true")
    p.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    args = p.parse_args(argv)

    agent_path = Path(args.agent_file)
    if not agent_path.exists():
        print(f"error: agent file not found: {agent_path}", file=sys.stderr)
        return 2
    try:
        text = agent_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"error: cannot read {agent_path}: {e}", file=sys.stderr)
        return 2

    fm, body = parse_frontmatter(text)
    agent_task = " ".join(
        filter(
            None,
            [
                str(fm.get("description", "")),
                body[:2000],
            ],
        )
    )

    skill_dirs = (
        [Path(d) for d in args.skill_dirs] if args.skill_dirs else _default_skill_dirs()
    )

    result = recommend_skills(
        agent_task=agent_task,
        skill_dirs=skill_dirs,
        top_k=args.top_k,
        include_disabled=args.include_disabled,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Agent task preview: {result['agent_task_preview']}")
        print()
        if not result["candidates"]:
            print("(no matching skills found)")
        else:
            print("Candidates (ranked):")
            for c in result["candidates"]:
                print(f"  - {c['skill']} (score {c['score']}) — {c['reason']}")
                print(f"    source: {c['source']}")
        print()
        print("Caveats:")
        for cav in result["caveats"]:
            print(f"  - {cav}")

    return 0 if result["candidates"] else 1


if __name__ == "__main__":
    sys.exit(main())
