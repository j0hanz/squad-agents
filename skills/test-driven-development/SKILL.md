---
name: test-driven-development
description: 'Use when implementing a feature or fixing a bug. The default implementation path — writes a failing test first, then the minimal code to pass it.'
disable-model-invocation: false
---

# test-driven-development

Autonomous TDD execution. **HARD GATE:** No implementation code WITHOUT a failing test.

## When NOT to use TDD

These are escape hatches from the HARD GATE — never self-invoke one silently. Confirm the carve-out via `AskUserQuestion` before skipping RED (the tool supplies a free-text "Other" automatically). Pick from the three categories below (see their definitions immediately following):

1. ✅ **Recommended** — Skip TDD: [the matching category from the list below] because [specific reason this case matches].
2. **Alternative** — Use full TDD anyway + the reason the carve-out doesn't actually apply.

- **Exploratory Spikes:** When the implementation path is unknown and you need to "find the shape" of the code first (throwaway code). **Mandatory:** once the shape is found, the spike code MUST be discarded (`git stash drop`/delete, not committed) and re-implemented through the normal RED-GREEN-REFACTOR loop. A spike is a sketch, never the shipped diff.
- **Trivial One-Liners:** Pure data mappings or standard boilerplate with zero logic.
- **Pure UI/CSS:** Visual styling that requires manual "eye-balling" rather than logical assertions.

## Process Flow

```
Start: TDD Request -> Carve-out applies (spike/trivial/CSS)? -- yes --> AskUserQuestion confirms skip -> exit (handle outside this skill)
                                                              -- no  --> 0. Confirm with user -> Pre-TDD: Interface (signatures, errors, examples) -> TDD Cycle:

  1. RED (write failing test + minimal stub) -> run test, confirm failure
       -- failure confirmed --> 2. GREEN (write minimal implementation) -> run test
                                   -- fail --> Stuck? (3+ attempts)
                                                  -- yes --> diagnose/request-plan (handoff)
                                                  -- no  --> retry GREEN
                                   -- pass --> 3. REFACTOR (surgical cleanup) -> run test, stay passing
                                                  -> All scenarios covered?
                                                       -- no  --> back to TDD Cycle
                                                       -- yes --> verification-before-completion (handoff)
```

**trigger:** TDD, write tests, implement feature, build this.
**constraint:** one failing test before any implementation code.
**constraint:** exactly one scenario in flight at a time — no skipping ahead to the next test before the current RED-GREEN-REFACTOR cycle closes.

## Step 0: Confirm Scope

**action:** `AskUserQuestion`.

1. **Recommended:** Start TDD for [feature].
2. **Alternative:** Explore first, then start TDD — state the reason exploration is needed before code.

## Step 1: Define the Interface

**action:** `AskUserQuestion` to lock the shape before writing a test against it.

1. **Recommended:** `name(inputs) -> output`.
2. **Alternative:** Propose a different shape and justify it.

- Enumerate expected error conditions.
- Provide 2-3 call-site examples.
- State the target test file path.
- **Gate:** run the existing suite first — establish a clean baseline before adding new tests.

## Step 2: RED (Failing Test)

_If JavaScript/TypeScript, read `references/js-ts-patterns.md` fully._

1. Write the smallest test for one behavior.
2. Stub the implementation (e.g. `return null`) — just enough to compile/run.
3. Run the test.
4. **Gate:** confirm FAILURE. A test that passes immediately is testing nothing — delete and rewrite it.

### N-1 Test (False-Green Elimination)

Before trusting a passing test:

1. Revert the implementation.
2. Run the test — confirm it fails (RED).
3. Restore the implementation.
4. Run the test — confirm it passes (GREEN).

## Step 3: GREEN (Make It Pass)

_If unsure how minimal is minimal, read `references/minimal-impl-examples.md` fully._

1. Checkpoint the working tree before editing.
2. Write the smallest implementation that satisfies the test — no speculative generality.
3. No code added "just in case" — only what the current test requires.
4. 3 failed attempts on the same test → restart with a smaller test.
5. Still stuck → escalate to `diagnose` or `request-plan`.

## Step 4: REFACTOR (Clean Up)

- **Gate:** only proceed while GREEN.
- Improve structure (naming, deduplication) without changing behavior.
- Never interleave a behavior fix with a refactor — they are separate passes.
- Re-run tests after every refactor; must stay GREEN.

## Strict Rules

- Mock only true externals (databases, APIs, network) — never mock the code under test.
- No second test until the first has completed its full RED-GREEN-REFACTOR cycle.
- Always run the test between RED and GREEN to confirm the failure before implementing.
- Never edit a test to force a pass. Fix the implementation. If the test itself is wrong, return to RED, state why, then rewrite it.

## Next Steps

On full coverage and a clean REFACTOR, hand off to `verification-before-completion`.
