# Spec Template & Self-Check

## File naming

`plan/<name>.specs.md` — stem must match the paired `<name>.plan.md`.

## The 8 sections

| #   | Section                          | Sketch   | Contract | Blueprint |
| --- | -------------------------------- | -------- | -------- | --------- |
| 1   | Goal                             | required | required | required  |
| 2   | Requirements                     | required | required | required  |
| 3   | Constraints                      | optional | required | required  |
| 4   | Interfaces                       | required | required | required  |
| 5   | Context                          | —        | required | required  |
| 6   | Acceptance Criteria & Validation | —        | required | required  |
| 7   | Examples & Edge Cases            | —        | required | required  |
| 8   | Notes & Risks                    | —        | —        | required  |

## ID prefixes

| Prefix     | Meaning                                               | Levels    |
| ---------- | ----------------------------------------------------- | --------- |
| `REQ-NNN`  | Functional requirement                                | All       |
| `SEC-NNN`  | Security / privacy requirement                        | All       |
| `PERF-NNN` | Performance requirement (must have numeric threshold) | All       |
| `COMP-NNN` | Compatibility / platform requirement                  | All       |
| `CON-NNN`  | Constraint (what the solution must NOT do)            | All       |
| `AC-NNN`   | Acceptance criterion (user-observable)                | All       |
| `VAL-NNN`  | Validation step (runnable verification command)       | All       |
| `RISK-NNN` | Risk with mitigation or "accepted"                    | Blueprint |
| `NOTE-NNN` | Rollout, migration, or rollback note                  | Blueprint |

`scaffold.py` places these IDs — never type them by hand.

## Self-check before handoff

Run `validate.py --spec` first, then use this checklist for what the validator cannot catch:

### Goal

- [ ] One sentence only. One measurable completion signal.
- [ ] No vague adjectives ("fast", "clean") without a numeric threshold.

### Requirements

- [ ] Each `REQ/SEC/PERF/COMP` states a **single** obligation (no "and" joining two).
- [ ] Uses active voice: "The system MUST validate…" not "Validation MUST be performed…"
- [ ] `PERF-###` includes a numeric threshold (e.g., "< 200ms p99", "10 000 events/s").

### Constraints

- [ ] Each `CON-###` excludes something concrete, not just rephrasing a REQ.

### Interfaces

- [ ] Every interface includes inputs, outputs, AND error cases.
- [ ] At minimum: invalid input (400), auth failure (401), downstream failure (500/503).

### Acceptance Criteria & Validation

- [ ] Each `AC-###` is independently observable without reading code.
- [ ] Each `AC-###` has a corresponding `VAL-###` that is a runnable command.

### Ready signal

If all checks pass and `validate.py --spec` returns 0 errors: ready for `sync.py`.

## Spec Interview (for vague requests)

Ask in order, one at a time:

1. **Goal**: "What outcome or capability are you enabling? One sentence."
2. **Scope**: "Which system or component does this touch? What's explicitly out of scope?"
3. **Constraints**: "Any limitations: timeline, existing systems, compliance, tech stack?"
4. **Interface**: "How will users/systems interact with this? What input, what output?"
5. **Success**: "How will you know it's done? What does the user see to verify it works?"

Document answers inline. Mark unknowns `UNKNOWN: [what and why]` — don't guess.
