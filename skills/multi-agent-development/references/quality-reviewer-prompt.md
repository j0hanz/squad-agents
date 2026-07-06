---
name: quality-reviewer-prompt
description: Dispatch template, checks, and verdict rules for the Phase-3 code-quality reviewer subagent.
type: reference
canonical: true
---

# Code Quality Reviewer Prompt

**purpose:** Assess implementation cleanliness, testability, and maintainability.
**when:** Only after `SPEC_PASS` from Phase 2.
**constraint:** Do NOT re-check spec compliance — that was Phase 2.

## Dispatch Template

```text
SCOPE:
  Files changed: [list from implementer's FILES_CHANGED]
  Baseline commit: [git hash from BEFORE implementer ran]
  Implementation commit: [implementer's COMMIT hash]

OBJECTIVE:
  Assess whether the implementation is clean, testable, and maintainable.
  Spec compliance is already verified — do not re-check it.

CONTEXT:
  Task summary (what was built):
  [Paste implementer's SUMMARY verbatim]

  Project conventions:
  [Paste relevant conventions from AGENTS.md — naming, error handling, test patterns]

CONSTRAINTS:
  - Evaluate ONLY code introduced by this task (delta from baseline to implementation commit).
  - Do NOT suggest features or scope expansions.
  - Flag any file that grew by more than 150 lines due to this task alone (heuristic; migrations/fixtures may legitimately exceed it — note as MINOR unless it signals a responsibility violation).

CHECKS:
  1. Responsibility: Does each file/class/function have one clear job?
  2. Testability: Are new units decomposed to be independently testable?
  3. Test coverage: Do tests exercise beyond the happy path?
  4. Error handling: Are all error paths handled, propagated, or explicitly documented as out-of-scope?
  5. File growth: Did any file gain >150 lines?
  6. Interface clarity: Are public APIs clearly named and typed?
  7. Security: Any injection risk (SQL/command/template), unsanitized input crossing a trust
     boundary, secrets/credentials committed, or unsafe deserialization introduced by this task?

OUTPUT:
  VERDICT: [QUALITY_PASS | CRITICAL | IMPORTANT | MINOR]

  STRENGTHS:
  [file:line — what is well-implemented]

  CRITICAL_ISSUES:
  [file:line — issue and why it blocks]
  [or: none]

  IMPORTANT_ISSUES:
  [file:line — issue and recommended fix]
  [or: none]

  MINOR_ISSUES:
  [file:line — advisory note; fix in later refactor]
  [or: none]

  SUMMARY:
  [2-3 sentences: quality verdict with specific evidence]
```

## Verdict Rules

| Verdict        | Definition                                                                                                                       | Action                               |
| :------------- | :------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------- |
| `QUALITY_PASS` | No CRITICAL or IMPORTANT issues                                                                                                  | Advance to next task                 |
| `CRITICAL`     | Silent failure, broken abstraction, untested error path risking data loss or incorrect behavior, or any Check 7 security finding | Fix before advancing; re-run Phase 3 |
| `IMPORTANT`    | Responsibility violation, tight coupling, test gap causing near-term pain                                                        | Fix before advancing                 |
| `MINOR`        | Style inconsistency, minor naming issue                                                                                          | Log; fix later                       |

## Dispatcher Rules

| Condition                 | Action                                                            |
| :------------------------ | :---------------------------------------------------------------- |
| `CRITICAL` or `IMPORTANT` | Dispatch a new `implementer` with issues verbatim; re-run Phase 3 |
| `MINOR`                   | Log; proceed to next task                                         |
| `QUALITY_PASS`            | Mark task complete; move to next task                             |
| 2nd failure               | Surface to user                                                   |

**constraint:** Max 2 quality-fix iterations before escalating to user.
**constraint:** Supply AGENTS.md conventions — reviewer cannot infer them from code alone.
**constraint:** MINOR issues do NOT block advancement.
