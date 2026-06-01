---
name: verification-before-completion
description: "Verify before completion. Trigger when the USER says 'looks good', 'ready to review', 'ready to merge', 'mark as done', or when Claude is about to report a task complete. Test actual behavior — not code inspection alone."
disable-model-invocation: false
---

# Verification Before Completion

## The Core Idea

**Do NOT confirm work is complete based on reading code.** Execution evidence must exist before reporting success. Code inspection tells you what the code says; only running it tells you what it does.

Crucially: that execution evidence can come from the developer. When someone tells you "I ran the tests and they all pass" or "I confirmed the original bug is reproduced then gone," **that is the evidence.** Your job is to make sure verification actually happened — not to personally re-execute every command.

## Scenario A: Developer Has Already Verified

If the developer confirms they've covered the relevant checklist items, accept it and move to the Transition step:

> "All 847 tests pass. Debug artifacts check: clean. Diff review: all changes are intentional."
> → **Verification complete.** Proceed to the Transition step below.

Do not ask to re-run things yourself, and do not treat self-reported verification as insufficient. The skill's purpose is to ensure verification happened, not to be the agent performing it.

## Scenario B: Verification Is Still Needed

If the developer says "it should work" or "looks correct" without reporting actual execution — or is asking you to confirm completion on their behalf — work through this checklist:

### Checklist

Before declaring any task done, verify ALL that apply:

- [ ] Run the specific tests for changed code — they must PASS
- [ ] Run the full test suite — no regressions introduced
- [ ] If there are no automated tests: exercise the feature manually and document what you tested (input given, expected behavior, actual behavior observed)
- [ ] If fixing a bug: reproduce the original failure first, then confirm it is gone
  - Not optional. Without seeing the failure, you cannot distinguish "fix works" from "test was never catching the bug in the first place."
- [ ] Check the diff for debug artifacts: `console.log`, `debugger`, `print(`, `breakpoint()`, `pdb.set_trace()`
- [ ] Review your diff — does every change match what was intended? Nothing extra, nothing missing.

### What isn't sufficient

- "It looks correct" — code review shows what was written, not whether it works at runtime
- "I'm confident" / "should work" — confidence is not evidence
- "The new tests pass" — new tests passing does not confirm no regressions in existing code
- "The CI failure is unrelated to my code" — you can't distinguish "my code is fine" from "my code is also broken" without seeing tests actually pass

### If verification cannot complete

State explicitly what could not be verified and why, so the user can decide how to proceed. Never silently declare success or let an untestable claim stand.

## Transition

Once all applicable checklist items are confirmed (whether verified by you or reported by the developer):

- **For non-trivial changes:** invoke `code-review` before finishing
- **When moving to PR or delivery:** invoke `delivery-manager`

A clean test run is necessary but not sufficient for shipping. The transition steps exist to catch issues that verification alone doesn't surface.
