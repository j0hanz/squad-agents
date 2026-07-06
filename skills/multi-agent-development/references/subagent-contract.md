---
name: subagent-contract
description: Canonical zero-shot prompt contract (five required fields) for dispatching general-purpose subagents.
type: reference
canonical: true
---

# Subagent Prompt Contract (Zero-Shot)

Canonical contract for any skill dispatching a `general-purpose` subagent (used by `multi-agent-development` and `multi-agent-dispatch`). Subagents start cold with no memory of the parent conversation. Every dispatch prompt MUST contain all five fields below.

## Prompt Fields

- **SCOPE:** In/Out of bounds paths. For writers, list files they may touch.
- **OBJECTIVE:** Concrete, verifiable outcome (e.g. "tests pass", not "improve X").
- **CONTEXT:** Errors, versions, baseline commit. Write large artifacts (>150 lines) under `.claude/dispatch/` and reference the file path here.
- **CONSTRAINTS:** Tool restrictions (e.g., read-only, git formatting conventions).
- **OUTPUT SCHEMA:** Instruct subagent to return:

  ```text
  VERDICT: [SUCCESS | FAILURE | BLOCKED | NEEDS_CONTEXT or role-specific enum]
  FILES_TOUCHED: [list of paths, or "none"]
  SUMMARY: [concise description of work/findings]
  EVIDENCE: [test results, grep output, or file:line citations]
  ```

## Common Mistakes (Check before dispatching)

- **Unbounded scope**: e.g., "Fix failing tests" -> Better: "Fix `src/auth/jwt.test.ts` only".
- **Missing context**: E.g., omitting error logs/baseline commit.
- **No constraints**: E.g., allowing edits in sibling lanes.
- **No output schema**: E.g., allowing freeform prose.
- **Inlined large files**: Inlining >150 lines configs instead of using file references.

## Model Tiering

Select the appropriate model tier based on task scope:

- **Fast/Cheap** (e.g., Haiku): Single domain, 1–2 files, fully concrete spec.
- **Standard** (`model: inherit`): Multi-file, cross-module, standard complexity.
- **Capable** (e.g., Opus): Architecture decisions, final-review gates, N-lane arbitration.

_Note: Default to `model: sonnet` if task complexity is ambiguous — never silently inherit the orchestrator's own model, which may be a more expensive tier than the task needs._

## Roles and Dispatch Directory

The project includes six named agents in the `agents/` directory with their own configurations and output schemas:

1. **`implementer`** (Writer): Runs with `isolation: worktree`. Returns `DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`.
2. **`researcher`** (Read-only Investigator/Researcher): Traces root causes and usages.
3. **`conflict-resolver`** (Writer): Resolves Git merge/rebase conflicts.
4. **`spec-reviewer`** & **`quality-reviewer`** (Read-only): Assess specs (Phase 2) and quality (Phase 3).
5. **`diff-reviewer`** (Read-only): Ad-hoc reviews on commits/diffs.

### Routing to Specialists

If a domain has no custom named agent, scan installed agents by category before falling back to `general-purpose`:

| Lane Domain                  | Specialist Focus                     | Fallback          |
| :--------------------------- | :----------------------------------- | :---------------- |
| Architecture / System Design | Architecture/System Review           | `general-purpose` |
| Language Code Quality        | Language-specific review (Python/TS) | `general-purpose` |
| Error Handling               | Silent-failure/error auditing        | `general-purpose` |
| Debugging                    | Diagnostic/investigation             | `general-purpose` |
| Documentation                | Docs maintenance/sync                | `general-purpose` |

## Independent Verification

Orchestrators must independently verify subagent claims (e.g., run test suites, check `git status`/`git diff`) instead of trusting a `VERDICT: SUCCESS` at face value.
