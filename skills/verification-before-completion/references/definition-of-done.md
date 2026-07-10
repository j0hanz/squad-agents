---
name: definition-of-done
description: Project-wide standing bar every task and dispatched lane must clear before counting as done.
type: reference
canonical: true
---

# Definition of Done (project-wide standing bar)

Per-task acceptance criteria answer "did we build the right thing?" for **one** task.
The Definition of Done (DoD) is the standing bar every task and lane must clear — it sits underneath acceptance criteria, not beside them.

A task is incomplete, and a lane's success is untrusted, until all items below hold.

## The bar

- [ ] **Tests green** — targeted tests + regression suite pass, with pasted runner output (exit code + counts). A claim without output is not evidence.
- [ ] **Build/types clean** — project build and type-check succeed with no new errors.
- [ ] **Lint clean** — no new warnings, unused imports, or unused variables introduced by the change.
- [ ] **No debug residue** — no `debugger`, `pdb`, `console.log`/`print` left for diagnosis, or stray `TODO`/`FIXME` added by this change.
- [ ] **Diff is intentional** — every changed line is explainable; no unrelated churn, no commented-out blocks.
- [ ] **Acceptance criteria met** — the task's own per-task criteria (from the plan) all pass.
- [ ] **Callers checked** — if a public interface changed, its call sites were traced and updated (no scope-blind verification).

## How skills use it

- **request-plan** — do not write per-task acceptance criteria that restate the DoD; assume the DoD as the floor and add only what's task-specific on top.
- **dispatch-agents** — a lane is mergeable only when its work clears this bar, independently verified (never on the agent's self-report).
- **verification-before-completion** — this bar is the Mandatory Checklist's source of truth.

If a project legitimately cannot meet an item (e.g. no test suite yet), that is a
**documented exception**, not a silent skip — name it in the report and route to the
skill that closes the gap (e.g. `test-driven-development`).
