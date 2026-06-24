---
name: multi-agent-dispatch
description: "Executes multiple independent task descriptions in parallel by fanning out to isolated, single-purpose subagents, producing integrated file edits, test results, and a consolidated execution report. Trigger on: 'in parallel', 'dispatch agents', 'fan out', 'multi-agent-dispatch', 'independent tasks', 'concurrent execution'. Also triggers when the user requests simultaneous task runs, concurrent agent dispatch, or parallel operations on separate codebase areas. Always prefer this skill over multi-agent-development when tasks have no shared file changes, no database or file dependencies, and do not require ordered execution, and over planning when the goal is task implementation rather than layout and analysis."
disable-model-invocation: false
argument-hint: '[the independent tasks to parallelize]'
---

# multi-agent-dispatch

Maximize efficiency through parallel execution across isolated problem domains. Independent domains (no shared state) → this skill. Shared mutable state or dependencies → `multi-agent-development` instead; the Lane Matrix below is the test.

```
GROUP -> MATRIX -> SELECT -> LAUNCH(background) ─┬─> INTEGRATE (on notify)
                                  |               |        ^
                                  └─ next batch ──┘    retry (partial failure)
```

Batches pipeline, they don't queue: launching batch N in the background is the signal to start scoping batch N+1, not a reason to wait.

## Strict Rules

- **NO Overlapping Writes:** Never launch parallel agents editing the same files. Use sequential execution instead.
- **NO Assumed Context:** Subagents start blank. Put every needed fact directly into the prompt.
- **MAX 3 Agents in the foreground at once:** that cap is about how many results you read and merge together, not how many can be running. Lanes dispatched with `run_in_background` don't occupy a foreground slot — you get notified on completion instead of blocking on it, so a 4th+ lane can launch the moment its own dependencies clear, without waiting on batch N's INTEGRATE.
- **NO Blind Trust:** Agents make mistakes. You MUST run the test suite to prove their work is correct.
- **NO Hidden Skips:** If you skip a check or a lane, say so in the final report. Never bury it in a summary.

## Step 1: GROUP

Form task groups yourself from the work already visible (a plan, a backlog, several independent fix-its) and state them as plain text — don't stop on `AskUserQuestion` by default, that just adds a wait for something the file list already tells you. Ask only when grouping is genuinely ambiguous (unclear whether two tasks actually share state or a file).

Heuristic, not a rule: parallel dispatch pays off most once you have 3+ tasks (or failures) in separate files with unrelated causes. Below that, sequential is usually simpler to reason about — don't force parallelism for its own sake.

## Step 2: MATRIX (write it down — don't reason about independence silently)

Before assigning roles or launching anything, write this table:

| Lane | Files touched | Depends on    | Risk         | Verification          |
| :--- | :------------ | :------------ | :----------- | :-------------------- |
| 1    | [exact paths] | none / Lane N | low/med/high | tests / grep / manual |
| 2    | ...           | ...           | ...          | ...                   |

This table **is** the dispatch gate:

- A lane may run in the current parallel batch only if its "Files touched" set is disjoint from every other lane in that batch AND "Depends on" is empty (or already merged).
- Any overlap or dependency → that lane moves to a later batch, or to sequential `multi-agent-development`.
- If you can't fill every cell with a concrete answer (not "probably fine"), you are not ready to parallelize that lane.

## Step 3: SELECT

Assign roles using the Role Vocabulary defined in `../multi-agent-development/references/subagent-contract.md` (Investigator / Writer / Researcher). **MANDATORY:** read that file before dispatching — it defines the prompt contract every dispatch below depends on.

- Writers MUST use `isolation: worktree` to prevent overlapping edits.

## Step 4: LAUNCH

- Re-check the matrix for the lanes in this batch: zero file overlap, zero unresolved dependencies.
- Launch all agents for a batch in ONE single message.
- **Default every Writer lane to `run_in_background: true`.** Foreground (blocking) dispatch is the exception now, reserved for a lane whose result you need before you can write the next prompt. Background is the default because the harness notifies you on completion — you are not "waiting" in either case, but background lets you keep working (prep the next batch's Matrix, answer the user, start a lane with no dependency on this one) instead of sitting idle until the slowest agent in the batch returns.
- As soon as a lane is launched in the background, immediately start GROUP/MATRIX for the next batch rather than waiting at this step — don't let "batch N is running" block "start scoping batch N+1."
- Track every in-flight background lane by name/id. When notified of a completion, INTEGRATE that lane immediately rather than batching notifications up.

## Step 5: INTEGRATE

Consolidate each agent's `VERDICT` / `SUMMARY` / `EVIDENCE` (per the contract) into one report, tiered the same way `multi-agent-development`'s quality reviewer is:

- **CRITICAL** — lane's work is wrong or broken: discard, do not merge, re-dispatch fresh.
- **IMPORTANT** — works but needs a fix before merge: re-dispatch with the issue verbatim.
- **MINOR** — cosmetic: merge now, log for later.

Then run the real test suite. A `VERDICT: SUCCESS` report is a claim, not proof — never merge on the report alone. A lane is mergeable only once its work clears the project-wide [Definition of Done](../verification-before-completion/references/definition-of-done.md), independently verified.

### Report Template

Present the consolidated result to the user in this exact shape:

```
| Lane | VERDICT | Tier                          | Action                          |
| :--- | :------ | :----------------------------- | :------------------------------- |
| 1    | ...     | PASS/CRITICAL/IMPORTANT/MINOR  | merged / re-dispatched / discarded |

Tests: [PASS|FAIL — command run]
Skipped/blocked lanes: [list, or "none"]
```

### Partial Failures

- Keep and save the successful, tested lanes.
- Re-run only the failed lanes with fresh agents.
- If a lane failed because it secretly depended on another lane finishing first, stop parallel work for that pair — update the Matrix and switch them to sequential.
- Always report blocked or failed lanes to the user, tiered as above.

## Failure Modes (check before you call it done)

- Concurrent edits collided because a Matrix "Files touched" cell was guessed instead of verified.
- A lane self-reported `SUCCESS` and that report was trusted instead of the test suite.
- A skipped lane or check got mentioned nowhere instead of surfaced as `BLOCKED`/`CRITICAL`.
- A background agent kept running with nobody checking on it after the batch moved on.

## Integration Rules

- **Read:** Agents can read the same files.
- **Write:** Agents CANNOT edit the same files.
- **Validate:** Run tests on all agent work. Never just trust the report.

## Success Criteria

All results are combined, tests are GREEN, every skipped/blocked lane is named in the report, and tasks are passed to `verification-before-completion`.

## Worked Example

6 test failures across 3 files, unrelated root causes. GROUP → 3 lanes. MATRIX:

| Lane | Files touched            | Depends on | Risk | Verification                |
| :--- | :----------------------- | :--------- | :--- | :-------------------------- |
| 1    | `tool-approval.test.ts`  | none       | low  | `vitest run tool-approval`  |
| 2    | `batch-complete.test.ts` | none       | med  | `vitest run batch-complete` |
| 3    | `agent-abort.test.ts`    | none       | low  | `vitest run agent-abort`    |

Files disjoint, no dependencies → all three launch in ONE message, each a Writer with `isolation: worktree`, `run_in_background: true`. As each notifies, INTEGRATE it. Then run the full suite (not the per-lane greps the agents reported):

```
| Lane | VERDICT | Tier | Action |
| :--- | :------ | :--- | :----- |
| 1    | SUCCESS | PASS | merged |
| 2    | SUCCESS | MINOR | merged, logged naming nit |
| 3    | SUCCESS | PASS | merged |

Tests: PASS — `vitest run` (all 6 green)
Skipped/blocked lanes: none
```

Outcome: 6 failures cleared concurrently, zero integration conflicts — because the Matrix proved the file sets were disjoint _before_ launch, not after.

## Next Skills

- `verification-before-completion`: Run this to check final work.
- `multi-agent-development`: Run this if tasks depend on each other (sequential).
- `diagnose`: Run this if combining the code causes errors.
- `context-optimizer`: Run this if context bloats while collecting parallel results.
