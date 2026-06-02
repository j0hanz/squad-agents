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

# Bundled parser — no external deps; insert idempotently to avoid duplicates
_here = str(Path(__file__).parent)
if _here not in sys.path:
    sys.path.insert(0, _here)
from spec_parser import parse_spec, parse_plan, PlanTask, IMPL_PREFIXES  # noqa: E402


def _is_impl_id(id_str: str) -> bool:
    return any(id_str.startswith(p) for p in IMPL_PREFIXES)


def _task_stub(task_id: str, spec_id: str, depends_on: str) -> str:
    return (
        f"### {task_id}: Implement {spec_id}\n\n"
        f"Depends on: {depends_on}\n"
        f"Files: [UNVERIFIED](UNVERIFIED)\n"
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
    best = 0
    for t in existing_tasks:
        m = re.match(r"TASK-(\d+)", t.id)
        if m:
            best = max(best, int(m.group(1)))
    return best + 1


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

    impl_stubs: list[str] = []
    ac_stub: str | None = None
    prev_depends = plan.tasks[-1].id if plan and plan.tasks else "none"

    for spec_id in missing_impl:
        tid = f"TASK-{next_num:03}"
        impl_stubs.append(_task_stub(tid, spec_id, prev_depends))
        prev_depends = tid
        next_num += 1

    if not ac_covered and ac_ids:
        tid = f"TASK-{next_num:03}"
        ac_stub = _acceptance_stub(tid, ac_ids, prev_depends)

    if plan_exists:
        original = plan_path.read_text(encoding="utf-8")
        updated = original
        if impl_stubs:
            impl_text = "\n".join(impl_stubs) + "\n"
            if "## PHASE-END" in updated:
                updated = updated.replace("## PHASE-END", impl_text + "## PHASE-END", 1)
            else:
                updated = updated.rstrip() + "\n\n" + impl_text
        if ac_stub:
            if "## PHASE-END" in updated:
                parts = re.split(r"(## PHASE-END[^\n]*)", updated, maxsplit=1)
                if len(parts) == 3:
                    updated = parts[0] + parts[1] + "\n\n" + ac_stub + parts[2]
                else:
                    updated = updated.rstrip() + "\n\n" + ac_stub
            else:
                updated = updated.rstrip() + "\n\n" + ac_stub
        plan_path.write_text(updated, encoding="utf-8")
    else:
        feat_name = spec_path.stem.replace(".specs", "")
        goal_content = spec.sections.get(
            "Goal", "One sentence: what capability or outcome?"
        ).strip()
        if not goal_content:
            goal_content = "One sentence: what capability or outcome?"

        impl_text = "\n".join(impl_stubs) if impl_stubs else ""
        new_plan_content = (
            f"# {feat_name}\n\n"
            f"Spec: [{spec_path.name}]({spec_path.name})\n\n"
            f"## Goal\n\n"
            f"{goal_content}\n\n"
            f"## PHASE-001: Implementation\n\n"
        )
        if impl_text:
            new_plan_content += impl_text + "\n"
        else:
            new_plan_content += "[Run sync.py to populate stubs]\n\n"

        new_plan_content += "## PHASE-END: Acceptance\n"
        if ac_stub:
            new_plan_content += f"\n{ac_stub}"

        plan_path.write_text(new_plan_content, encoding="utf-8")

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
