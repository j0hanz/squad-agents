---
name: test-driven-development
description: |
  Use this skill when the user asks to implement a feature or bugfix using TDD, asks to write tests first, or requests to add behaviors incrementally. Triggers on "TDD", "red-green-refactor", "test-first", or when asked to write tests before implementation. MANDATORY for any non-trivial logic implementation where correctness is prioritized. Defines strict rules for how an LLM agent should navigate the TDD loop without hallucinating tests or getting stuck in broken environments. Also invoked as the implementation sub-skill of `spec-driven-development` — each plan task is executed using this skill's red-green-refactor loop.
disable-model-invocation: false
---

# Test-Driven Development (TDD)

Claude already knows standard TDD concepts (red-green-refactor, interface design, what makes a good test). This skill defines the **operational procedures** for executing TDD effectively as an autonomous agent, avoiding the common pitfalls of LLM-driven development.

## Hard Gate

**Do NOT write any implementation code until you have a failing test that asserts the specific behavior.**

No exceptions. Not for "obvious" code. Not for "trivial" utilities. Not for "one-liners."

If you cannot write a failing test first, that is a signal the interface is unclear — clarify it, then write the test.

## Red Flags

| Thought | Reality |
|---------|---------|
| "I'll add tests after I get it working" | Tests come first. Always. This is not negotiable. |
| "This is too simple to need a test" | Simple code still breaks. Write the test. |
| "Let me get the implementation working first" | HARD-GATE: no impl without a failing test. |
| "The test structure isn't clear yet" | That means the design isn't clear. Figure it out in the test. |
| "I'll write all tests first, then implement" | That's horizontal slicing — see Anti-Pattern section below. |
| "It passed on the first try" | Either you wrote a tautology or you tested existing behavior. Rewrite. |

## The Critical Anti-Pattern: Horizontal Slicing

Agents generate tokens efficiently by writing batches. This is fatal in TDD.

**NEVER write all tests first, then all code.**

```
WRONG:  [test1, test2, test3, test4]  →  [impl1, impl2, impl3, impl4]
RIGHT:   test1 → run → impl1 → run → test2 → run → impl2 → run
```

Tests written in bulk verify _imagined_ behavior. By the time you implement the second feature, the structure required by the third test is already wrong.

**MANDATORY RULE**: Write exactly ONE test. Stop. Run the test. Only after confirming it fails should you write implementation code.

## Agent-Specific TDD Execution Loop

### Phase 1: The First RED (Tracer Bullet)

1. Write the simplest possible test for the core behavior.
2. Run the test using the project's test runner.
3. **Analyze the Failure**:
   - If it passes immediately: You wrote a tautology or tested existing behavior. Delete and rewrite.
   - If it fails due to a syntax error, missing import, or environment issue: **STOP**. Fix the environment/test setup first. Do not touch implementation code until the test runner executes and fails on your assertion.
   - If it fails on the assertion (e.g. `AssertionError`): Proceed to GREEN.

### Phase 2: The GREEN (Implementation)

1. Write the _minimum_ code required to make the test pass.
2. **NEVER add speculative abstractions.** Agents love to build "robust" architectures prematurely. Stop yourself. If the test requires returning `0`, literally `return 0`.
3. Run the test.
4. **If stuck in RED for 3+ attempts**: Your approach is fundamentally flawed.
   - **Procedure**: Revert the implementation to the last GREEN state. Delete the failing test. Write a _smaller_, simpler test to make fractional progress.

### Phase 3: The REFACTOR (Cleanup)

1. Only enter this phase when all current tests are GREEN.
2. Consolidate logic, extract deep modules, and remove duplication.
3. **NEVER** write implementation and refactor in the same turn. Green code and refactoring must be separate tool calls so you can run the test suite between them to catch regressions.

## Absolute NEVERs for LLM Agents

- **NEVER mock internal collaborators.** Agents often use `unittest.mock` or `jest.mock` on internal imports to avoid building actual objects. This creates brittle tests that test the mock, not the system. **Mock at system boundaries only** (external APIs, DBs, Time, I/O).
- **NEVER bypass the public interface to set up test state.** (e.g., directly mutating a private class property or inserting raw database rows for a unit test). If an internal state is unreachable via the public interface, the public interface is incomplete or the test is invalid.
- **NEVER ignore the test runner output.** Read the actual traceback. If it says `ModuleNotFoundError`, do not rewrite the business logic.

## Pre-TDD: Document Public Interface

Before writing any tests, write down the public interface:

1. **Function/Method Signatures**
   ```
   function_name(param1, param2) → return_type
   ```

2. **Error Cases** (What happens when things go wrong?)
   ```
   - Invalid input: raise ValueError or return error?
   - Missing data: raise exception or return default?
   ```

3. **Usage Examples** (2-3 realistic scenarios)
   ```python
   # Happy path
   calculate_discount(100, 10)  # → 90
   
   # Edge case
   calculate_discount(100, 0)   # → 100
   
   # Error case
   calculate_discount(-50, 10)  # → raises ValueError
   ```

This prevents mid-stream API changes and gives tests a target to hit.

---

## Test Scope: One Scenario Per Test

Write one scenario per test function. Do NOT batch multiple scenarios:

**WRONG:**
```python
def test_discount():
    assert calculate_discount(100, 10) == 90      # Scenario 1
    assert calculate_discount(200, 50) == 100     # Scenario 2
    assert calculate_discount(50, 0) == 50        # Scenario 3 (all in one test)
```

**RIGHT:**
```python
def test_basic_discount():
    assert calculate_discount(100, 10) == 90      # ONE scenario

def test_large_discount():
    assert calculate_discount(200, 50) == 100     # ONE scenario

def test_no_discount():
    assert calculate_discount(50, 0) == 50        # ONE scenario
```

Why: Each test = one reason to run. One scenario per test = clear diagnosis when it fails.

---

## Workflow Execution

When asked to use TDD, follow this exact sequence via sequential tool calls:

1. Document public interface (names, signatures, errors, examples).
2. Use file editing tools to add **one** failing test (one scenario only).
3. Use shell command execution to run the test. Wait for it to fail.
4. **Analyze the failure** (see "Failure Analysis" section below).
5. Use file editing tools to implement the minimal fix.
6. Use shell command execution to run the test. Confirm it passes.
7. Repeat for the next behavior (go back to step 2).

---

## Analyze Test Failures

When a test fails, identify the failure type and respond appropriately:

### Environment Failures (Fix environment, re-run test)
- `ModuleNotFoundError: No module named 'my_module'` → Create the missing module
- `ImportError: cannot import 'MyClass'` → Create the missing class/function  
- `AttributeError: 'MyClass' object has no attribute 'validate'` → Add the missing method

**Action**: Write a minimal stub (empty function/class), re-run test.

### Logic Failures (Fix implementation, re-run test)
- `AssertionError: assert 80 == 90` → Your calculation is wrong
- `TypeError: unsupported operand type(s)` → Return type is wrong
- `ValueError: Invalid input` → Your validation logic is wrong

**Action**: Check the assertion message, fix implementation logic, re-run test.

### Unexpected Failures (Debug, then proceed)
- Any exception not listed above → Inspect traceback carefully
- May indicate flawed test or flawed setup
- Don't proceed until you understand the root cause

**Action**: Diagnose, then either fix the test or the code.

---

## Minimal Implementation: Domain-Specific Guidance

The principle: implement exactly what the test requires, nothing more.

**When you need patterns for a specific domain** (math functions, validators, parsers, classes):
**MANDATORY — READ ENTIRE FILE**: `references/minimal-impl-examples.md`

---

## REFACTOR Phase Guidance

Only refactor when ALL current tests are GREEN. Use the refactor skill for detailed execution, but here's the TDD-specific checklist:

**Before refactoring:**
- [ ] All tests passing (confirmed by test run)
- [ ] Feature is complete (no pending tests)
- [ ] Refactoring won't change behavior

**What to refactor:**
- [ ] Duplicated code (DRY) - only if 2+ real occurrences
- [ ] Unclear variable/function names - rename to self-document
- [ ] Long functions (>10 lines) - extract helper with clear purpose
- [ ] Magic numbers/strings - replace with named constants
- [ ] Deep nesting - flatten with guard clauses

**What NOT to refactor:**
- Don't add new behavior or fix bugs - do in separate step
- Don't apply complex patterns without test coverage
- Don't rename just for consistency - only if name misleads

**After each refactor change:**
- Run all tests (must still pass)
- Confirm no new failures introduced

**For detailed refactoring strategy:** Consult the separate `refactor` skill if you need to apply complex structural patterns (Strategy, Observer, extract classes, etc.). This TDD skill covers WHEN to refactor in the cycle; the refactor skill covers HOW.

---

## Troubleshooting: Stuck in RED for 3+ Attempts

If you fail the same test 3+ times, your approach is fundamentally flawed:

**Procedure:**
1. Revert implementation to the last GREEN state
2. Delete the current failing test
3. Write a SMALLER, SIMPLER test that makes fractional progress

**Example:**
```python
# You're stuck on this (failing 3+ times):
def test_csv_parser():
    # Trying to handle single-line + multi-line + quotes all at once
    assert parse("a,b,c") == [["a", "b", "c"]]
    assert parse("a,b\nc,d") == [["a", "b"], ["c", "d"]]
    assert parse('"a,b",c') == [["a,b", "c"]]

# Solution: Revert implementation, delete test, write simpler:
def test_parse_single_line():
    # Just handle one feature
    assert parse("a,b,c") == [["a", "b", "c"]]
```

Each test is one building block. If the block doesn't fit, it's too big.

---

## Concrete Example

For a complete RED-GREEN-REFACTOR walkthrough (4 tests, failure analysis, expected test runner
output at each step):
**MANDATORY — READ ENTIRE FILE**: `references/full-cycle-example.md`
