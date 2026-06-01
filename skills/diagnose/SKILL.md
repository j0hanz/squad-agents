---
name: diagnose
description: "Disciplined debugging for any bug or unexpected behavior. Trigger on 'debug', 'fix crash', 'not working', 'why is this failing', 'unexpected output', 'production error', 'diagnose'. Mandatory root-cause workflow before any fix."
disable-model-invocation: false
argument-hint: "[symptom or file path]"
---

# Skill: diagnose

## Red Flags

The value of this methodology is that it forces you to know — not guess — before you act. Every shortcut below hides the real issue.

| Thought | Reality |
|---------|---------|
| "I can see the issue" | You haven't traced it. Complete Phases 1–2 first. |
| "This quick fix will work" | No fix without a documented root cause. |
| "It's probably X" | "Probably" is not root cause. Falsify it. |
| "Let me try a few things" | Scatter-shot changes hide the real issue. One hypothesis at a time. |
| "The fix is obvious" | Document it anyway. You may be wrong. |
| "I'll write the regression test after" | Write it before the fix. That is Phase 5. |

**Purpose:** Systematic bug finding and fixing. A fast, deterministic feedback loop is a prerequisite to finding the root cause — do not guess. Applies to code, infrastructure, flakiness, and performance.

## NEVER

- **NEVER apply multiple changes simultaneously** — you cannot isolate which change fixed (or masked) the issue; one hypothesis, one change, one test run
- **NEVER delete or overwrite the reproduction harness** before the fix is confirmed and the regression test passes — if the first fix is wrong you need to reproduce from the same baseline
- **NEVER accept "works on my machine"** as a root cause — the environmental difference between machines IS the bug; investigate the delta (env vars, OS, runtime version, seed)

## Execution Rules

- **Rule 1:** Execute phases in strict sequence.
- **Rule 2:** NEVER skip Phase 1.
- **Rule 3:** NEVER modify the original source file directly. Create a working copy (e.g., `orders_fixed.py`) before making any changes.

## Phases

### Phase 1: Build Feedback Loop

**MANDATORY — READ ENTIRE FILE**: `references/feedback-loops.md` before writing the reproduction harness.

- **Goal:** Create a deterministic pass/fail signal.
- **Actions:** Write test, shell script, or minimal harness.
- **Metric_Speed:** Target < 2 seconds. (Performance-bug loops may exceed this — minimize setup overhead, not measurement runs.)
- **Metric_Signal:** Assert exact symptom.
- **Metric_Determinism:** Pin time, seed RNG, isolate filesystem.

**If you cannot run code** (no environment access, only logs or a description provided): Stop here. Ask the user for one of: (1) environment or shell access, (2) captured artifacts (logs, core dumps, traces), or (3) permission to add production telemetry. Do not proceed to Phase 2 without a runnable feedback loop.

### Phase 2: Reproduce

- **Goal:** Confirm bug matches user report.
- **Checklist_1:** Loop reproduces exact failure.
- **Checklist_2:** High reproduction rate achieved. If rate is below 50%, go back to Phase 1 — add stress, concurrency, or timing control until the bug reproduces reliably before continuing.
- **Checklist_3:** Captured precise symptom (error, timing, state).

**Gate:** Before moving to Phase 3, confirm your loop reproduces the exact failure the user described. If it does not, return to Phase 1.

### Phase 3: Hypothesize

- **Goal:** Generate 3-5 falsifiable hypotheses BEFORE testing.
- **Format:** "If [X] is the cause, then [Y] will change when I do [Z]."
- **Ranking:** Bayesian prior: Recent changes > Code logic > Environment/config > External dependency.
- **Action:** Rank hypotheses and present to user before testing any of them.

**Example hypotheses for a KeyError crash:**
- H1: The key is genuinely absent in some inputs (most likely — recent data model change). *Falsify:* add a log before the access; check whether the key appears in the failing case.
- H2: The key is present but under a different name due to a serialization mismatch. *Falsify:* log `dict.keys()` at the crash site.
- H3: A race condition clears the dict between check and access. *Falsify:* run a single-threaded replay; if it reproduces, concurrency is not the cause.

### Phase 4: Instrument

**MANDATORY — READ ENTIRE FILE**: `references/phases.md` for instrumentation patterns and decision trees.

- **Constraint:** ABSOLUTE REQUIREMENT. You MUST instrument code dynamically. Do NOT rely solely on static inspection, even if the bug appears obvious.
- **Tagging_Rule:** MANDATORY. Prefix ALL temporary logs with a unique tag (e.g., `[DEBUG-a4f2]`). The tag makes cleanup a single `grep -r "[DEBUG-a4f2]"` — no manual hunting.
- **Preference_1:** Debugger/REPL.
- **Preference_2:** Targeted logs at decision boundaries.
- **Anti_Pattern:** Never "log everything". Use targeted probes.
- **Performance Exception:** For performance bugs, do NOT use log statements as the measurement tool — instrumentation overhead distorts timing. Use `time.perf_counter`, `cProfile`, `EXPLAIN QUERY PLAN`, or `performance.now()` instead.

### Phase 5: Fix + Regression Test

Write the regression test at the correct seam **before** applying the fix. This is the RED→GREEN cycle:

1. **Write the test** targeting the exact failure. Choose the right depth:
   - Logic / data bug → unit test at the function boundary
   - Race condition → concurrent stress test (N threads × M iterations, assert final state)
   - Performance regression → timing assertion (`assert elapsed_ms < threshold`)
2. **Run it — confirm it FAILS (RED).** If it passes immediately, the test is wrong — it is not targeting the actual bug.
3. **Apply the fix** to your working copy.
4. **Run it again — confirm it PASSES (GREEN).**
5. **Re-run Phase 1 loop** — confirm the original symptom is gone end-to-end.

### Phase 6: Cleanup + Post-Mortem

Work through this checklist completely before closing:

- [ ] All `[DEBUG-XXXX]` tags removed — run `grep -r "[DEBUG-" .` to confirm zero matches.
- [ ] Throwaway reproduction scripts deleted OR explicitly promoted into the test suite. No orphaned debug scripts left behind.
- [ ] Working copy is the canonical fixed file. Original untouched source preserved if needed for diff.
- [ ] Original bug is verified gone via Phase 1 loop.
- [ ] Output the Diagnosis Summary and Post-Mortem below.

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
