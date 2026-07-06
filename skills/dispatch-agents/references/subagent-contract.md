---
name: subagent-contract
description: Canonical zero-shot prompt contract (five required fields), roles, model tiering, and verdict schemas for dispatch-agents.
type: reference
canonical: true
---

# Subagent Prompt Contract (Zero-Shot)

Canonical contract for the `dispatch-agents` skill. Subagents start cold with no memory of the parent conversation. Every dispatch prompt MUST contain all five fields below.

## Prompt Fields

- **SCOPE:** In/Out of bounds paths. For writers, list files they may touch.
- **OBJECTIVE:** Concrete, verifiable outcome (e.g. "tests pass", not "improve X").
- **CONTEXT:** Errors, versions, baseline commit. Write large artifacts (>150 lines) under `.claude/dispatch/` and reference the file path here — never inline them in the dispatch prompt.
- **CONSTRAINTS:** Tool restrictions (e.g., read-only, git formatting conventions).
- **OUTPUT SCHEMA:** Instruct the subagent to return the role-specific verdict schema (see Roles table below).

```text
VERDICT: [role-specific enum]
FILES_TOUCHED: [list of paths, or "none"]
SUMMARY: [concise description of work/findings]
EVIDENCE: [test results, grep output, or file:line citations]
```

## Common Mistakes (Check before dispatching)

- **Unbounded scope**: e.g., "Fix failing tests" -> Better: "Fix `src/auth/jwt.test.ts` only".
- **Missing context**: E.g., omitting error logs/baseline commit.
- **No constraints**: E.g., allowing edits in sibling lanes.
- **No output schema**: E.g., allowing freeform prose.
- **Inlined large files**: Inlining >150-line configs instead of using `.claude/dispatch/` file references.

## Model Tiering

Select the appropriate model tier based on task scope:

- **Fast/Cheap** (e.g., Haiku): Single domain, 1–2 files, fully concrete spec.
- **Standard** (`model: "sonnet"`): Multi-file, cross-module, standard complexity.
- **Capable** (e.g., Opus): Architecture decisions, final-review gates, N-lane arbitration, security-sensitive or adversarial work.

_Note: Default to `model: "sonnet"` if task complexity is ambiguous. Apply an explicit `model:` override at every dispatch call site._

## Roles

The `dispatch-agents` skill uses exactly four named agents. None of them spawn further subagents (depth-1 rule).

| Agent               | Role                                 | Isolation              | Verdict Schema                                                                                                                            |
| :------------------ | :----------------------------------- | :--------------------- | :---------------------------------------------------------------------------------------------------------------------------------------- |
| `implementer`       | Writer — implements one task         | `worktree`             | `DONE \| DONE_WITH_CONCERNS \| BLOCKED \| NEEDS_CONTEXT`                                                                                  |
| `researcher`        | Read-only investigator               | (none, read-only)      | `SUCCESS \| FAILURE \| BLOCKED \| NEEDS_CONTEXT`                                                                                          |
| `reviewer`          | Read-only combined spec+quality gate | (none, read-only)      | `SPEC_VERDICT: SPEC_PASS \| SPEC_FAIL` + `QUALITY_VERDICT: QUALITY_PASS \| CRITICAL \| IMPORTANT \| MINOR` + derived `GATE: PASS \| FAIL` |
| `conflict-resolver` | Writer — resolves merge conflicts    | (none, edits in place) | `DONE \| BLOCKED`                                                                                                                         |

_Note: Per-role output schemas are detailed in their respective prompt files in `references/` (e.g. `implementer-prompt.md`, `reviewer-prompt.md`, `researcher-prompt.md`)._

## Issue Tiering (CRITICAL / IMPORTANT / MINOR)

Every lane is tiered for the final report:

- **CRITICAL:** Silent failure, broken abstraction, untested error path risking data loss, or any security finding (injection, unsanitized input at trust boundary, committed secrets, unsafe deserialization). Blocks advancement.
- **IMPORTANT:** Responsibility violation, tight coupling, test gap causing near-term pain. Fix before advancing.
- **MINOR:** Style inconsistency, minor naming issue. Researcher lanes default here unless they report a blocker (which escalates). Does NOT block advancement.
