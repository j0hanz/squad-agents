# Combined Spec + Quality Reviewer Prompt

**purpose:** Verify an implementer's diff in a single pass for BOTH spec compliance and code quality.
**when:** Immediately after an implementer returns `DONE` or `DONE_WITH_CONCERNS`.
**constraint:** This is the ONLY review path in `dispatch-agents`. There is no split-into-two-agents fallback. One reviewer, one pass, both verdicts.

## Dispatch Template

```text
SCOPE:
  Files touched: [list from implementer's FILES_TOUCHED]
  Baseline commit: [git hash from BEFORE implementer ran]
  Implementation commit: [implementer's git commit hash]

OBJECTIVE:
  Verify the implementation in ONE pass for BOTH:
  (a) Spec compliance — the diff matches the task spec, nothing more, nothing less.
  (b) Code quality — the diff is clean, testable, and maintainable.

CONTEXT:
  Task spec (verbatim):
  [Paste full original task spec — do not paraphrase]

  Implementer's claimed summary:
  [Paste implementer's SUMMARY verbatim]

  Project conventions:
  [Paste relevant conventions from AGENTS.md — naming, error handling, test patterns]

CONSTRAINTS:
  - Do NOT trust the implementer's summary — verify by reading the actual code.
  - Read every file listed in FILES_TOUCHED; diff baseline-to-implementation commit.
  - Evaluate ONLY code introduced by this task (delta from baseline to implementation commit).
  - Do NOT suggest features or scope expansions.
  - Flag any file that grew by more than 150 lines due to this task alone (heuristic; migrations/fixtures may legitimately exceed it — note as MINOR unless it signals a responsibility violation).

  SPEC CHECKS:
    1. MISSING_REQUIREMENTS: spec requirement not implemented (file:line).
    2. EXTRA_WORK: implemented but not in spec (file:line).
    3. MISINTERPRETATIONS: implementation solves a different problem than specified (file:line).

  QUALITY CHECKS:
    1. Responsibility: Does each file/class/function have one clear job?
    2. Testability: Are new units decomposed to be independently testable?
    3. Test coverage: Do tests exercise beyond the happy path?
    4. Error handling: Are all error paths handled, propagated, or explicitly documented as out-of-scope?
    5. File growth: Did any file gain >150 lines?
    6. Interface clarity: Are public APIs clearly named and typed?
    7. Security: Any injection risk (SQL/command/template), unsanitized input crossing a trust
       boundary, secrets/credentials committed, or unsafe deserialization introduced by this task?

OUTPUT SCHEMA:
  SPEC_VERDICT: [SPEC_PASS | SPEC_FAIL]

  QUALITY_VERDICT: [QUALITY_PASS | CRITICAL | IMPORTANT | MINOR]

  GATE: [PASS | FAIL]
  // GATE is FAIL if SPEC_VERDICT is SPEC_FAIL OR QUALITY_VERDICT is CRITICAL or IMPORTANT.
  // GATE is PASS otherwise (SPEC_PASS + QUALITY_PASS, or SPEC_PASS + MINOR).

  MISSING_REQUIREMENTS:
  [spec requirement not implemented — file:line reference]
  [or: none]

  EXTRA_WORK:
  [implemented but not in spec — file:line reference]
  [or: none]

  MISINTERPRETATIONS:
  [implementation solves different problem than specified — file:line reference]
  [or: none]

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
  [2-3 sentences: combined verdict with specific evidence from code, not from report]
```
