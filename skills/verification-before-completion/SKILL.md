---
name: verification-before-completion
description: 'Use when code changes require verification via execution evidence (test runs or manual reproduction with pasted output). Prefer over request-code-review if implementation is unverified.'
disable-model-invocation: false
allowed-tools: AskUserQuestion, Bash, Read, Grep
---

# verification-before-completion

Guarantee operational correctness through execution evidence. **NEVER** confirm based on reading code alone.

## Process Flow

```
Start: Ready to Complete
  -> §1 Mandatory Checklist (tests run or manual repro performed, fresh output pasted)
  -> §2 Decision Logic (route by status — table)
```

## 1. Mandatory Checklist

The full bar lives in [definition-of-done.md](references/definition-of-done.md) (Tests, Build/types, Lint, No debug residue, Diff, Acceptance criteria, Callers) — read it first. The items below are the delta this skill adds on top of that bar:

- [ ] **Manual:** Documented inputs/outputs if no automation (see §3).
- [ ] **Bug Fix:** Confirm reproduction failure then confirm success.

**Done when:** all checklist items are verified and manual test evidence is documented (if required).

## 2. Decision Logic

**"Non-trivial" heuristic:** a change is non-trivial unless it is a single-file, single-line edit with no executable surface and no new public surface (the Trivial→done criteria below). Bias toward caution — when in doubt, treat as non-trivial. Self-classifying a change as trivial to skip the review handoff below is itself a verification failure.

**Trivial -> done when** (all must hold, each observable — prose alone fails):

- (a) `git diff --stat` shows exactly **1 file** and **1 line** changed (1 ins + 1 del); AND
- (b) the change is a comment/doc/typo with **no executable surface** (no statement, branch, or signature touched); AND
- (c) the relevant suite — or, if no test touches the file, build + lint — is green, with pasted output from a run **after the last edit**.

Any deviation from (a)/(b)/(c) → non-trivial → route to `request-code-review`. "It's just a typo" without (c) is not done.

| Status             | Action                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| :----------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CI-Only**        | Stop. Report: "Blocked by CI. Wait for pipeline."                                                                                                                                                                                                                                                                                                                                                                                          |
| **No Test Suite**  | **Gate, not a pass:** before marking INCOMPLETE, you MUST write at least one executable smoke/characterization test or manual reproduction script proving the change works (see §3 Manual Verification Template) — a prose rationale alone is not sufficient. Only after that evidence exists may you mark **INCOMPLETE** and document why full coverage wasn't added (e.g. route to `test-driven-development` for proper coverage later). |
| **Regression**     | Stop. Route to `diagnose`.                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **Verified Clean** | Non-trivial (see heuristic above) → route to `request-code-review`. Trivial → done **only if** the Trivial -> done criterion above holds.                                                                                                                                                                                                                                                                                                  |

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

## 4. Failure Modes

Each mode below is a self-report claim that is **not** execution evidence. The required evidence is what you must paste or point to instead. Any prose-only answer is a fail — re-run §1.

| Mode                   | The rationalization (signal)                                          | Required evidence (artifact)                                                                                                   |
| :--------------------- | :-------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| **Confidence**         | "It should work" / "it probably works" / "it compiles, so it runs"    | Fresh command output: exit code + counts, from a run **after the last edit**.                                                  |
| **Green-Wash**         | "Tests pass, so it's done" — mocks hiding logic or missing assertions | The test that exercises the **changed** lines (named); N-1 proof the suite fails without the fix (§5).                         |
| **Scope Blindness**    | "I didn't touch that part, so it's unaffected"                        | Every call site of each changed public interface, named (`file:line`).                                                         |
| **Shadow Regressions** | "The diff is small, so it's safe"                                     | `git diff --stat` with every file/line mapped to the task; grep shared/global state touched outside the diff's primary module. |
| **Stale Evidence**     | "I already verified" — an earlier run against different state         | Output from the **most recent** run, not the first; re-run after every change.                                                 |

Review does not re-run your code — "I'll catch it in review" is verification deferred, not done.

## 5. Expert Patterns

**action:** Use the N-1 test (Revert → Fail → Fix → Pass, see [test-driven-development](../test-driven-development/SKILL.md#n-1-test-false-green-elimination)) to eliminate false greens.
**action:** Test `null`, `undefined`, empty collections, and boundary cases to ensure robust coverage.
