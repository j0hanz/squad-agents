---
name: verification-before-completion
description: 'Use when code changes are declared done and need pressure-testing that declared-done actually means done — gather execution evidence (run tests or manual repro, paste fresh output) before review or release. Prefer over request-code-review when the implementation has not yet been verified by execution.'
disable-model-invocation: false
allowed-tools: AskUserQuestion, Bash, Read, Grep
---

# verification-before-completion

Guarantee operational correctness through execution evidence. **NEVER** confirm based on reading code alone.

## Process Flow

```
Start: Ready to Complete
  -> 1. Mandatory Checklist (tests, manual, sweep, diff)
  -> 2. Gather Evidence (runner output / exercise log)
  -> 3. Decision Logic (see table below)
```

## 1. Mandatory Checklist

The standing bar every change clears is [`references/definition-of-done.md`](references/definition-of-done.md) — the project-wide Definition of Done. The items below are that bar applied here; read it first.

**action:** Verify all items before completion.

The full checklist lives in [`references/definition-of-done.md`](references/definition-of-done.md) (Tests, Build/types, Lint, No debug residue, Diff, Acceptance criteria, Callers) — read it first. The items below are the delta this skill adds on top of that bar:

- [ ] **Manual:** Documented inputs/outputs if no automation.
- [ ] **Bug Fix:** Confirm reproduction failure then confirm success.

## 2. Decision Logic

**"Non-trivial" heuristic:** a change is non-trivial unless it is a single-file edit of 20 lines or fewer with no new public surface and no logic branching. This is a bias-toward-caution heuristic, not a precise boundary — when in doubt, treat the change as non-trivial. Self-classifying a change as trivial to skip the review handoff below is itself a verification failure.

**Trivial -> done when** (all must hold, each observable — prose alone fails):

- (a) `git diff --stat` shows exactly **1 file** and **1 line** changed (1 ins + 1 del); AND
- (b) the change is a comment/doc/typo with **no executable surface** (no statement, branch, or signature touched); AND
- (c) the relevant suite — or, if no test touches the file, build + lint — is green, with pasted output from a run **after the last edit**.

Any deviation from (a)/(b)/(c) → non-trivial → route to `request-code-review`. "It's just a typo" without (c) is not done.

| Status             | Action                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| :----------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CI-Only**        | Stop. Report: "Blocked by CI. Wait for pipeline."                                                                                                                                                                                                                                                                                                                                                                                          |
| **No Test Suite**  | **Gate, not a pass:** before marking INCOMPLETE, you MUST write at least one executable smoke/characterization test or manual reproduction script proving the change works (see §3 Manual Verification Template) — a prose rationale alone is not sufficient. Only after that evidence exists may you mark **INCOMPLETE** and document why full coverage wasn't added (e.g. route to `test-driven-development` for proper coverage later). |
| **Regression**     | Stop. Invoke `diagnose`.                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Verified Clean** | Non-trivial (see heuristic above) → invoke `request-code-review`. Trivial → done **only if** the Trivial -> done criterion above holds.                                                                                                                                                                                                                                                                                                    |

## 3. Manual Verification Template

If no automated pass/fail signal exists, propose a manual test plan via `AskUserQuestion` — the tool supplies a free-text "Other" automatically, so don't add one manually:

1. ✅ **Recommended** — [Test Plan] based on [feature scope and risk].
2. **Alternative** — [Lighter Test] + the justification for why less coverage is acceptable here.

**format:**

```markdown
### Manual Verification

**input:** [Specific values]
**expected:** [Observed side-effect]
**observed:** [Actual behavior]
**status:** PASS/FAIL
```

## 4. Rationalizations that are not verification

Each is a self-report claim, not execution evidence. None counts as the verification step — each is the signal to re-run §1, not to skip it.

- "It should work." / "It probably works." — confidence is not output.
- "I already verified." — an earlier run against different state is Stale Evidence, not current verification.
- "Tests pass, so it's done." — green tests ≠ acceptance criteria met; the suite may not exercise the changed lines.
- "It compiles / type-checks, so it runs." — a static pass is not a runtime pass.
- "I didn't touch that part, so it's unaffected." — grep call sites; see Scope Blindness.
- "The diff is small, so it's safe." — size is not behavior; a one-line change can break a caller.
- "I'll catch it in review." — verification deferred is verification denied; review does not re-run your code.

## 5. Pressure-test before declaring done

Answer each with a concrete artifact (command output, file:line, test name). Any prose-only answer is a fail — go back to §1.

- What command did you run, and what was its **exit code + counts**? Paste the tail.
- Which test exercises the **changed** lines (not the surrounding module)? Name it.
- What was the last failing assertion before the fix, and what is it after? (N-1 test, §6.)
- For each public interface changed: name every call site and the change made at each.
- What does `git diff --stat` show, and does every file/line in it map to the task?
- What did you re-run after the **last** edit? (The most recent run, not the first.)

## 6. Critical Failure Modes

**avoid:**

- **Confidence:** "It should work" is not evidence.
- **Green-Wash:** Mocks hiding actual logic or missing assertions.
- **Shadow Regressions:** Distant modules broken by global state changes — grep for shared/global state touched outside the diff's primary module.
- **Scope Blindness:** Verifying only the changed lines while ignoring callers/consumers of a changed interface — trace call sites before declaring done.
- **Stale Evidence:** Pasting output from a run predating the latest edit — re-run after every change, not just the first.

## 7. Expert Patterns

**action:** Use the N-1 test (Revert → Fail → Fix → Pass, see [`test-driven-development`](../test-driven-development/SKILL.md#n-1-test-false-green-elimination)) to eliminate false greens.
**action:** Test `null`, `undefined`, empty collections, and boundary cases to ensure robust coverage.

**next skills:**

- `request-code-review`: Once all verification items are satisfied, behavior is confirmed clean through execution evidence, and the change is non-trivial (§2).
- `diagnose`: If the checklist or evidence-gathering surfaces a regression, to root-cause it before re-attempting completion.
