---
name: multi-agent-development
description: 'Use when implementing a multi-task plan where tasks depend on each other, share files, or must run in order. Prefer over multi-agent-dispatch when tasks have shared state or file dependencies that prevent parallel execution.'
disable-model-invocation: false
argument-hint: '[path to plan file]'
allowed-tools: Agent(implementer), Agent(spec-reviewer), Agent(quality-reviewer), Agent(conflict-resolver), AskUserQuestion, Bash(git log*), Bash(git diff*), Skill(write-commit), Skill(verification-before-completion), Skill(request-code-review)
---

# multi-agent-development

Orchestrate sequential task execution with zero context pollution and high quality-assurance.

## When to Use

- **Dependencies or shared state across tasks?** → Sequential (this skill).
- **Fully independent tasks, no shared state?** → Parallel (`multi-agent-dispatch`).
- **A plan mixing both?** → This skill, but cluster the independent tasks (see Partitioning & Scope) and dispatch each cluster the way `multi-agent-dispatch` does — background, in parallel — instead of forcing every task through the loop one at a time.

## Process Flow

```
Start Cluster (1+ tasks, Depends-on satisfied) -> Phase 1: Implement EACH task in the cluster
  (independent tasks: launched together, run_in_background, isolation: worktree — no waiting between them)
  -> per task, as it reports back: Phase 2+3: Combined Review (one read-only reviewer, both verdicts)
       -- SPEC_PASS + (QUALITY_PASS|MINOR) ---> this task done
       -- SPEC_FAIL or CRITICAL/IMPORTANT (1st) -> fix, re-run Combined Review
       -- 2nd failure (split mode) -------------> fix, re-run as separate Phase 2 / Phase 3
       -- still failing after split's 2 tries --> BLOCKED (escalate to user)

Cluster done when every task in it is done/blocked -> Next Cluster?
  -- yes --> loop to Start Cluster
  -- no  --> Final Validation (test & verify)
```

## Step 0: Setup

Read `references/implementer-prompt.md`, `references/spec-reviewer-prompt.md`, `references/quality-reviewer-prompt.md`, and `references/subagent-contract.md` once, here — not again per task or per phase. The Core Loop below assumes you already have them.

Default to running all tasks straight through — that was already the recommended option, so don't spend a round-trip asking for it. Raise `AskUserQuestion` ("run all" vs. "run one task first to validate the loop") only when the plan is large or unfamiliar enough that a single test task is a genuinely safer first step.

## Partitioning & Scope

**Single task, no dependencies?** Skip the Matrix — there's nothing to partition. Go straight to the Core Loop.

Before asking the user, write the Lane Matrix defined in `skills/multi-agent-dispatch/SKILL.md#Step 2: MATRIX` — it's what makes "strict order" a fact instead of a guess.

- **File Rule**: Combine tasks into one if they touch the same files — never run two tasks against overlapping paths even sequentially without merging them first.
- **Cluster Rule**: Group every run of tasks that share `Depends on: none` and disjoint files into one cluster. A cluster is dispatched together (see Clustered Phase 1 below) — clusters themselves still run in the matrix's dependency order.
- **Action**: Derive the order directly from the matrix's `Depends on` column and state it as plain text — that was already the recommended option, so don't ask for it. Raise `AskUserQuestion` only if the matrix itself is ambiguous (conflicting or circular dependencies) and the order can't be resolved from the files alone.

## Clustered Phase 1 (independent tasks only)

For a cluster of 2+ tasks with no dependency between them: dispatch one implementer per task in the SAME message, each with `isolation: "worktree"` and `run_in_background: true`. Don't wait for one to finish before launching the next in the cluster — that's the serialization this skill otherwise forces, and it's unnecessary when the Matrix already proves the tasks don't touch each other. Run Phase 2/Phase 3 for each task as soon as its implementer reports back, independently of the others in the cluster — a slow task in the cluster never blocks review of a fast one. Move to the next task/cluster only once every task in the current cluster has reached `QUALITY_PASS` or escalated.

## Core Loop (Strict Order, per task or per cluster member)

- **Phase 1**: Implement.
- **Agent**: `implementer` (isolated worktree), per `references/implementer-prompt.md` and `references/subagent-contract.md` (large-artifact rule, Model Tiering — apply an explicit `model:` override at the dispatch call site).
- **Output**: Verdict, files touched, commit, summary.
- **Before advancing:** implementer must return `DONE` or `DONE_WITH_CONCERNS`. If `BLOCKED` or `NEEDS_CONTEXT`, stop and surface to the user — do not dispatch Phase 2.

- **Phase 2+3 (default — low/med risk, first pass)**: Combined Review.
- **Agent**: ONE read-only `spec-reviewer`, given both `references/spec-reviewer-prompt.md` and `references/quality-reviewer-prompt.md` as its dispatch contract, asked to return both `SPEC_VERDICT` and `QUALITY_VERDICT` in one pass. This avoids two cold-start agents independently re-reading the same diff.
- **Rules**: Combined review retries in combined mode up to 2 tries. If `SPEC_FAIL`, fix and re-run the combined pass (don't bother scoring quality on a spec-failing diff). If `SPEC_PASS` but `CRITICAL`/`IMPORTANT`, fix and re-run. On the 2nd failure in combined mode, OR if the task was designated high-risk up-front, split into per-agent review (Phase 2 / Phase 3 below).
- **Before advancing:** needs `SPEC_PASS` + (`QUALITY_PASS` or `MINOR`).

- **Phase 2 / Phase 3 (split)**: run as two separate agents, per the original per-phase contracts below. Fresh eyes matter once a fix has already gone in.
  - **Phase 2**: Read-only `spec-reviewer` per `references/spec-reviewer-prompt.md`. Do not substitute `diff-reviewer` — it lacks the full task spec context. Max 2 tries; `SPEC_FAIL` twice → escalate.
  - **Phase 3**: Read-only `quality-reviewer` per `references/quality-reviewer-prompt.md`, only after `SPEC_PASS`. Do not substitute `diff-reviewer`. Max 2 tries (separate from Phase 2's count); `CRITICAL`/`IMPORTANT` twice → escalate.

- **After SPEC_PASS + (QUALITY_PASS or MINOR), whichever path got you there:** advance to the next task or cluster.

## Final Validation

- **Bar**: Every task clears the project-wide [Definition of Done](../verification-before-completion/references/definition-of-done.md) before it counts as done — independently verified, never on the implementer's self-report.
- **Test**: Run project tests.
- **Verify**: Run `verification-before-completion`.
- **Review**: Run `request-code-review` (Mandatory).
- **Done when:** every task is QUALITY_PASS or escalated-by-name, the full test suite is GREEN, and both `verification-before-completion` and `request-code-review` have run.

### Report Template

Present the consolidated result to the user in this exact shape:

```
| Task | VERDICT        | Spec   | Quality        | Action                        |
| :--- | :-------------- | :----- | :-------------- | :----------------------------- |
| 1    | DONE/BLOCKED... | PASS/FAIL | QUALITY_PASS/CRITICAL/IMPORTANT/MINOR | merged / re-dispatched / blocked |

Tests: [PASS|FAIL — command run]
Blocked/escalated tasks: [list, or "none"]
```

## Failure Modes (check before you call it done)

- A task's "Depends on" was assumed instead of verified against the Lane Matrix — order was wrong.
- An implementer's `DONE` summary was trusted instead of the spec/quality reviewers actually reading the diff.
- A blocked or skipped task wasn't surfaced to the user — it just silently didn't happen. **If any lane reaches `BLOCKED` or `NEEDS_CONTEXT`, surface it to the user before continuing. Never advance the next cluster while a blocked lane is unresolved.**
- An old agent was reused across tasks, carrying stale memory into a new task's context.
- Tasks with `Depends on: none` and disjoint files were still run one-at-a-time instead of clustered — wasted wall-clock time with no correctness benefit.
- On resume, a task's completion was assumed instead of verified against `git log` — always confirm the task's commit (matched by its `<type>: [task title]` subject) actually exists before treating it as done.

## Worked Example

Plan: add a "saved searches" feature — schema, API, and UI. Partition Matrix:

| Task | Files touched                                           | Depends on | Risk | Verification      |
| :--- | :------------------------------------------------------ | :--------- | :--- | :---------------- |
| 1    | `migrations/saved_search.sql`, `models/saved_search.ts` | none       | med  | `npm test models` |
| 2    | `api/saved-search.ts`                                   | Task 1     | med  | `npm test api`    |
| 3    | `ui/SavedSearches.tsx`                                  | Task 2     | low  | `npm test ui`     |

Strict chain (2 needs 1's model, 3 needs 2's contract) → no clustering; run in order. Each task: Phase 1 implement (worktree) → combined Phase 2+3 review, clearing the [Definition of Done](../verification-before-completion/references/definition-of-done.md) before the next starts.

```
| Task | VERDICT | Spec | Quality | Action |
| :--- | :------ | :--- | :------ | :----- |
| 1    | DONE    | PASS | QUALITY_PASS    | merged |
| 2    | DONE    | PASS | IMPORTANT → fixed, re-run split (Phase 2/Phase 3) | re-dispatched, then merged |
| 3    | DONE    | PASS | QUALITY_PASS    | merged |

Tests: PASS — `npm test` (full suite)
Blocked/escalated tasks: none
```

Contrast with `multi-agent-dispatch`: there the lanes were file-disjoint and launched together; here Task 2 literally cannot start until Task 1's model exists, so the Matrix's `Depends on` column forces order.

**Clustered Phase 1:** When tasks share `Depends on: none` and disjoint files, dispatch all their implementers in the same message (`isolation: worktree`, `run_in_background: true`) — review each as it reports back independently. Tasks that depend on the cluster wait for every member to reach `QUALITY_PASS` before launching.

## Operational Rules

- **Agents**: Use a new agent for every task. Independent tasks in a cluster get separate agents launched together, not reused or queued.
- **Prompts**: Give agents all facts. They have no memory.
- **Commits**: Implementer subjects follow `<type>: [task title]` — format rules (policy, secret-scan, vocabulary) defer to `write-commit`.
- **Rejects**: Throw away bad work. Start over from a clean base.
- **Conflicts**: If a Git merge fails, follow the conflict-resolution procedure in `skills/multi-agent-dispatch/SKILL.md#Git Merge Conflict Resolution` (dispatch the specialized `conflict-resolver` agent; escalate to the user only if it reports the conflict cannot be resolved).
- **Resuming**: Before restarting, check `git log` for commits matching the plan's task titles (`<type>: [task title]` subjects) to see which tasks already completed — never trust self-recollection alone.
- **Context**: The orchestrator thread accumulates summaries across every task loop even though subagents are isolated. Prune intermediate subagent logs, thinking steps, and full file diffs from the main conversation context once integrated, keeping only a high-level summary and the merge commit hash.

## Next Skills

- `write-commit`: Apply commit rules for each task's staged changes before final validation.
- `verification-before-completion`: Run this for Final Validation handoff.
- `diagnose`: Run this for merge/test failure investigation.
