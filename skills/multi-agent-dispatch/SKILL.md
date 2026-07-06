---
name: multi-agent-dispatch
description: 'Use when executing multiple tasks that are fully independent — no shared files, no dependencies between them, no required ordering. Prefer over multi-agent-development when tasks are file-disjoint and can safely run concurrently.'
disable-model-invocation: false
argument-hint: '[the independent tasks to parallelize]'
allowed-tools: Agent(implementer), Agent(researcher), Agent(conflict-resolver), AskUserQuestion, Bash(git *)
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
- **MAX 3 Agents in the foreground at once:** the cap counts only results read and merged in one sitting, not how many agents can be running.
- **Background lanes are exempt from that cap:** a lane launched with `run_in_background` doesn't occupy a foreground slot — the harness notifies on completion instead of blocking on it, so a 4th+ lane can launch the moment its own dependencies clear, without waiting on batch N's INTEGRATE. If the harness has no background/notify primitive, treat MAX 3 as a hard concurrency cap instead and run remaining lanes in sequential batches of ≤3.
- **NO Blind Trust:** Agents make mistakes. Run the test suite to prove their work is correct — never merge on a self-reported verdict alone.
- **NO Hidden Skips:** Name any skipped check or lane in the final report. Never bury it in a summary.

## Step 1: GROUP

Form task groups from the work already visible (a plan, a backlog, several independent fix-its) and state them as plain text — don't stop on `AskUserQuestion` by default, that just adds a wait for something the file list already answers. Ask only when grouping is genuinely ambiguous (unclear whether two tasks actually share state or a file).

Heuristic, not a rule: parallel dispatch pays off most once there are 3+ tasks (or failures) in separate files with unrelated causes. Below that, sequential is usually simpler to reason about — don't force parallelism for its own sake.

**Done when:** every task group is stated as plain text with its file list and no `AskUserQuestion` is still pending.

## Step 2: MATRIX (write it down — don't reason about independence silently)

Before assigning roles or launching anything, write this table:

| Lane | Files touched | Depends on    | Risk         | Verification          |
| :--- | :------------ | :------------ | :----------- | :-------------------- |
| 1    | [exact paths] | none / Lane N | low/med/high | tests / grep / manual |
| 2    | ...           | ...           | ...          | ...                   |

This table **is** the dispatch gate:

- A lane may run in the current parallel batch only if its "Files touched" set is disjoint from every other lane in that batch AND "Depends on" is empty (or already merged).
- Any overlap or dependency → that lane moves to a later batch, or to sequential `multi-agent-development`.
- Treat any cell without a concrete answer (not "probably fine") as a sign that lane isn't ready to parallelize.

**Done when:** the Lane Matrix table is written with concrete file paths in every "Files touched" cell and a non-empty "Depends on" answer for every lane.

## Step 3: SELECT

Assign roles: **Investigator** (read-only, traces root cause), **Writer** (dispatches the named `implementer` agent, `isolation: worktree`), **Researcher** (read-only, reports file paths/usages).

Writer lanes dispatch `subagent_type: implementer` (`agents/implementer.md`), not generic `general-purpose` — it already requires `isolation: worktree` and returns its own fixed output schema (see Step 5: INTEGRATE), so skip the generic five-field/VERDICT-SCHEMA setup for Writer lanes specifically. Investigator and Researcher lanes MUST dispatch the named `researcher` agent (`agents/researcher.md`) — this enforces hard read-only tool restrictions at the harness level.

For the full contract (five required prompt fields), common mistakes, specialist-routing table, large-artifact `.claude/dispatch/` handoff rule, and Model Tiering table, see `../multi-agent-development/references/subagent-contract.md#prompt-fields` — read it before dispatching when available, and apply an explicit `model:` override at the dispatch call site per the tiering guidance.

- Writers MUST use `isolation: worktree` to prevent overlapping edits — state it explicitly in the dispatch call since `isolation` is dispatcher-side guidance, not an enforced agent property.

**Done when:** every lane has an assigned role (Investigator/Writer/Researcher) and Writer lanes specify `isolation: worktree` at the dispatch call site.

## Step 4: LAUNCH

- Re-check the matrix for the lanes in this batch: zero file overlap, zero unresolved dependencies.
- Launch all agents for a batch in ONE single message.
- **Default every Writer lane to `run_in_background: true`.** Reserve foreground (blocking) dispatch for a lane whose result is needed before writing the next prompt. The harness notifies on completion either way; background just keeps the next batch's Matrix, a user reply, or an independent lane moving instead of sitting idle until the slowest agent in the batch returns.
- As soon as a lane launches in the background, start GROUP/MATRIX for the next batch immediately — "batch N is running" is not a reason to delay scoping batch N+1.
- Track every in-flight background lane by name/id. When notified of a completion, INTEGRATE that lane immediately rather than batching notifications up.

**Done when:** every lane in the batch has disjoint files, empty `Depends on`, and is tracked by name/id before any agent is dispatched.

## Step 5: INTEGRATE

Each lane reports against a different schema depending on its role — interpret accordingly before tiering:

<!-- # mirror of subagent-contract.md#prompt-fields — the VERDICT enum tokens below are duplicated from the canonical contract; the tier-mapping prose (DONE -> QUALITY_PASS/merged; etc.) is dispatch-local integration guidance that has no canonical home in subagent-contract.md, so both copies are kept per GATE-D. -->

- **Writer lanes (`implementer`):** Returns `VERDICT: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]` + SUMMARY + FILES_CHANGED + COMMIT + CONCERNS/BLOCKER/QUESTION. Map to a tier: `DONE` → QUALITY_PASS/merged; `DONE_WITH_CONCERNS` → MINOR or IMPORTANT depending on the concern's severity (merge-and-log, or re-dispatch with the concern verbatim); `BLOCKED` → CRITICAL/discarded, re-dispatch fresh only after resolving the blocker; `NEEDS_CONTEXT` → CRITICAL/discarded, re-dispatch with the question answered, not retried verbatim.
- **Investigator/Researcher lanes (`researcher`):** Returns the generic `VERDICT/FILES_TOUCHED/SUMMARY/EVIDENCE` contract (where `VERDICT` is `SUCCESS | FAILURE | BLOCKED | NEEDS_CONTEXT`) — tier its dispatch-specific VERDICT enum the same CRITICAL/IMPORTANT/MINOR way as before.

Tier every lane, regardless of schema, into the same three buckets (CRITICAL, IMPORTANT, MINOR) used here and by `multi-agent-development`'s quality reviewer — see `../multi-agent-development/references/quality-reviewer-prompt.md` for the canonical definitions.

### Git Merge Conflict Resolution

If a Git merge conflict occurs during integration, do NOT immediately abort or escalate to the user:

1. Dispatch the specialized `conflict-resolver` agent (`agents/conflict-resolver.md`) to resolve the conflict markers.
2. The conflict resolver will read the conflicted files, resolve the edits, run tests, and commit the resolution.
3. If it returns `VERDICT: DONE`, proceed with the merge. If it returns `VERDICT: BLOCKED`, escalate the conflict to the user.

### Context Compaction & Token Hygiene

See the Context Compaction rule in `skills/multi-agent-development/SKILL.md#Operational Rules`: prune intermediate subagent logs, thinking steps, and full file diffs once a lane is integrated, keeping only a high-level summary and the merge commit hash.

Then run the real test suite. Neither implementer's `DONE` nor a researcher's `VERDICT: SUCCESS` is proof by itself — never merge on either report alone. A lane is mergeable only once its work clears the project-wide [Definition of Done](../verification-before-completion/references/definition-of-done.md), independently verified.

### Report Template

Present the consolidated result to the user in this exact shape:

```
| Lane | VERDICT (native schema)                         | Tier                          | Action                          |
| :--- | :----------------------------------------------- | :----------------------------- | :------------------------------- |
| 1    | DONE/DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT (Writer) or SUCCESS/FAILURE/BLOCKED (Investigator/Researcher) | QUALITY_PASS/CRITICAL/IMPORTANT/MINOR  | merged / re-dispatched / discarded |

Tests: [PASS|FAIL — command run]
Skipped/blocked lanes: [list, or "none"]
```

### Partial Failures

- Keep and save the successful, tested lanes.
- Re-run only the failed lanes with fresh agents.
- If a lane failed because it secretly depended on another lane finishing first, stop parallel work for that pair — update the Matrix and switch them to sequential.
- Always report blocked or failed lanes to the user, tiered as above.

**Done when:** every lane is tiered (CRITICAL/IMPORTANT/MINOR), the real test suite is GREEN, the report template is filled, and any skipped/blocked lane is named in the report.

## Failure Modes (check before calling it done)

- Concurrent edits collided because a Matrix "Files touched" cell was guessed instead of verified.
- A lane self-reported `SUCCESS` and that report was trusted instead of the test suite.
- A skipped lane or check got mentioned nowhere instead of surfaced as `BLOCKED`/`CRITICAL`.
- A background agent kept running with nobody checking on it after the batch moved on.

## Success Criteria

All results are combined, tests are GREEN, every skipped/blocked lane is named in the report, and tasks are passed to `verification-before-completion`.

## Worked Example

6 test failures across 3 files, unrelated root causes. GROUP → 3 lanes. MATRIX:

| Lane | Files touched            | Depends on | Risk | Verification                |
| :--- | :----------------------- | :--------- | :--- | :-------------------------- |
| 1    | `tool-approval.test.ts`  | none       | low  | `vitest run tool-approval`  |
| 2    | `batch-complete.test.ts` | none       | med  | `vitest run batch-complete` |
| 3    | `agent-abort.test.ts`    | none       | low  | `vitest run agent-abort`    |

Files disjoint, no dependencies → all three launch in ONE message, each dispatching `implementer` with `isolation: worktree`, `run_in_background: true`. As each notifies, INTEGRATE it. Then run the full suite (not the per-lane greps the agents reported):

```
| Lane | VERDICT (implementer) | Tier | Action |
| :--- | :--------------------- | :--- | :----- |
| 1    | DONE                    | QUALITY_PASS | merged |
| 2    | DONE_WITH_CONCERNS      | MINOR | merged, logged naming nit from CONCERNS |
| 3    | DONE                    | QUALITY_PASS | merged |

Tests: PASS — `vitest run` (all 6 green)
Skipped/blocked lanes: none
```

Outcome: 6 failures cleared concurrently, zero integration conflicts — because the Matrix proved the file sets were disjoint _before_ launch, not after.

## Next Skills

- `verification-before-completion`: Run this to check final work.
- `multi-agent-development`: Run this if tasks depend on each other (sequential).
- `diagnose`: Run this if combining the code causes errors.
