# ponytail: local reference, frontmatter deferred until a cross-skill consumer appears

# Spec Compliance Reviewer Prompt

**purpose:** Verify implementation matches task spec — nothing more, nothing less.
**when:** Immediately after implementer returns `DONE` or `DONE_WITH_CONCERNS`.

## Dispatch Template

```text
SCOPE:
  Files changed: [list from implementer's FILES_CHANGED]
  Baseline commit: [git hash from BEFORE implementer ran]
  Implementation commit: [implementer's COMMIT hash]

OBJECTIVE:
  Verify the implementation matches the task specification — nothing more, nothing less.

CONTEXT:
  Task spec (verbatim):
  [Paste full original task spec — do not paraphrase]

  Implementer's claimed summary:
  [Paste implementer's SUMMARY verbatim]

CONSTRAINTS:
  - Do NOT trust the implementer's summary — verify by reading actual code.
  - Read every file listed in FILES_CHANGED.
  - Compare implementation to spec line by line.
  - Do NOT evaluate code quality, style, or test coverage — that is Phase 3.
  - Flag only: did they build exactly what was asked?

OUTPUT:
  VERDICT: [SPEC_PASS | SPEC_FAIL]

  MISSING_REQUIREMENTS:
  [spec requirement not implemented — file:line reference]
  [or: none]

  EXTRA_WORK:
  [implemented but not in spec — file:line reference]
  [or: none]

  MISINTERPRETATIONS:
  [implementation solves different problem than specified — file:line reference]
  [or: none]

  SUMMARY:
  [2-3 sentences: compliance verdict with evidence from code, not from report]
```

## Dispatcher Rules

| Condition       | Action                                                                                       |
| :-------------- | :------------------------------------------------------------------------------------------- |
| `SPEC_PASS`     | Advance to Phase 3                                                                           |
| `SPEC_FAIL`     | Dispatch a new `implementer` with MISSING_REQUIREMENTS + EXTRA_WORK verbatim; re-run Phase 2 |
| 2nd `SPEC_FAIL` | Surface to user — spec is ambiguous or conflicting                                           |

**constraint:** Max 2 fix iterations before escalating to user.
**constraint:** Provide task spec verbatim — never paraphrase.
**constraint:** Supply both commit hashes so reviewer diffs exactly what changed.
