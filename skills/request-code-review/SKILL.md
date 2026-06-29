---
name: request-code-review
description: 'Use when implementation is complete and the diff needs a fresh-eye review before merging — security audit, correctness check, or pre-PR validation. Prefer over receive-code-review when requesting a new review rather than acting on existing feedback.'
disable-model-invocation: false
argument-hint: '[target: branch, commit, file, or "current diff"]'
allowed-tools: Bash(git *), Agent
disallowed-tools: Write, Edit
---

# request-code-review

Get an unbiased review by dispatching a fresh-context subagent. Never review your own work in the same thread that wrote it — you already rationalized every decision once; a subagent with no memory of the implementation reads the diff cold, the way a human reviewer would.

## Process Flow

```
Start: Review Request -> 0. Confirm with user -> Pre-Review Checkpoint (tests, context, diffable)
  -> 1. Stat Check (git diff --stat) -> 2. Dispatch Agent (diff-reviewer) -> 3. Check Result Shape
       -- malformed -------> Retry Dispatch (once) -> back to 3. Check Result Shape
       -- failed twice ----> Escalate to user
       -- well-formed -----> 4. Hand Off Result
                                -- PASS -------------> pr-workflow (handoff)
                                -- FAIL (blocking) ---> receive-code-review (handoff)
```

## Step 0: Confirm

Action: AskUserQuestion (no manual "Other" option)
Option 1 (Recommended): Dispatch fresh-context review
Option 2 (Alternative): Inline review for small/uncommitted diffs

## Pre-Review Checkpoint

Verification: Confirm unit tests passed
Context: Get commit range (`git log --oneline -10`) and 1-paragraph summary
Diff Check: If no commits, skip dispatch and request Before/After blocks for inline review

## Phase 1: Dispatch

Stat Check: Run `git diff --stat {{base}}..{{head}}`
Prompt: Fill `references/reviewer-dispatch-prompt.md`
Dispatch: Run `diff-reviewer` (Write/Edit denied by its tools frontmatter)
Safety Check: Run `git status --porcelain` (if modified: discard, restore, re-dispatch)
Output Validation: Require `## Code Review Result` block with `Status`, `Blocking Issues`, `Advisory Issues`, and `What Was Checked` sections (retry once if missing, then fail). Full schema and a filled example live in `references/reviewer-dispatch-prompt.md`.

## Phase 2: Hand Off

Action: Keep subagent output verbatim (do not edit)
On PASS: Prompt user "Run `/pr-workflow`"
On FAIL: Invoke `receive-code-review` (do not fix directly)

## Strict Rules (NEVER)

Self-Review: Forbidden in the same thread
Subagent Writes: Forbidden (enforce tool limits)
Invalid Output: Forbidden (never accept without `## Code Review Result` block)
Isolated Review: Forbidden (diff or before/after blocks required)
