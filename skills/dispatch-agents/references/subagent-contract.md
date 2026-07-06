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

_Note: Default to `model: "sonnet"` if task complexity is ambiguous — never silently inherit the orchestrator's own model, which may be a more expensive tier than the task needs. Apply an explicit `model:` override at every dispatch call site._

## Roles

The `dispatch-agents` skill uses exactly four named agents. None of them spawn further subagents — the orchestrator (main thread) is the only dispatcher (depth-1 rule).

| Agent               | Role                                 | Isolation              | Verdict Schema                                                                                                                            |
| :------------------ | :----------------------------------- | :--------------------- | :---------------------------------------------------------------------------------------------------------------------------------------- |
| `implementer`       | Writer — implements one task         | `worktree`             | `DONE \| DONE_WITH_CONCERNS \| BLOCKED \| NEEDS_CONTEXT`                                                                                  |
| `researcher`        | Read-only investigator               | (none, read-only)      | `SUCCESS \| FAILURE \| BLOCKED \| NEEDS_CONTEXT`                                                                                          |
| `reviewer`          | Read-only combined spec+quality gate | (none, read-only)      | `SPEC_VERDICT: SPEC_PASS \| SPEC_FAIL` + `QUALITY_VERDICT: QUALITY_PASS \| CRITICAL \| IMPORTANT \| MINOR` + derived `GATE: PASS \| FAIL` |
| `conflict-resolver` | Writer — resolves merge conflicts    | (none, edits in place) | `DONE \| BLOCKED`                                                                                                                         |

### Writer Verdict Schema (implementer)

```text
VERDICT: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
SUMMARY: [what was built]
FILES_CHANGED: [paths]
COMMIT: [git hash]
CONCERNS / BLOCKER / QUESTION: [per verdict]
```

### Investigator Verdict Schema (researcher)

```text
VERDICT: [SUCCESS | FAILURE | BLOCKED | NEEDS_CONTEXT]
FILES_TOUCHED: [list of paths, or "none"]
SUMMARY: [concise description of findings]
EVIDENCE: [test results, grep output, or file:line citations]
```

## Issue Tiering (CRITICAL / IMPORTANT / MINOR)

Every lane — writer or researcher — is tiered into one of three buckets for the final report, matching the reviewer's `QUALITY_VERDICT` enum:

- **CRITICAL:** Silent failure, broken abstraction, untested error path risking data loss or incorrect behavior, or any security finding (injection, unsanitized input at a trust boundary, committed secrets, unsafe deserialization). Blocks advancement; re-dispatch or discard.
- **IMPORTANT:** Responsibility violation, tight coupling, test gap causing near-term pain. Fix before advancing.
- **MINOR:** Style inconsistency, minor naming issue. Log; fix later. Does NOT block advancement.

## Dispatch Constraints (dispatch-agents specific)

These two constraints are in addition to the common contract above:

1. **Wave width <= 10 lanes, sized to the Matrix's actual independent-task count — never padded to hit the cap.** A wave contains only lanes the Lane Matrix proves are file-disjoint and dependency-clear. If the Matrix shows 3 independent lanes, the wave is 3 lanes; padding it to 10 introduces collisions and duplicated work. The 10-lane cap is a maximum, never a target.

2. **Dispatch stays at depth 1.** None of the four named agents (`implementer`, `researcher`, `reviewer`, `conflict-resolver`) spawn further subagents. The orchestrator (main thread) is the only dispatcher. A named agent that needs more work returns its verdict and the orchestrator decides the next dispatch — it does not delegate downward.

## Independent Verification

Orchestrators must independently verify subagent claims (e.g., run the test suite, check `git status` / `git diff`) instead of trusting a `VERDICT: DONE` or `VERDICT: SUCCESS` at face value. The reviewer's `GATE: PASS` is a claim; the real test suite is proof.
