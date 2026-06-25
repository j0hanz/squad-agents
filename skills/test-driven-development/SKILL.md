---
name: test-driven-development
description: 'Implements features using test-driven development (TDD). Use when the user requests "implement feature using TDD", "write unit tests", "red-green-refactor", or "test-first development". Action: writes test files first, verifies failure, then writes minimal implementation.'
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

**Trigger:** TDD, write tests, implement feature, build this.

**Rules:**

- Write a failing test _before_ writing any code.
- Do exactly ONE thing at a time. No skipping ahead.
- Example: Finish RED+GREEN+REFACTOR for one small piece completely before starting the next test.

## Step 0: Ask First

Ask the user how to start using `AskUserQuestion`:

1. **Recommended:** Start TDD for [feature].
2. **Alternative:** Try something else first (like exploring) and explain why.

## Step 1: Plan the Code Shape

Ask the user to confirm how the code will work using `AskUserQuestion`:

1. **Recommended:** Use this shape: `name(inputs) -> output`.
2. **Alternative:** Suggest a different shape and explain why.

- List errors that might happen.
- Show 2-3 examples of how to use it.
- Tell them where the test file goes.
- **Check:** Run all old tests first to make sure everything works before adding new ones.

## Step 2: RED (Failing Test)

_If using JavaScript/TypeScript, read `references/js-ts-patterns.md` fully._

1. Write the simplest test for one small thing.
2. Write blank code (like `return null`) just so it runs.
3. Run the test.
4. **Stop:** Make sure it FAILS. If it passes, delete it and write it differently.

### The Make-Sure Test

Before you trust a passing test:

1. Take out your code fix.
2. Run the test to make sure it fails again.
3. Put your code fix back in.
4. Run the test to make sure it passes.

## Step 3: GREEN (Make it Pass)

_If stuck on how simple to be, read `references/minimal-impl-examples.md` fully._

1. Save your work first.
2. Write the **smallest amount of code possible** to make the test pass.
3. Do not add extra code "just in case."
4. If you fail 3 times, start over with a smaller test.
5. If still stuck, use `diagnose` or `request-plan` tools.

## Step 4: REFACTOR (Clean Up)

- **Stop:** Only do this if tests are passing (GREEN).
- Clean up the code (rename things, remove repeated code).
- Do not fix code and clean up at the same time. They must be separate steps.
- Run tests again after cleaning.

## Strict Rules

- Only fake (mock) outside things like databases or APIs. Never fake your own code.
- Never write a second test until the first one is completely done.
- Always run tests between the RED and GREEN steps.
- Never change a test just to force it to pass. Fix your code instead. If the test is broken, go back to RED and explain why before changing it.

## Next Steps

When everything is done and clean, use `verification-before-completion` to double-check your work.
