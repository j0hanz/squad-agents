# Definition of Done (project-wide standing bar)

Per-task acceptance criteria answer "did we build the right thing?" for **one** task.
The Definition of Done is the **standing bar every task and every dispatched lane
clears before it counts as done** — it sits underneath acceptance criteria, not
beside them. Acceptance criteria change per task; the DoD does not.

A task is **not done**, and a lane's `VERDICT: SUCCESS` is **not trusted**, until
every item below holds. This is the single shared bar referenced by `request-plan`/`receive-plan`,
`multi-agent-development`, `multi-agent-dispatch`, and this skill — so each skill
stops re-stating its own partial copy.

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
- **multi-agent-development / multi-agent-dispatch** — a lane is mergeable only when its work clears this bar, independently verified (never on the agent's self-report).
- **verification-before-completion** — this bar is the Mandatory Checklist's source of truth.

If a project legitimately cannot meet an item (e.g. no test suite yet), that is a
**documented exception**, not a silent skip — name it in the report and route to the
skill that closes the gap (e.g. `test-driven-development`).
