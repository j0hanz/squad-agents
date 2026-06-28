---
name: multi-agent-development
description: "Executes a multi-task implementation plan sequentially using isolated, single-purpose subagents with gated quality checks. Accepts a file path to a markdown plan or specification file as input, and writes code changes across multiple files, completing with a comprehensive validation report, test results, and automated git commits. Trigger on: 'implement the plan', 'execute spec', 'agentic development', 'multi-agent-development', 'sequential tasks', 'gated implementation'. Also triggers when the user wants to run a series of dependent coding tasks with rigorous code reviews and test runs at each step. Always prefer over multi-agent-dispatch when tasks share mutable state, have file dependencies, or require ordered execution."
disable-model-invocation: false
argument-hint: '[path to plan file]'
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
  -> per task, as it reports back: Phase 2: Spec Compliance (read-only reviewer)
       -- SPEC_PASS ------------------> Phase 3: Code Quality (read-only auditor)
       -- SPEC_FAIL (retry) -----------> back to Phase 1 for that task only
       -- SPEC_FAIL (after 2 attempts) -> BLOCKED (escalate to user)

     Phase 3: Code Quality
       -- QUALITY_PASS -------------> this task done
       -- CRITICAL / IMPORTANT (retry) -> back to Phase 1 for that task only

Cluster done when every task in it is done/blocked -> Next Cluster?
  -- yes --> Orchestrator Context Bloated? -- yes --> context-optimizer --> resume loop
                                            -- no  --> loop to Start Cluster
  -- no  --> Final Validation (test & verify)
```

## NEVER Do This

- **Skip Gates**: NEVER. It causes errors.
- **Trust Summaries**: NEVER. Verify the code yourself.
- **Reuse Agents**: NEVER. Old memory causes mistakes.
- **Blind Reviewers**: NEVER. Read prompt files before sending reviewers.
- **File Overlaps**: NEVER. Tasks must use different files unless ordered.
- **Merge Early**: NEVER. Wait until the task fully passes.
- **Trust Clean Merges**: NEVER. Run tests after every merge.

## Step 0: Setup

Default to running all tasks straight through — that was already the recommended option, so don't spend a round-trip asking for it. Raise `AskUserQuestion` ("run all" vs. "run one task first to validate the loop") only when the plan is large or unfamiliar enough that a single test task is a genuinely safer first step.

## Partitioning & Scope

Before asking the user, write the same Lane Matrix `multi-agent-dispatch` uses — it's what makes "strict order" a fact instead of a guess:

| Task | Files touched | Depends on | Risk | Verification |
| :--- | :------------ | :--------- | :--- | :----------- |
| 1    | [exact paths] | none       | ...  | ...          |
| 2    | ...           | Task 1     | ...  | ...          |

- **File Rule**: Combine tasks into one if they touch the same files — never run two tasks against overlapping paths even sequentially without merging them first.
- **Cluster Rule**: Group every run of tasks that share `Depends on: none` and disjoint files into one cluster. A cluster is dispatched together (see Clustered Phase 1 below) — clusters themselves still run in the matrix's dependency order.
- **Action**: Derive the order directly from the matrix's `Depends on` column and state it as plain text — that was already the recommended option, so don't ask for it. Raise `AskUserQuestion` only if the matrix itself is ambiguous (conflicting or circular dependencies) and the order can't be resolved from the files alone.

## Clustered Phase 1 (independent tasks only)

For a cluster of 2+ tasks with no dependency between them: dispatch one implementer per task in the SAME message, each with `isolation: "worktree"` and `run_in_background: true`. Don't wait for one to finish before launching the next in the cluster — that's the serialization this skill otherwise forces, and it's unnecessary when the Matrix already proves the tasks don't touch each other. Run Phase 2/Phase 3 for each task as soon as its implementer reports back, independently of the others in the cluster — a slow task in the cluster never blocks review of a fast one. Move to the next task/cluster only once every task in the current cluster has reached `QUALITY_PASS` or escalated.

## Core Loop (Strict Order, per task or per cluster member)

- **Phase 1**: Implement.
- **Agent**: `implementer` (isolated worktree).
- **Input**: Read `references/implementer-prompt.md` and `references/subagent-contract.md` (including the large-artifact rule for `.claude/dispatch/` handoff).
- **Output**: Verdict, files touched, commit, summary.
- **Before advancing:** implementer must return `DONE` or `DONE_WITH_CONCERNS`. If `BLOCKED` or `NEEDS_CONTEXT`, stop and surface to the user — do not dispatch Phase 2.

- **Phase 2**: Spec Check.
- **Agent**: Read-only `spec-reviewer`. Do not substitute `diff-reviewer` here — spec-reviewer receives the full task spec context that diff-reviewer does not have.
- **Input**: Read `references/spec-reviewer-prompt.md`.
- **Goal**: Check if they built exactly what was asked.
- **Rules**: Max 2 tries. If blocked, pause all tasks and ask the user.
- **Before advancing:** spec-reviewer must return `SPEC_PASS`. If `SPEC_FAIL` twice, escalate to user.

- **Phase 3**: Quality Check.
- **Agent**: Read-only `quality-reviewer`. Do not substitute `diff-reviewer` here.
- **Input**: Read `references/quality-reviewer-prompt.md`.
- **Goal**: Check code quality and tests.
- **Rules**: Max 2 tries (this does not count against Phase 2).
- **Before advancing:** quality-reviewer must return `QUALITY_PASS` or `MINOR`. If `CRITICAL` or `IMPORTANT` twice, escalate to user.

## Final Validation

- **Bar**: Every task clears the project-wide [Definition of Done](../verification-before-completion/references/definition-of-done.md) before it counts as done — independently verified, never on the implementer's self-report.
- **Test**: Run project tests.
- **Verify**: Run `verification-before-completion`.
- **Review**: Run `request-code-review` (Mandatory).

### Report Template

Present the consolidated result to the user in this exact shape:

```
| Task | VERDICT        | Spec   | Quality        | Action                        |
| :--- | :-------------- | :----- | :-------------- | :----------------------------- |
| 1    | DONE/BLOCKED... | PASS/FAIL | PASS/CRITICAL/IMPORTANT/MINOR | merged / re-dispatched / blocked |

Tests: [PASS|FAIL — command run]
Blocked/escalated tasks: [list, or "none"]
```

## Failure Modes (check before you call it done)

- A task's "Depends on" was assumed instead of verified against the Lane Matrix — order was wrong.
- An implementer's `DONE` summary was trusted instead of the spec/quality reviewers actually reading the diff.
- A blocked or skipped task wasn't surfaced to the user — it just silently didn't happen. **If any lane reaches `BLOCKED` or `NEEDS_CONTEXT`, surface it to the user before continuing. Never advance the next cluster while a blocked lane is unresolved.**
- An old agent was reused across tasks, carrying stale memory into a new task's context.
- Tasks with `Depends on: none` and disjoint files were still run one-at-a-time instead of clustered — wasted wall-clock time with no correctness benefit.

## Worked Example

Plan: add a "saved searches" feature — schema, API, and UI. Partition Matrix:

| Task | Files touched                                           | Depends on | Risk | Verification      |
| :--- | :------------------------------------------------------ | :--------- | :--- | :---------------- |
| 1    | `migrations/saved_search.sql`, `models/saved_search.ts` | none       | med  | `npm test models` |
| 2    | `api/saved-search.ts`                                   | Task 1     | med  | `npm test api`    |
| 3    | `ui/SavedSearches.tsx`                                  | Task 2     | low  | `npm test ui`     |

Strict chain (2 needs 1's model, 3 needs 2's contract) → no clustering; run in order. Each task: Phase 1 implement (worktree) → Phase 2 spec check → Phase 3 quality check, clearing the [Definition of Done](../verification-before-completion/references/definition-of-done.md) before the next starts.

```
| Task | VERDICT | Spec | Quality | Action |
| :--- | :------ | :--- | :------ | :----- |
| 1    | DONE    | PASS | PASS    | merged |
| 2    | DONE    | PASS | IMPORTANT → fixed | re-dispatched, then merged |
| 3    | DONE    | PASS | PASS    | merged |

Tests: PASS — `npm test` (full suite)
Blocked/escalated tasks: none
```

Contrast with `multi-agent-dispatch`: there the lanes were file-disjoint and launched together; here Task 2 literally cannot start until Task 1's model exists, so the Matrix's `Depends on` column forces order.

## Worked Example: Clustered Phase 1

Same feature, but Tasks 1 and 2 turn out to be independent (separate modules, no shared types) while Task 3 still depends on both:

| Task | Files touched                 | Depends on | Risk | Verification   |
| :--- | :---------------------------- | :--------- | :--- | :------------- |
| 1    | `migrations/saved_search.sql` | none       | med  | `npm test db`  |
| 2    | `api/rate-limiter.ts`         | none       | low  | `npm test api` |
| 3    | `ui/SavedSearches.tsx`        | 1, 2       | low  | `npm test ui`  |

Tasks 1 and 2 share `Depends on: none` and disjoint files → one cluster. Dispatch both implementers in the SAME message, each `isolation: "worktree"`, `run_in_background: true` — do not wait for Task 1 before launching Task 2. When Task 2's implementer notifies first (it's the smaller change), immediately run its Phase 2/3 gates without waiting on Task 1; a slow lane in the cluster never blocks review of a fast one. Task 3 cannot launch until both 1 and 2 have reached `QUALITY_PASS`, since it depends on both.

```
| Task | VERDICT | Spec | Quality | Action |
| :--- | :------ | :--- | :------ | :----- |
| 2    | DONE    | PASS | PASS    | merged (reviewed first, finished first) |
| 1    | DONE    | PASS | PASS    | merged |
| 3    | DONE    | PASS | PASS    | merged, started only after 1 and 2 both passed |

Tests: PASS — `npm test` (full suite)
Blocked/escalated tasks: none
```

Outcome: two independent tasks ran wall-clock in parallel inside an otherwise sequential plan, with zero added risk — because the Matrix proved them file-disjoint and dependency-free before clustering them.

## Operational Rules

- **Agents**: Use a new agent for every task. Independent tasks in a cluster get separate agents launched together, not reused or queued.
- **Prompts**: Give agents all facts. They have no memory.
- **Commits**: Give reviewers the exact old commit and new commit.
- **Rejects**: Throw away bad work. Start over from a clean base.
- **Conflicts**: If a Git merge fails, do NOT immediately abort or escalate. Dispatch the specialized `conflict-resolver` agent (`agents/conflict-resolver.md`) to read conflict markers, resolve them, test, and commit the resolution. Only pause and ask the user if the conflict resolver returns `VERDICT: BLOCKED`.
- **Resuming**: Check `git log` before restarting to avoid repeating work.
- **Context**: The orchestrator thread accumulates summaries across every task loop even though subagents are isolated. Run `context-optimizer` after every cluster boundary (never mid-task) once 3+ tasks have reported back since the last optimization pass, or sooner if responses noticeably slow down. Prune intermediate subagent logs, thinking steps, and full file diffs from the main conversation context once integrated, keeping only a high-level summary and the merge commit hash.
