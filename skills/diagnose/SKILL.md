---
name: diagnose
description: |
  Disciplined debugging methodology for any bug—software crashes, performance regressions, flaky tests, infrastructure failures, API errors, race conditions. Use when the user says "debug this", "fix this crash", "why is this slow", "diagnose", "my code is broken", "test is flaking", or describes unexpected behavior. Works for code (C/JavaScript/Python/etc), infrastructure (logs, services, deployments), and everything in between.
---

# Skill: diagnose

## Hard Gate

**Do NOT propose any fix until you have:**
1. Created a deterministic reproduction (Phases 1–2 complete)
2. Root cause confirmed by dynamic instrumentation AND documented in writing (Phases 3–4 complete)
3. A failing regression test ready (Phase 5 requirement)

Proposing a fix before these are done means you are patching symptoms. That is a debugging failure.

## Red Flags

| Thought | Reality |
|---------|---------|
| "I can see the issue" | You haven't traced it. Complete Phases 1–2 first. |
| "This quick fix will work" | No fix without a documented root cause. |
| "It's probably X" | "Probably" is not root cause. Falsify it. |
| "Let me try a few things" | Scatter-shot changes hide the real issue. One hypothesis at a time. |
| "The fix is obvious" | Document it anyway. You may be wrong. |
| "I'll write the regression test after" | Write it before the fix. That is Phase 5. |

## Overview

- **Purpose:** Systematic bug finding and fixing.
- **Principle:** A fast, deterministic feedback loop is a prerequisite to finding the root cause. Do not guess.
- **Applicability:** Code, infrastructure, flakiness, performance.

## Execution Rules

- **Rule 1:** Execute phases in strict sequence.
- **Rule 2:** NEVER skip Phase 1.
- **Rule 3:** NEVER modify the original source file directly. Create a working copy before making any changes.

## Phases

### Phase 1: Build Feedback Loop

**MANDATORY — READ ENTIRE FILE**: `references/feedback-loops.md` before writing the reproduction harness.

- **Goal:** Create a deterministic pass/fail signal.
- **Actions:** Write test, shell script, or minimal harness.
- **Metric_Speed:** Target < 2 seconds. (Performance-bug loops may exceed this — minimize setup overhead, not measurement runs.)
- **Metric_Signal:** Assert exact symptom.
- **Metric_Determinism:** Pin time, seed RNG, isolate filesystem.

### Phase 2: Reproduce

- **Goal:** Confirm bug matches user report.
- **Checklist_1:** Loop reproduces exact failure.
- **Checklist_2:** High reproduction rate achieved.
- **Checklist_3:** Captured precise symptom (error, timing, state).

### Phase 3: Hypothesize

- **Goal:** Generate 3-5 falsifiable hypotheses BEFORE testing.
- **Format:** "If [X] is the cause, then [Y] will change."
- **Ranking:** Bayesian prior: Recent changes > Code logic > Environment/config > External dependency.
- **Action:** Rank hypotheses and present to user.

### Phase 4: Instrument

**MANDATORY — READ ENTIRE FILE**: `references/phases.md` for instrumentation patterns and decision trees.

- **Constraint:** ABSOLUTE REQUIREMENT. You MUST instrument code dynamically. Do NOT rely solely on static inspection, even if the bug appears obvious.
- **Tagging_Rule:** MANDATORY. Prefix ALL temporary logs with a unique tag (e.g., `[DEBUG-a4f2]`).
- **Preference_1:** Debugger/REPL.
- **Preference_2:** Targeted logs at decision boundaries.
- **Anti_Pattern:** Never "log everything". Use targeted probes.
- **Performance Exception:** For performance bugs, do NOT use log statements as the measurement tool — instrumentation overhead distorts timing. Use `time.perf_counter`, `cProfile`, `EXPLAIN QUERY PLAN`, or `performance.now()` instead.

### Phase 5: Fix + Regression Test

- **Seam_Rule:** Write regression test at the correct depth BEFORE fixing (if possible). Invoke `test-driven-development` for this step — it defines the red-green-refactor loop to follow.
- **Seam Examples:**
  - Logic / data bug → unit test at the function boundary
  - Race condition → concurrent stress test (N threads × M iterations, assert final state)
  - Performance regression → timing assertion (`assert elapsed_ms < threshold`)
- **Actions:** Watch test fail -> Apply fix -> Watch test pass -> Re-run Phase 1 loop.

### Phase 6: Cleanup + Post-Mortem

- **Checklist_1:** All `[DEBUG-XXXX]` logs removed via grep.
- **Checklist_2:** Throwaway scripts deleted OR explicitly promoted to the test suite. No orphaned debug scripts left behind.
- **Checklist_3:** Original bug is verified gone.
- **Requirement:** MANDATORY FINAL STEP. Output Diagnosis Summary and Post-Mortem.

## Required Final Output Format

Always conclude with this exact structure:

```markdown
## Diagnosis Summary

- **Symptom:** [What the user saw]
- **Root Cause:** [Correct hypothesis]
- **Fix:** [What changed]
- **Feedback Loop Used:** [How reproduced]

## Post-Mortem

- **Prevention:** [What would have prevented this?]
- **Next Steps:** [Concrete and actionable — a skill to activate, a doc to update, or "None" if the fix is complete]
```
