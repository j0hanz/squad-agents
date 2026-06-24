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

## Process Flow

```
Start Loop (Per Task) -> Phase 1: Implement (general-purpose subagent) -> Phase 2: Spec Compliance (read-only reviewer)
  -- SPEC_PASS ------------------> Phase 3: Code Quality (read-only auditor)
  -- SPEC_FAIL (retry) -----------> back to Phase 1
  -- SPEC_FAIL (after 2 attempts) -> BLOCKED (escalate to user)

Phase 3: Code Quality
  -- QUALITY_PASS -------------> Next Task?
  -- CRITICAL / IMPORTANT (retry) -> back to Phase 1

Next Task?
  -- yes --> Orchestrator Context Bloated? -- yes --> context-optimizer --> resume loop
                                            -- no  --> loop to Start
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

## Step 0: Confirm

- **Action**: AskUserQuestion for setup.
- **Option 1**: Run all tasks (Recommended).
- **Option 2**: Run one task to test (Alternative).

## Partitioning & Scope

Before asking the user, write the same Lane Matrix `multi-agent-dispatch` uses — it's what makes "strict order" a fact instead of a guess:

| Task | Files touched | Depends on | Risk | Verification |
| :--- | :------------ | :--------- | :--- | :----------- |
| 1    | [exact paths] | none       | ...  | ...          |
| 2    | ...           | Task 1     | ...  | ...          |

- **File Rule**: Combine tasks into one if they touch the same files — never run two tasks against overlapping paths even sequentially without merging them first.
- **Action**: AskUserQuestion for task order, using the matrix as evidence.
- **Option 1**: Strict order based on the matrix's `Depends on` column (Recommended).
- **Option 2**: Grouped tasks with reasons (Alternative).

## Core Loop (Strict Order)

- **Phase 1**: Implement.
- **Agent**: `general-purpose` (isolated worktree).
- **Input**: Read `references/implementer-prompt.md` and `references/subagent-contract.md`.
- **Output**: Verdict, files touched, commit, summary.

- **Phase 2**: Spec Check.
- **Agent**: Read-only `general-purpose`.
- **Input**: Read `references/spec-reviewer-prompt.md`.
- **Goal**: Check if they built exactly what was asked.
- **Rules**: Max 2 tries. If blocked, pause all tasks and ask the user.

- **Phase 3**: Quality Check.
- **Agent**: Read-only `general-purpose`.
- **Input**: Read `references/quality-reviewer-prompt.md`.
- **Goal**: Check code quality and tests.
- **Rules**: Max 2 tries (this does not count against Phase 2).

## Final Validation

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
- A blocked or skipped task wasn't surfaced to the user — it just silently didn't happen.
- An old agent was reused across tasks, carrying stale memory into a new task's context.

## Operational Rules

- **Agents**: Use a new agent for every task.
- **Prompts**: Give agents all facts. They have no memory.
- **Commits**: Give reviewers the exact old commit and new commit.
- **Rejects**: Throw away bad work. Start over from a clean base.
- **Conflicts**: If a merge fails, pause and ask the user.
- **Resuming**: Check `git log` before restarting to avoid repeating work.
- **Context**: The orchestrator thread accumulates summaries across every task loop even though subagents are isolated. If it bloats, run `context-optimizer` between loop iterations (never mid-task) before continuing.
