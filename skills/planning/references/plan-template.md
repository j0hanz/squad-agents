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

## PHASE-000: Setup & Discovery

### TASK-000: Verify environment and discover files

Depends on: none
Files: none
Symbols: none
Satisfies: none
Action: Run `python <skill-dir>/scripts/discover.py --files "src/**/*"` to identify relevant files.
Validate: `python <skill-dir>/scripts/discover.py --files "src/**/*"`
Expected result: Non-empty list of verified files.

## PHASE-001: Core Implementation

### TASK-001: [Action title]

Depends on: [TASK-000](#task-000-verify-environment-and-discover-files)
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
- `Satisfies` is set by `sync.py` — do not type it by hand

## Depth profiles

| Depth       | Task count  | Format                                |
| ----------- | ----------- | ------------------------------------- |
| `sketch`    | 5–12 tasks  | Compact phases, lighter discovery     |
| `contract`  | 12–30 tasks | Full atomic tasks, verified paths     |
| `blueprint` | 20–50 tasks | Narrative runbook with rollback phase |

## Decomposition guidance

See [decomposition.md](decomposition.md) for task sizing heuristics and effort estimates.
