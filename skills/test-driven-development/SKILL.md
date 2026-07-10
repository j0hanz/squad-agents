---
name: test-driven-development
description: 'Use when new logic requires implementation (RED-first) or when a TDD red flag (trivially passing test, code written before its test, or lack of observed RED) occurs.'
disable-model-invocation: false
allowed-tools: AskUserQuestion, Bash, Read, Grep, Glob, Write, Edit, NotebookEdit
---

# test-driven-development

Autonomous TDD execution. **HARD GATE:** No implementation code WITHOUT a failing test — observe RED before every GREEN; a GREEN you never saw fail tests nothing.

## When NOT to use TDD

Escape hatches from the HARD GATE. Never self-invoke one silently — confirm via `AskUserQuestion` first (the tool supplies a free-text "Other"). Pick from the three categories below:

1. ✅ **Recommended** — Skip TDD: [matching category] because [specific reason].
2. **Alternative** — Use full TDD anyway + reason the escape hatch doesn't apply.

- **Exploratory Spikes:** Implementation path unknown; throwaway code to "find the shape." **Mandatory:** once found, the spike MUST be discarded (`git stash drop`/delete, not committed) and re-implemented through RED-GREEN-REFACTOR. A spike is a sketch, never the shipped diff.
- **Trivial One-Liners:** Pure data mappings or standard boilerplate with zero logic.
- **Pure UI/CSS:** Visual styling needing manual "eye-balling," not logical assertions.

## Process Flow

- **Start: TDD Request**
  - _Escape hatch applies (spike/trivial/CSS)_: AskUserQuestion confirms skip -> exit (handle outside this skill)
  - _No escape hatch_: 0. Confirm with user -> Pre-TDD: Interface (signatures, errors, examples) -> TDD Cycle
- **TDD Cycle**:
  - **1. RED (write failing test + minimal stub)** -> run test, confirm failure
    - _failure confirmed_: 2. GREEN (write minimal implementation) -> run test
  - **2. GREEN (write minimal implementation)**
    - _fail_: Stuck? (3+ attempts)
      - _yes_: diagnose/request-plan (handoff)
      - _no_: retry GREEN
    - _pass_: 3. REFACTOR
  - **3. REFACTOR (surgical cleanup)** -> run test, stay passing
    - _All behaviors covered?_
      - _no_: back to TDD Cycle
      - _yes_: verification-before-completion (handoff)

## Step 0: Confirm Scope

**action:** `AskUserQuestion`.

1. **Recommended:** Start TDD for [feature].
2. **Alternative:** Explore first, then start TDD — state why exploration is needed before code.

**Done when:** user response is captured via AskUserQuestion.

## Pre-TDD: Define the Interface

**action:** `AskUserQuestion` to lock the shape before writing a test against it.

1. **Recommended:** `name(inputs) -> output`.
2. **Alternative:** Propose a different shape and justify it.

- Enumerate expected error conditions.
- Provide 2-3 call-site examples.
- State the target test file path.
- Start the **behavior list**: happy path + the enumerated errors; it grows by one edge case per RED cycle and is the coverage gauge for REFACTOR.
- **Gate:** run the relevant existing tests first — establish a clean baseline before adding new tests.

**Done when:** interface details, errors, and test path are locked and user confirms.

## Step 1: RED (Failing Test)

_If JavaScript/TypeScript, read `references/js-ts-patterns.md` fully._

1. Write the smallest test for one behavior.
2. Stub the implementation (e.g. `return null`) — just enough to compile/run.
3. Run the test.
4. **Gate:** confirm FAILURE. A test that passes immediately tests nothing — delete and rewrite it.

## Step 2: GREEN (Make It Pass)

_If unsure how minimal is minimal, read `references/minimal-impl-examples.md` fully._

1. Checkpoint the working tree before editing.
2. Write the smallest implementation that satisfies the test — no speculative generality.
3. No code added "just in case" — only what the current test requires.
4. 3 failed attempts on the same test → restart with a smaller test.
5. Still stuck → escalate to `diagnose` or `request-plan`.

### N-1 Test (False-Green Elimination)

Before trusting a passing test:

1. Revert the implementation.
2. Run the test — confirm RED.
3. Restore the implementation.
4. Run the test — confirm GREEN.

## Step 3: REFACTOR (Clean Up)

- **Gate:** only proceed while GREEN.
- Improve structure (naming, deduplication) without changing behavior.
- Never interleave a behavior fix with a refactor — separate passes.
- Re-run tests after every refactor; must stay GREEN.
- **Done when:** no further structural improvement available AND the relevant tests GREEN; then evaluate coverage against the behavior list (gaps → back to RED; else hand off).

## Strict Rules

- Mock only true externals (databases, APIs, network) — never mock the code under test.
- No second test until the first has completed its full RED-GREEN-REFACTOR cycle.
- If the test itself is wrong (not the implementation), return to RED, state why, then rewrite it — don't edit a test to force a pass (see Red Flags).

## Red Flags — Stop Rationalizing, Delete and Restart

Any of these signals means you have left TDD. The fix is the same every time: delete the implementation (or the code-first diff), return to RED, and re-drive the cycle. Do not argue the case; do not "adapt" what you wrote.

- Implementation written before, or without, a failing test for the behavior it adds (a HARD GATE violation).
- The test trivially passes without exercising the logic under test (e.g. asserts a constant the stub already returns, mocks the unit itself, or never calls the code path).
- Tests retrofitted to match already-written code ("tests-after"), or a test edited to force a pass.
- Self-talk: "too simple to test", "I already manually tested it", "tests after achieve the same purpose", "it's the spirit that matters, not the ritual", "this is different because...".
- Skipping the N-1 check because "it obviously would fail" — a test you have not seen fail is testing nothing.
- A GREEN that arrives on the first run with no RED observed for that specific behavior.
- Keeping code-first output "as reference" or "to adapt" instead of deleting it.

**All of these mean:** delete the code-first implementation, re-enter the cycle at RED, and run the test to confirm it fails before re-implementing.

<!-- Defer the deeper apparatus (rationalization table, spirit-vs-letter clause, commitment framing, pressure-test evidence). Add it only when a real session demonstrates a rationalization this list doesn't already kill. The full kit lives in the writing-skills anti-rationalization reference — see it before re-adding anything: ~/.claude/skills/writing-skills/references/anti-rationalization/README.md -->

## Next Steps

On full behavior-list coverage and a clean REFACTOR, hand off to `verification-before-completion`.
