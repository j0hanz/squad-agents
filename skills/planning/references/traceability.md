# Traceability Spine

The `Satisfies:` field is the link between spec requirements and plan tasks.

## How it works

Every plan task has a `Satisfies:` field listing one or more spec IDs:

```markdown
### TASK-003: Implement token signing

Depends on: TASK-002
Files: [src/auth/jwt.ts](src/auth/jwt.ts)
Symbols: [signToken](src/auth/jwt.ts#L24)
Satisfies: REQ-001, SEC-001
Action: Implement JWT signing using the configured secret and RS256 algorithm.
Validate: `npm test -- auth/jwt.test.ts`
Expected result: All 6 tests pass, 0 skipped.
```

`sync.py` sets `Satisfies:` automatically when generating stubs — you never type it by hand.

## The coverage matrix (`validate.py --cross`)

`validate.py --cross` loads both paired files and checks three things:

| Check                         | Rule                                                                                             | Error type                                                               |
| ----------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| **No uncovered requirements** | Every `REQ/SEC/PERF/COMP` ID from the spec must appear in at least one task's `Satisfies:` field | `[CROSS] Uncovered requirement: REQ-002`                                 |
| **No orphan tasks**           | Every ID in a `Satisfies:` field must exist in the spec                                          | `[CROSS] Orphan task: TASK-007 satisfies 'REQ-999' which is not in spec` |
| **AC coverage**               | Every `AC-###` from the spec should map to at least one task                                     | Warning: `[CROSS] AC-003 has no corresponding task`                      |

## Running the coverage check

```bash
python <skill-dir>/scripts/validate.py <name> --cross
```

Output includes a summary table:

```python
Coverage matrix:
  Requirements covered : 5/5
  ACs covered          : 3/3
  Orphan Satisfies IDs : 0
```

## What counts as "covered"

A requirement is covered if any task in the plan has that ID in its `Satisfies:` field. One task can satisfy multiple IDs; one ID can be satisfied by multiple tasks.

`CON-###` (constraints) and `VAL-###` (validation commands) are not checked for coverage — they are spec-internal.

## When spec changes after sync

If you add or rename requirements after running `sync.py`:

1. Edit the spec.
2. Re-run `python sync.py <name>.specs.md` — it will add stubs for new IDs only; existing tasks are untouched.
3. Re-run `validate.py --cross` to confirm coverage is clean.

Never manually edit the `Satisfies:` field of an existing task. Always let `sync.py` manage it.

## Why this matters

The spine turns "the plan should implement the requirements" from prose advice into a machine-checkable contract. A plan that passes `--cross` with zero errors provably covers every stated requirement.
