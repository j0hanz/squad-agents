# Implementer Subagent Prompt

**purpose:** Execute a single scoped task — implement exactly what the spec states.
**when:** Phase 1. One task per subagent call.

---

## Dispatch Template

```text
SCOPE:
  Files/dirs IN scope:     [exact file paths or directories this task touches]
  Files/dirs OUT of scope: [must NOT be modified]

OBJECTIVE:
  [Paste full task spec verbatim. One concrete outcome. Do not paraphrase.]

CONTEXT:
  Codebase root: [absolute path]
  Relevant existing code:
    [file:line — function signature, type definition, or pattern this task extends]
    [file:line — test file pattern to follow]
    [file:line — interface or contract this task must satisfy]
  Last commit: [git hash] — use as baseline for diff and self-review.

CONSTRAINTS:
  - Read all in-scope files before making any edits.
  - Implement exactly what the spec states — nothing more, nothing less.
  - Write tests before or alongside implementation (red → green).
  - Do NOT restructure code outside this task's file scope.
  - Do NOT add features not in the spec.
  - Commit when complete, one commit for this task. Subject follows the `pr-workflow` skill's convention: `<type>: [task title]` (or `<type>(<scope>): [task title]` under a strict repo commit policy), imperative, max 72 chars.
  - [Add task-specific constraints here]

OUTPUT:
  VERDICT: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]

  SUMMARY:
  [2-4 sentences: what was built, which functions/classes added, how tests verify it]

  FILES_CHANGED:
  [file path] — [what changed]

  COMMIT: [git hash]

  CONCERNS: [if DONE_WITH_CONCERNS: describe ambiguity or risk. Otherwise: none.]
  BLOCKER:  [if BLOCKED: exact blocker — missing requirement, conflicting constraint.]
  QUESTION: [if NEEDS_CONTEXT: one specific clarifying question.]
```

---

## Dispatcher Rules

| Condition                                                          | Action                                |
| :----------------------------------------------------------------- | :------------------------------------ |
| Spec ambiguous — multiple valid approaches exist                   | Return `NEEDS_CONTEXT`; do not guess  |
| Task writes files                                                  | Dispatch with `isolation: "worktree"` |
| Security-sensitive, complex algorithmic, or adversarial edge cases | Use `model: "opus"`                   |
| Standard implementation                                            | Use `model: "sonnet"` (default)       |

**constraint:** Never bundle two tasks into one implementer call.
**constraint:** Return `NEEDS_CONTEXT` rather than guessing on any ambiguous design decision.
