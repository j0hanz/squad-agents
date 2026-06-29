---
name: verification-before-completion
description: 'Use before claiming any work is complete — runs tests, checks for regressions, and gathers execution evidence. Always before request-code-review; never substitute code-reading for actual execution.'
disable-model-invocation: false
allowed-tools: AskUserQuestion
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

- [ ] **Tests:** Targeted tests and regression suite pass. Paste actual runner output (exit code + pass/fail counts) — a claim without pasted output is not evidence.
- [ ] **Manual:** Documented inputs/outputs if no automation.
- [ ] **Bug Fix:** Confirm reproduction failure then confirm success.
- [ ] **Clean:** `grep` sweep for debug logs/tags (`debugger`, `pdb`, `TODO`).
- [ ] **Lint:** No new unused imports or variables.
- [ ] **Diff:** Audit every change for intent.

## 2. Decision Logic

**"Non-trivial" heuristic:** a change is non-trivial unless it is a single-file edit of 20 lines or fewer with no new public surface and no logic branching. This is a bias-toward-caution heuristic, not a precise boundary — when in doubt, treat the change as non-trivial. Self-classifying a change as trivial to skip the review handoff below is itself a verification failure.

| Status             | Action                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| :----------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CI-Only**        | Stop. Report: "Blocked by CI. Wait for pipeline."                                                                                                                                                                                                                                                                                                                                                                                          |
| **No Test Suite**  | **Gate, not a pass:** before marking INCOMPLETE, you MUST write at least one executable smoke/characterization test or manual reproduction script proving the change works (see §3 Manual Verification Template) — a prose rationale alone is not sufficient. Only after that evidence exists may you mark **INCOMPLETE** and document why full coverage wasn't added (e.g. route to `test-driven-development` for proper coverage later). |
| **Regression**     | Stop. Invoke `diagnose`.                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Verified Clean** | Non-trivial (see heuristic above) → invoke `request-code-review`. Trivial → done.                                                                                                                                                                                                                                                                                                                                                          |

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

## 4. Critical Failure Modes

**avoid:**

- **Confidence:** "It should work" is not evidence.
- **Green-Wash:** Mocks hiding actual logic or missing assertions.
- **Shadow Regressions:** Distant modules broken by global state changes — grep for shared/global state touched outside the diff's primary module.
- **Scope Blindness:** Verifying only the changed lines while ignoring callers/consumers of a changed interface — trace call sites before declaring done.
- **Stale Evidence:** Pasting output from a run predating the latest edit — re-run after every change, not just the first.

## 5. Expert Patterns

**action:** Use the N-1 test (Revert → Fail → Fix → Pass, see [`test-driven-development`](../test-driven-development/SKILL.md#n-1-test-false-green-elimination)) to eliminate false greens.
**action:** Test `null`, `undefined`, empty collections, and boundary cases to ensure robust coverage.

**next skills:**

- `request-code-review`: Once all verification items are satisfied, behavior is confirmed clean through execution evidence, and the change is non-trivial (§2).
- `diagnose`: If the checklist or evidence-gathering surfaces a regression, to root-cause it before re-attempting completion.
