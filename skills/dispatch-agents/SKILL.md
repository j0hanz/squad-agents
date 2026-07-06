---
name: dispatch-agents
description: Use when implementing a multi-task plan or backlog — independent, dependent, or a mix. Groups tasks into dependency-ordered waves and dispatches up to 10 subagents per wave, in parallel where safe. Prefer over hand-rolling sequential or ad hoc parallel execution.
argument-hint: '[path to plan file, or the tasks to execute]'
allowed-tools: Agent(implementer), Agent(researcher), Agent(reviewer), Agent(conflict-resolver), AskUserQuestion, Bash(git *), Skill(write-commit), Skill(verification-before-completion), Skill(request-code-review)
---

# dispatch-agents

Execute a multi-task plan or backlog by grouping tasks into dependency-ordered waves and dispatching up to 10 subagents per wave, in parallel where the Matrix proves independence.

## When to Use

- A plan or backlog of 2+ tasks — independent, dependent, or a mix.
- Prefer this skill over hand-rolling sequential loops or ad hoc parallel `Agent` calls. The Matrix is the launch gate that makes parallelism safe; without it, concurrent edits collide.

## Process Flow

```
Read tasks -> MATRIX (files / depends-on / risk / verification, per task)
           -> WAVES (topological sort on depends-on; same-file tasks merge into one lane)
           -> per wave, in order:
                DISPATCH  all lanes in ONE message, <=10 lanes (writers: implementer+worktree; read-only: researcher)
                REVIEW    per writer lane, as it reports back: reviewer (combined pass, max 2 tries, else escalate)
                INTEGRATE once the wave's lanes are done/escalated: real tests, conflict-resolver on merge conflicts
-> after the last wave: Final Validation (DoD -> tests -> verification-before-completion -> request-code-review)
```

## Step 1: MATRIX (write it down — don't reason about independence silently)

Before dispatching anything, write the Lane Matrix:

| Lane | Files touched | Depends on    | Risk         | Verification          |
| :--- | :------------ | :------------ | :----------- | :-------------------- |
| 1    | [exact paths] | none / Lane N | low/med/high | tests / grep / manual |
| 2    | ...           | ...           | ...          | ...                   |

This table **is** the launch gate:

- A lane may run in the current wave only if its "Files touched" set is disjoint from every other lane in that wave AND "Depends on" is empty (or already merged from a prior wave).
- Any file overlap → merge those tasks into one lane (same-file tasks never run in parallel).
- Any dependency → that lane moves to a later wave.
- Treat any cell without a concrete answer (not "probably fine") as a sign that lane isn't ready to dispatch.

**Done when:** the Matrix is written with concrete file paths in every "Files touched" cell and a non-empty "Depends on" answer for every lane.

## Step 2: WAVES

Topologically sort the Matrix on `Depends on`. Lanes with `none` (or whose dependencies are all merged) form wave 1; lanes depending only on wave-1 lanes form wave 2; and so on. Same-file tasks merge into one lane before sorting.

State the wave plan as plain text. Raise `AskUserQuestion` only if the dependency graph is ambiguous or circular and cannot be resolved from the files alone.

**Done when:** every lane is assigned to a wave, and lanes within a wave are proven file-disjoint and dependency-clear.

## Step 3: DISPATCH (per wave, in order)

- Re-check the Matrix for the lanes in this wave: zero file overlap, zero unresolved dependencies.
- Launch all lanes for the wave in ONE single message — up to 10 lanes.
- Writer lanes dispatch the named `implementer` agent with `isolation: "worktree"` and `run_in_background: true`. Read-only lanes dispatch the named `researcher` agent.
- Apply an explicit `model:` override at the dispatch call site per the Model Tiering guidance in `references/subagent-contract.md`.
- Every dispatch carries the 5-field contract (SCOPE / OBJECTIVE / CONTEXT / CONSTRAINTS / OUTPUT SCHEMA) from `references/subagent-contract.md` — subagents start cold with no memory of this conversation.
- As soon as a wave launches, do not wait idly — if a next wave is fully scoped, prep its dispatch prompts. But do not launch wave N+1 until wave N's lanes are done or escalated (dependencies must clear first).

**Done when:** every lane in the wave is dispatched in a single message, writers carry `isolation: "worktree"`, and every dispatch has all 5 contract fields.

## Step 4: REVIEW (per writer lane, as it reports back)

- As each writer lane returns `DONE` or `DONE_WITH_CONCERNS`, dispatch the named `reviewer` agent with the combined spec+quality dispatch template from `references/reviewer-prompt.md`.
- The reviewer returns the combined schema: `SPEC_VERDICT: SPEC_PASS | SPEC_FAIL`, `QUALITY_VERDICT: QUALITY_PASS | CRITICAL | IMPORTANT | MINOR`, and derived `GATE: PASS | FAIL`.
- `GATE: PASS` (i.e. `SPEC_PASS` + `QUALITY_PASS` or `MINOR`) → advance the lane.
- `GATE: FAIL` on 1st attempt → dispatch a fresh `implementer` with the reviewer's findings verbatim; re-run the reviewer. Max 2 tries.
- 2nd failure → escalate the lane to the user BY NAME. Do not retry a third time. No split-into-two-agents fallback — the combined reviewer is the only review path.
- `BLOCKED` or `NEEDS_CONTEXT` from the implementer → surface to the user before continuing; do not dispatch the reviewer.
- Read-only `researcher` lanes do not get reviewed; tier their verdict per `references/subagent-contract.md` and integrate.

**Done when:** every writer lane in the wave is either `GATE: PASS`, or escalated by name, or surfaced as `BLOCKED`/`NEEDS_CONTEXT`.

## Step 5: INTEGRATE (once the wave's lanes are done/escalated)

- Run the real test suite — never merge on a self-reported verdict alone.
- If a Git merge conflict occurs, dispatch the named `conflict-resolver` agent. If it returns `VERDICT: BLOCKED`, escalate to the user.
- Tier every lane into CRITICAL / IMPORTANT / MINOR per `references/subagent-contract.md` for the final report.
- Move to the next wave only once this wave's lanes are merged or escalated. Never advance while a blocked lane is unresolved.

**Done when:** every lane in the wave is tiered, the test suite is GREEN for the wave's scope, and any blocked/escalated lane is named.

## Final Validation (after the last wave)

- **DoD:** Every task clears the project-wide [Definition of Done](../verification-before-completion/references/definition-of-done.md) — independently verified, never on the implementer's self-report.
- **Test:** Run the full project test suite.
- **Verify:** Run `verification-before-completion`.
- **Review:** Run `request-code-review` (mandatory).
- **Done when:** every task is `GATE: PASS` or escalated-by-name, the full test suite is GREEN, and both `verification-before-completion` and `request-code-review` have run.

### Report Template

Present the consolidated result in this exact shape:

```
| Lane | VERDICT (implementer) | SPEC_VERDICT | QUALITY_VERDICT | GATE | Action |
| :--- | :-------------------- | :----------- | :-------------- | :--- | :----- |
| 1    | DONE                  | SPEC_PASS    | QUALITY_PASS    | PASS | merged |
| 2    | DONE_WITH_CONCERNS    | SPEC_PASS    | MINOR           | PASS | merged, logged |

Tests: [PASS|FAIL — command run]
Blocked/escalated lanes: [list by name, or "none"]
```

## Strict Rules

- **No overlapping writes:** The Matrix is the launch gate. Two lanes in the same wave never touch overlapping paths — same-file tasks merge into one lane before dispatch.
- **No assumed context:** Every dispatch carries the 5-field contract (SCOPE / OBJECTIVE / CONTEXT / CONSTRAINTS / OUTPUT SCHEMA) from `references/subagent-contract.md`. Subagents start cold.
- **Wave width sized to genuine independence, max 10 lanes:** A wave contains only lanes the Matrix proves are independent. Never pad a wave to hit the 10-lane cap — 3 genuinely independent lanes is correct, 10 padded ones is slop.
- **Dispatch stays at depth 1:** None of the four named agents (`implementer`, `researcher`, `reviewer`, `conflict-resolver`) spawn further subagents. The orchestrator (main thread) is the only dispatcher.
- **No blind trust:** Real tests, independent verification. A `VERDICT: DONE` or `GATE: PASS` is a claim; the test suite is proof.
- **No hidden skips:** Name every escalated or blocked lane in the final report. Never bury a skip in a summary.

## Failure Modes (check before you call it done)

- Concurrent edits collided because a Matrix "Files touched" cell was guessed instead of verified.
- An implementer's `DONE` was trusted instead of the reviewer reading the diff and the test suite running.
- A blocked or skipped lane wasn't surfaced in the final report — it silently didn't happen.
- A wave was padded to 10 lanes when only 3 were genuinely independent — the extra lanes collided or duplicated work.
- A named agent spawned a sub-subagent, breaking depth-1 dispatch and flooding the orchestrator's context.
- On resume, a task's completion was assumed instead of verified against `git log` — always confirm the task's commit exists before treating it as done.

## Next Skills

- `write-commit`: Apply commit rules for each task's staged changes before final validation.
- `verification-before-completion`: Run this for Final Validation handoff.
- `diagnose`: Run this for merge/test failure investigation.
- `request-code-review`: Mandatory at Final Validation.
