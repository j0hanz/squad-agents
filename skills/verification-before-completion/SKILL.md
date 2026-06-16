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

**CI-only environments:** If tests can only run in CI (no local runner available), do not declare success before CI completes. State: "Tests are queued in CI — I cannot confirm PASS until the pipeline finishes. Proceed only after CI returns green." Do not proceed to `code-review` or final delivery until CI confirms PASS.

**No test suite exists:** If there are no automated tests and the feature cannot be exercised manually (e.g., a background job, a webhook handler), document exactly what was changed, what the expected behavior is, and what would need to be true for the change to be correct. Mark verification as INCOMPLETE and surface it to the user before proceeding.

## Transition

Once all applicable checklist items are confirmed (whether verified by you or reported by the developer):

- **For non-trivial changes:** invoke `code-review` before finishing
- **When moving to PR or delivery:** prompt the user to run `/github-automation` — this skill requires user invocation and cannot be triggered automatically

---

## Expert Patterns

- **The "N-1" Test:** To prove a fix works, delete the changed code, run the tests to confirm they FAIL (reproduction), then re-apply the changes and confirm they PASS. This eliminates "false greens" where the test wasn't actually checking the fix.
- **Edge Case Blitz:** Beyond the happy path, explicitly test for `null`, `undefined`, empty strings, zero values, and boundary conditions (e.g., max integer, empty arrays).
- **Log Diffing:** For changes with side effects (e.g., database writes, network calls), check the logs _before_ and _after_ the change. Ensure no new error levels or unexpected warnings are being emitted silently.
- **Environment Parity Check:** If the bug is machine-specific or only happens in CI, document exactly how your local environment differs (OS, Node version, env vars) to help the reviewer understand why a local pass might not guarantee a CI pass.

## Common Failure Modes

- **Green-Wash:** All tests pass, but the tests were the wrong ones, had no assertions, or were mocking away the very behavior you intended to fix. **Fix:** Review the test code as carefully as the implementation code.
- **Shadow Regressions:** The primary tests pass, but a distant, unmonitored part of the system is failing due to a shared dependency or global state change. **Fix:** Run a broad, shallow "smoke test" of the entire application if the change touches global state.
- **The "Works on my machine" Trap:** Relying on local state (e.g., a local database, untracked files, specific environment variables) that won't exist in production or CI. **Fix:** Use `git status` to ensure all necessary files are tracked and check `.env.example` matches your local setup.
- **Verification Fatigue:** Skipping the full test suite because "it's just a one-line change." **Fix:** Automate the "run everything relevant" command and make it part of your muscle memory.

A clean test run is necessary but not sufficient for shipping. The transition steps exist to catch issues that verification alone doesn't surface.
