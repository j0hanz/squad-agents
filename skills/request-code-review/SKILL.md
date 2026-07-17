---
name: request-code-review
description: 'Use when a verified diff needs a fresh-eye review before merging. Prefer over receive-code-review when requesting a new review rather than acting on feedback.'
disable-model-invocation: false
argument-hint: '[target: branch, commit, or file]'
allowed-tools: 'Bash(git diff *), Bash(git status *), Bash(git log *), Bash(git merge-base *), Agent, AskUserQuestion, Read'
disallowed-tools: Write, Edit
---

# request-code-review

A subagent reviews the diff with fresh context, reading it like a human reviewer.

## Step 0: Confirm

Action: Dispatch a subagent as a read-only reviewer with the base..head diff (or, if uncommitted, the working-tree diff passed as a text block).

## Pre-Review Checkpoint

- **Required Inputs**:
  1. **Verified**: confirm verification-before-completion has run, or paste fresh test output.
  2. **Commit Range / Diff Source**: Determine base and head commit SHAs. If target is a branch, find the merge base using `git merge-base origin/main HEAD`.
  3. **Plan/Requirements Summary**: Obtain a 1-paragraph summary of the change (either from git commit logs or by asking the user).
- **Required Outputs**:
  1. A verified base-to-head git diff stat. If the diff is empty and no uncommitted changes exist, abort the process and report to the user.
  2. A fully populated configuration for the dispatch prompt.

## Phase 1: Dispatch

1. **Stat Check**: Run `git diff --stat {{base_commit}}..{{head_commit}}` to verify files changed.
2. **Safety Check (Baseline)**: Run `git status --porcelain` and record any dirty files. Verify no files are altered during dispatch.
3. **Prompt Compilation**: Fill [reviewer-dispatch-prompt.md](references/reviewer-dispatch-prompt.md).
   - Map `{{base_commit}}` and `{{head_commit}}` to the resolved SHAs.
   - Map `{{repo_path}}` to the absolute path of the workspace.
   - Map `{{plan_or_requirements_summary}}` to the 1-paragraph summary.
   - Map `{{patterns_reference_path}}` to the absolute path of `.github/review-patterns.md` if it exists; otherwise, populate as "N/A".
4. **Dispatch**: Dispatch a subagent as the read-only reviewer.
   - _Constraint_: Force-enable read-only mode for the subagent by explicitly denying write/edit tools in the agent invocation config.
5. **Safety Check (Post-Dispatch)**: Run `git status --porcelain` again. Compare with the baseline. If any modifications were made to the working tree, immediately abort, discard changes (if safe), and report a safety violation.
6. **Output Validation**: Ensure the subagent's response strictly contains the required headers (`## Code Review Result`, `**Status**:`, `### Blocking Issues`, `### Advisory Issues`, and `### What Was Checked`). If any header is missing or malformed, retry dispatch exactly once with a reminder prompt. If the second attempt fails, abort the process.

## Phase 2: Hand Off

**Execution Guardrail**: Do not proceed until subagent execution completes and validates.

Action: Keep subagent output verbatim (do not edit)
On PASS: Prompt user "Changes are ready — commit and push / open a PR."
On FAIL: Invoke `receive-code-review` (do not fix directly)

## Strict Rules (NEVER)

- **NEVER** review your own work in the same thread/context that wrote it. You MUST dispatch a fresh-context subagent reviewer.
- **NEVER** run git/file commands that mutate the working tree or index (such as `git stash`, `git checkout`, or `git reset`) to force a clean status check. If the working tree is modified, you MUST abort and report.
- **NEVER** manually edit, correct, or translate the subagent's review output. It must be kept verbatim.
- **NEVER** fix findings directly when the status is `FAIL`. You MUST invoke the `receive-code-review` skill.
- **NEVER** dispatch the review prompt with unresolved `{{placeholders}}`. Ask the user if any values are unknown.
- **NEVER** accept malformed subagent output. You may retry once; if it fails again, you must fail the review process immediately.

## Completion Criteria

Before completing this task, you must verify that:

1. [ ] **Test Verification**: The run log shows explicit verification that unit tests passed immediately prior to the review request.
2. [ ] **Clean Status Verification**: `git status --porcelain` was executed and yielded no output before the reviewer was dispatched.
3. [ ] **Zero Placeholders**: All placeholders (`{{base_commit}}`, `{{head_commit}}`, etc.) were fully replaced with actual, verified values.
4. [ ] **Verbatim Output**: The final output presented to the user contains the exact, unaltered Markdown output from the subagent reviewer.
5. [ ] **Next Steps Executed**: The agent has either prompted the user that the diff is ready to commit and push (if PASS) or invoked the `receive-code-review` skill (if FAIL), without performing direct fixes.
