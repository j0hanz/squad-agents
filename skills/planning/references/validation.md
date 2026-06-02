# Validation Guide

Run `validate.py` after authoring each artifact and after every `sync.py` run.

```bash
python <skill-dir>/scripts/validate.py <name>              # all three checks
python <skill-dir>/scripts/validate.py <name> --spec       # spec only
python <skill-dir>/scripts/validate.py <name> --plan       # plan only
python <skill-dir>/scripts/validate.py <name> --cross      # coverage matrix only
```

`<name>` can be a bare stem (`auth-jwt`) or a full path to either artifact.

## What each mode checks

### `--spec`

- All mandatory sections present for the chosen depth (sketch/contract/blueprint)
- Requirements are atomic (no "and" joining two obligations)
- Requirements use active voice
- No vague adjectives (fast, robust, lightweight…) without numeric threshold
- REQs have corresponding ACs; ACs have corresponding VALs

### `--plan`

- Every task has all six mandatory fields: `Depends on`, `Files`, `Symbols`, `Action`, `Validate`, `Expected result`
- `Files` and `Symbols` are markdown links `[name](path#L42)`, not bare paths
- `Validate` field contains a backtick-wrapped command
- Warning when `Satisfies:` is missing (traceability spine not set)

### `--cross`

See [traceability.md](traceability.md) for full details. In brief:

- Every `REQ/SEC/PERF/COMP` ID covered by ≥1 task
- Every `Satisfies:` ID exists in the spec
- Every `AC-###` mapped to a task (warning if not)

## Exit codes

- `0` — all selected checks pass
- `1` — at least one ERROR found (warnings do not affect exit code)

## Fixing common errors

| Error                                   | Fix                                                                             |
| --------------------------------------- | ------------------------------------------------------------------------------- |
| `Missing mandatory section: Interfaces` | Add the section; include at least one introductory sentence before sub-headings |
| `REQ-002 missing fields: Action`        | Fill the empty field in the task block                                          |
| `bare path — use markdown links`        | Replace `src/auth.ts` with `[src/auth.ts](src/auth.ts)`                         |
| `Uncovered requirement: REQ-003`        | Re-run `sync.py` to add the missing stub, then author it                        |
| `Orphan task satisfies 'REQ-999'`       | The ID doesn't exist in the spec — fix the typo or remove the Satisfies entry   |

## UNVERIFIED markers

`sync.py` emits `[UNVERIFIED](UNVERIFIED)` in task `Files:` fields. Before the plan is ready for execution, replace each `UNVERIFIED` with a real path from `discover.py` output, or document why the path is not yet resolvable (e.g., "new file created by TASK-001").

## Quality gate checklist

Before marking a plan ready for execution:

- [ ] `validate.py --spec` — 0 errors
- [ ] `validate.py --plan` — 0 errors, 0 bare-path warnings
- [ ] `validate.py --cross` — 0 errors, coverage matrix complete
- [ ] All `UNVERIFIED` markers resolved or documented
- [ ] Reviewer agent returns `ready_for_execution: true`
