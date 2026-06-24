# Plan Template

## File naming

`plan/<name>.plan.md` — stem must match the paired `<name>.specs.md`.

## Full structure

```markdown
# <name>

Spec: [<name>.specs.md](<name>.specs.md)

## Goal

[2-3 sentences: what this plan delivers and how it satisfies the spec]

## Current Context

[Relevant files, existing behavior, constraints from the spec]

## PHASE-001: Implementation

### TASK-001: [Action title]

Depends on: none
Files: [src/auth/jwt.ts](src/auth/jwt.ts)
Symbols: [signToken](src/auth/jwt.ts#L24)
Satisfies: REQ-001
Action: Single specific imperative action — one outcome only.
Validate: `npm test -- src/auth/jwt.test.ts`
Expected result: All 6 tests pass, 0 skipped.

## PHASE-END: Acceptance

### TASK-NNN: Final acceptance verification

Depends on: [TASK-NNN-1](#task-nnn-1-title)
Files: none
Symbols: none
Satisfies: AC-001, AC-002
Action: Verify all Acceptance Criteria from spec are observable in the running system.
Validate: `[VAL commands from spec]`
Expected result: All AC items confirmed observable.
```

Per-task `Validate:`/`Expected result:` are task-specific and sit **on top of** the
project-wide [Definition of Done](../../verification-before-completion/references/definition-of-done.md)
— the standing bar (tests/build/lint clean, no debug residue) every task clears
regardless. Do not restate the DoD in each task; assume it as the floor and add
only what's specific to the task.

## Canonical task block

Every task must have exactly these fields (in this order):

```markdown
Depends on: [TASK-NNN](#anchor) or none
Files: [path/to/file.ts](path/to/file.ts) or none
Symbols: [symbolName](path/to/file.ts#L42) or none
Satisfies: REQ-001 or none
Action: Single specific imperative implementation action.
Validate: `runnable shell command`
Expected result: Observable success signal.
```

**Rules:**

- `Files` and `Symbols` must be markdown links (never bare paths)
- `Validate` must be a backtick-wrapped runnable command
- `Action` must describe exactly one outcome (no "and")
- `Satisfies` is set by `cli.py sync` — do not type it by hand

## Discovery — filling Files:/Symbols: fields

Use Claude's native **Grep** and **Glob** tools to resolve file paths and code
symbols before writing `Files:`/`Symbols:` fields.

- Find files matching a pattern: Glob with pattern `src/**/*.ts` (or `src/**/*.{ts,tsx}`)
- Find a symbol by name: Grep with pattern `parseConfig`, `output_mode: "content"`, `-n: true` for line numbers
- Regex symbol search (e.g. all React hooks): Grep with pattern `^export (function|const) use[A-Z]`
- Combined search: run Glob to narrow files, then Grep within that scope

Grep/Glob return raw paths and line numbers — format them yourself as markdown
links before pasting into the fields:

```markdown
- [src/auth/jwt.ts](src/auth/jwt.ts)
- [signToken](src/auth/jwt.ts#L24) — `src/auth/jwt.ts:24`
- [validateToken](src/auth/jwt.ts#L41) — `src/auth/jwt.ts:41`
```

Rules:

1. Run discovery before writing task fields — never guess paths
2. Copy line anchors exactly as reported by Grep
3. For new files (not yet created): mark as `[UNVERIFIED: path/to/new-file.ts](UNVERIFIED)` and note which task creates it
4. For cross-repo paths discovery can't reach: mark as `[UNVERIFIED: path/to/file.ts](UNVERIFIED)` and document the assumption inline (which repo, why it's not discoverable here)

| Situation                    | Action                                            |
| ---------------------------- | ------------------------------------------------- |
| Pattern returns 0 results    | Simplify glob; check the directory exists         |
| Symbol not found             | Try broader pattern; verify the symbol name       |
| New file created during plan | Mark UNVERIFIED; resolve after creating task runs |
| Cross-repo path needed       | Mark UNVERIFIED; document the assumption inline   |

## Phase vs Task

**Phase** — a major work unit with one measurable goal. Groups related tasks.

**Task** — an atomic unit: one code change, one file modified, one clear observable outcome.

Prefer bounding a phase to one feature's vertical slice (the complete path through its layers) over one architectural layer spanning multiple features — slicing horizontally by layer hides integration gaps until the last phase.

## Task sizing

A well-sized task:

- Duration: 15–60 minutes for an experienced developer
- Files: touches 1–3 files max
- Outcome: one observable result (no "and")
- Dependencies: minimal coupling

**Split when:** more than 3 distinct changes in one file; tests for unrelated components; task description uses "and".

**Combine when:** single function, < 5 min; trivial boilerplate with no independent value.

## Phase structure

Good phases have one measurable goal and 3–8 tasks:

```markdown
## PHASE-001: Setup & Configuration

## PHASE-002: Core Implementation

## PHASE-003: Integration & Testing

## PHASE-END: Acceptance
```

This Setup → Core → Integration sequence is intra-slice sequencing for one feature, not a template for batching by layer across unrelated features (e.g. "all DB work, then all API work, then all UI work").

## Effort reference

| Task type                 | Complexity            | Base time |
| ------------------------- | --------------------- | --------- |
| New file (implementation) | Simple (< 50 LOC)     | 15–30 min |
| New file (utility/helper) | Medium (50–150 LOC)   | 30–60 min |
| New file (integration)    | Complex (150–300 LOC) | 60–90 min |
| Modify existing file      | Simple (1–20 changes) | 10–20 min |
| Modify existing file      | Complex (20+ changes) | 30–60 min |
| Test file (unit)          | Per 10 cases          | 20–30 min |
| Test file (integration)   | Per 5 cases           | 30–45 min |

**Multipliers:** unfamiliar framework ×1.3; complex architecture change ×1.5; first time in codebase ×1.2.

## Depth profiles

For depth definitions (task counts, effort, format), see **Depth Profiles** in `SKILL.md`.
