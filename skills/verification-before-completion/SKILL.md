---
name: verification-before-completion
description: |
  Use before declaring any task, feature, or fix complete. Verifies actual behavior matches
  expected through running code and tests — not code inspection alone.
when_to_use: |
  Triggers when the user says: "done", "finished", "looks good", "ready to review",
  "ready to merge", "it should work", or "I think this is complete".
disable-model-invocation: false
---

# Verification Before Completion

## The Rule

**Do NOT report success based on reading code.** Run the code and observe the behavior.

**HARD-GATE: If any applicable checklist item below cannot be verified, the task is NOT complete. Do not report success.**

## Checklist

Before declaring any task done, verify ALL that apply:

- [ ] Run the specific tests for changed code — they must PASS
- [ ] Run the full test suite — no regressions introduced
- [ ] If there are no automated tests: exercise the feature manually and document what you tested
- [ ] If fixing a bug: reproduce the original failure first, then confirm it is gone (not optional — without this you cannot distinguish "fix works" from "test was never catching the bug")
- [ ] Check the diff for debug artifacts: `console.log`, `debugger`, `print(`, `breakpoint()`, `pdb.set_trace()`
- [ ] Review your diff — does every change match what was intended? Nothing extra, nothing missing.

## NEVER

- Never report success based on reading code alone — "it looks correct" is not evidence
- Never say "it should work" without running it
- Never skip reproduction for bug fixes — if you can't show the original failure first, you can't show it's gone
- Never report complete when tests can't run — state explicitly what couldn't be verified and why

## If Verification Fails

Do NOT report success or move on. Either:

- Fix the issue and re-verify from the top of the checklist, OR
- Explicitly state what could not be verified and why, so the user can make an informed decision

Never say "it should work" without evidence.

## Transition

After verification passes:

- For non-trivial changes: invoke `code-review` before finishing
- When moving to PR or delivery: invoke `delivery-manager`
