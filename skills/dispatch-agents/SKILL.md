---
name: dispatch-agents
description: 'Use when a multi-task plan or backlog has dependency-ordered tasks that can run in parallel without file conflicts.'
disable-model-invocation: false
argument-hint: '[path to plan file, or the tasks to execute]'
allowed-tools: Agent, AskUserQuestion, Bash, Read, Grep
---

# dispatch-agents

Execute a multi-task plan by grouping tasks into dependency-ordered waves and dispatching up to 10 subagents in parallel.

## Process Flow

`Matrix (lane independence) -> Waves (topological sort) -> wave loop (Dispatch -> Review -> Integrate) -> Final Validation`

## Step 1: Matrix

Before dispatching, define the Lane Matrix:

| Lane | Files touched | Depends on    | Risk         | Verification          |
| :--- | :------------ | :------------ | :----------- | :-------------------- |
| 1    | [exact paths] | none / Lane N | low/med/high | tests / grep / manual |
| 2    | ...           | ...           | ...          | ...                   |

- **Lane Independence:** Lanes run in the same wave only if their "Files touched" sets are disjoint and dependencies are cleared.
- **Overlap Resolution:** Merge same-file tasks into a single lane (never run overlapping writes in parallel).
- **Avoid Fog of War:** Do not dispatch if paths or dependencies are ambiguous or incomplete.

**Done when:** the Matrix is written with concrete file paths in every "Files touched" cell and a concrete "Depends on" value (such as `none` or a specific lane number) for every lane.

## Step 2: Waves

Topologically sort lanes by `Depends on`. State the wave plan as plain text. Raise `AskUserQuestion` only if the dependency graph is ambiguous or circular and cannot be resolved from the files alone.

**Done when:** every lane is assigned to a wave, and lanes within a wave are proven file-disjoint and dependency-clear.

## Step 3: Dispatch (per wave, in order)

- **Parallel Launch:** Launch wave lanes concurrently in one message (max 10 lanes). Do not pad wave width.
- **Pipelining:** Prep the next wave's prompts while current wave runs (tight loop). Do not launch wave N+1 until wave N completes.
- **Zero-Shot Contract:** Apply the 5-field prompt and model tiering per [subagent-contract.md](references/subagent-contract.md).

**Done when:** every lane in the wave is dispatched in a single message and every dispatch prompt contains all 5 contract fields.

## Step 4: Review (per writer lane)

- **Review Path:** Dispatch a subagent as the `reviewer` on each completed writer lane using [reviewer-prompt.md](references/reviewer-prompt.md).
- **Red Loop:** For `GATE: FAIL`, execute a red loop (max 2 tries total) with the reviewer's findings verbatim.
- **Escalation Policy:** Escalate `GATE: FAIL` (on 2nd try) or `BLOCKED` / `NEEDS_CONTEXT` lanes to the user by name.

**Done when:** every writer lane in the wave is either `GATE: PASS`, or escalated by name, or surfaced as `BLOCKED`/`NEEDS_CONTEXT`.

## Step 5: Integrate & Loop

- **Integrate Wave:** Resolve conflicts by dispatching a subagent as the `conflict-resolver`. Verify integration with the project test suite.
- **Sequential Wave Clear:** Do not advance to wave N+1 until wave N's lanes are resolved or escalated.
- **Loop Control:** If there are remaining waves in the Wave Plan, loop back to Step 3. Otherwise, proceed to Final Validation.

**Done when:** every lane in the wave is tiered (per [subagent-contract.md](references/subagent-contract.md)), the test suite is GREEN for the wave's scope, and any blocked/escalated lane is named.

## Final Validation (after the last wave)

- **Resume Lesson:** On task resume, apply the lesson: verify the task commit exists in `git log` before proceeding.
- **Verification:** Run the full project test suite, `verification-before-completion`, and `request-code-review`.

**Done when:** every task is `GATE: PASS` or escalated-by-name, the full test suite is GREEN, and both `verification-before-completion` and `request-code-review` have run.

### Report Template

Present the consolidated result using the exact schema in [reviewer-prompt.md](references/reviewer-prompt.md):

```
| Lane | VERDICT (implementer) | SPEC_VERDICT | QUALITY_VERDICT | GATE | Action |
| :--- | :-------------------- | :----------- | :-------------- | :--- | :----- |
| 1    | DONE                  | SPEC_PASS    | QUALITY_PASS    | PASS | merged |

Tests: [PASS|FAIL — command run]
Blocked/escalated lanes: [list by name, or "none"]
```

## Strict Rules

- **Asynchronous Yield Handling:** When waiting for background subagents, output a brief status update and stop calling tools to end your turn. Do not run Final Validation or declare overall completion until all waves are fully processed.
- Dispatch stays at depth 1 (see [subagent-contract.md](references/subagent-contract.md)).

## Next Skills

| Skill                                                                        | Use Case                        |
| :--------------------------------------------------------------------------- | :------------------------------ |
| [verification-before-completion](../verification-before-completion/SKILL.md) | Final Validation                |
| [request-code-review](../request-code-review/SKILL.md)                       | Mandatory at Final Validation   |
