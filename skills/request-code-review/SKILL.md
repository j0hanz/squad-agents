---
name: request-code-review
description: 'Use when implementation is complete and the diff needs a fresh-eye review before merging — security audit, correctness check, or pre-PR validation. Prefer over receive-code-review when requesting a new review rather than acting on existing feedback.'
disable-model-invocation: false
argument-hint: '[target: branch, commit, file, or "current diff"]'
allowed-tools: Bash(git *), Agent(diff-reviewer), AskUserQuestion, Read
disallowed-tools: Write, Edit
---

# request-code-review

Get an unbiased review by dispatching a fresh-context subagent. Never review your own work in the same thread that wrote it — you already rationalized every decision once; a subagent with no memory of the implementation reads the diff cold, the way a human reviewer would.

## Process Flow

# mirror of "Step 0: Confirm" -> "Pre-Review Checkpoint" -> "Phase 1: Dispatch" -> "Phase 2: Hand Off" below — canonical flow incl. retry-once-then-escalate and PASS->pr-workflow / FAIL->receive-code-review branches.

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
Safety Check: Run `git status --porcelain` (if modified: abort and report; do not mutate working tree)
Output Validation: Require the reviewer's output to match the schema in `references/reviewer-dispatch-prompt.md` (retry once if it doesn't, then fail).

## Phase 2: Hand Off

Action: Keep subagent output verbatim (do not edit)
On PASS: Prompt user "Run `/pr-workflow`"
On FAIL: Invoke `receive-code-review` (do not fix directly)

## Strict Rules (NEVER)

# mirror of the NEVERs stated inline in the step prose: intro (self-review forbidden in-thread), Phase 1 Dispatch/Safety Check (subagent writes forbidden via tool limits), Output Validation (malformed reviewer output rejected — retry once then fail), Pre-Review Checkpoint Diff Check (isolated review forbidden — diff or before/after blocks required).
