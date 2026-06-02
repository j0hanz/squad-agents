#!/usr/bin/env python3
"""sync.py — Sync spec requirements into plan task stubs (idempotent).

Reads <name>.specs.md, generates one TASK stub per REQ/SEC/PERF requirement
with Satisfies: pre-filled, and merges into the paired <name>.plan.md.

Idempotency: tasks whose Satisfies field already covers an ID are left
untouched. Only IDs with no existing coverage get new stubs appended.
A PHASE-END acceptance task is also created/updated from spec ACs.

Usage:
    python sync.py <name>.specs.md [--plan <name>.plan.md]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Bundled parser — no external deps; append to avoid shadowing stdlib modules
sys.path.append(str(Path(__file__).parent))
from spec_parser import parse_spec, parse_plan, PlanTask  # noqa: E402


# IDs we generate tasks for (not CON/AC/VAL — those don't need impl tasks)
_IMPL_PREFIXES = ("REQ-", "SEC-", "PERF-", "COMP-")


def _is_impl_id(id_str: str) -> bool:
    return any(id_str.startswith(p) for p in _IMPL_PREFIXES)


def _task_stub(task_id: str, spec_id: str, depends_on: str) -> str:
    return (
        f"### {task_id}: Implement {spec_id}\n\n"
        f"Depends on: {depends_on}\n"
        f"Files: UNVERIFIED\n"
        f"Symbols: none\n"
        f"Satisfies: {spec_id}\n"
        f"Action: [Implement the logic required by {spec_id} as specified in the spec]\n"
        f"Validate: `[UNVERIFIED command]`\n"
        f"Expected result: [Observable success signal for {spec_id}]\n"
    )


def _acceptance_stub(task_id: str, ac_ids: list[str], depends_on: str) -> str:
    ac_list = ", ".join(sorted(ac_ids)) if ac_ids else "none"
    return (
        f"### {task_id}: Final acceptance verification\n\n"
        f"Depends on: {depends_on}\n"
        f"Files: none\n"
        f"Symbols: none\n"
        f"Satisfies: {ac_list}\n"
        f"Action: Verify all Acceptance Criteria from spec are observable in the running system.\n"
        f"Validate: `[run VAL commands from spec]`\n"
        f"Expected result: All AC items confirmed observable.\n"
    )


def _next_task_number(existing_tasks: list[PlanTask]) -> int:
    nums = []
    for t in existing_tasks:
        m = re.match(r"TASK-(\d+)", t.id)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def sync(spec_path: Path, plan_path: Path) -> int:
    """Merge spec IDs into plan. Returns count of new stubs added."""
    spec = parse_spec(spec_path)
    impl_ids = sorted(id_ for id_ in spec.reqs if _is_impl_id(id_))
    ac_ids = sorted(spec.acs)

    plan_exists = plan_path.exists()
    plan = parse_plan(plan_path) if plan_exists else None

    # IDs already covered by existing tasks
    covered: set[str] = set()
    if plan:
        for task in plan.tasks:
            covered |= task.satisfies

    missing_impl = [id_ for id_ in impl_ids if id_ not in covered]
    ac_covered = bool(ac_ids) and all(a in covered for a in ac_ids)

    if not missing_impl and ac_covered:
        print(f"sync: nothing to add — all {len(impl_ids)} IDs already covered.")
        return 0

    # Determine last task id for depends-on chain
    next_num = _next_task_number(plan.tasks) if plan else 1

    new_blocks: list[str] = []
    prev_depends = plan.tasks[-1].id if plan and plan.tasks else "none"

    for spec_id in missing_impl:
        tid = f"TASK-{next_num:03}"
        new_blocks.append(_task_stub(tid, spec_id, prev_depends))
        prev_depends = tid
        next_num += 1

    if not ac_covered and ac_ids:
        tid = f"TASK-{next_num:03}"
        new_blocks.append(_acceptance_stub(tid, ac_ids, prev_depends))

    stubs_text = "\n".join(new_blocks)

    if plan_exists:
        original = plan_path.read_text(encoding="utf-8")
        # Insert before PHASE-END if it exists, otherwise append
        if "## PHASE-END" in original:
            updated = original.replace(
                "## PHASE-END",
                stubs_text + "\n## PHASE-END",
                1,
            )
        else:
            updated = original.rstrip() + "\n\n" + stubs_text
        plan_path.write_text(updated, encoding="utf-8")
    else:
        plan_path.write_text(
            f"# {spec_path.stem}\n\nSpec: [{spec_path.name}]({spec_path.name})\n\n"
            + stubs_text,
            encoding="utf-8",
        )

    added = len(missing_impl) + (0 if ac_covered else 1)
    print(f"sync: added {added} stub(s) to {plan_path}")
    return added


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync spec requirements into plan task stubs (idempotent)."
    )
    parser.add_argument("spec", help="Path to <name>.specs.md")
    parser.add_argument(
        "--plan",
        default=None,
        metavar="FILE",
        help="Path to <name>.plan.md (default: same dir/stem as spec)",
    )
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"sync.py: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    plan_path = (
        Path(args.plan)
        if args.plan
        else spec_path.parent / (spec_path.stem.replace(".specs", "") + ".plan.md")
    )

    sync(spec_path, plan_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"sync.py: {e}", file=sys.stderr)
        sys.exit(1)
