---
name: diagnose
description: "Performs disciplined root-cause analysis for software bugs and crashes using a systematic hypothesis-falsification workflow. Accepts a symptom description or error trace, and produces a structured diagnosis report detailing the symptom, root cause, fix, and reproduction feedback loop. Trigger on: 'debug', 'fix crash', 'why is this failing', 'unexpected output', 'diagnose bug', 'root cause analysis', 'feedback loop', 'instrumentation'. Also triggers when troubleshooting test failures or diagnosing unexpected runtime exceptions. Always prefer this skill over test-driven-development when diagnosing a bug prior to implementing a fix."
disable-model-invocation: false
argument-hint: '[symptom description or error trace]'
---

# diagnose

Identify true root cause through systematic falsification. **DO NOT GUESS.**

## Process Flow

```
Phase 1: Build Feedback Loop (pass/fail signal)
  -> Phase 2: Reproduce (confirm bug)
  -> Phase 3: Hypothesize & Falsify (3-5 hypotheses)
       -- falsified --> retry Phase 3 with new hypotheses
  -> Phase 4: Instrumentation (targeted probes)
  -> Phase 5: Red-Green Fix (regression test)
  -> Phase 6: Finalization (de-instrument / verify)
```

**trigger:** debug, fix crash, unexpected behavior
**constraint:** apply 1 hypothesis per run
**constraint:** modify working copy only
**constraint:** reject "works on my machine"

## Phase 1: Feedback Loop

**action:** create <2s deterministic pass/fail signal
**action:** isolate filesystem, pin seeds/time
**mandatory:** read `references/feedback-loops.md` (do NOT load `references/phases.md`)
**gate:** require loop or request telemetry/logs

## Phase 2: Reproduce

**action:** achieve >50% reproduction rate
**gate:** require logged repro signal before Phase 3

## Phase 3: Hypothesize & Falsify

**mandatory:** read `references/phases.md` (do NOT load `references/feedback-loops.md`)
**action:** propose 3-5 falsifiable hypotheses via `AskUserQuestion` (surface top 3, queue rest)
**format:** "If [X] is the cause, then [Y] will change when I do [Z]."
**dispatch:** use `multi-agent-dispatch` for independent hypotheses (require `isolation: worktree`)
**gate:** require confirmed probe result (no guessing by elimination)

## Phase 4: Instrumentation

**action:** instrument decision boundaries dynamically
**format:** prefix logs with `[DEBUG-XXXX]`
**constraint:** target logs strictly; use profilers for performance

## Phase 5: Red-Green Fix

**action:** write regression test targeting failing seam
**action:** confirm RED
**action:** apply minimal fix on working copy
**action:** confirm GREEN
**action:** execute N-1 test (revert fix -> confirm RED -> restore fix)

## Phase 6: Finalization

**action:** remove all `[DEBUG-XXXX]` tags
**action:** verify fix via Phase 1 loop
**action:** promote scripts to test suite or delete

## Next Skills

**test-driven-development:** implement new logic/tests
**architecting:** clean up multiple files/modules
**request-plan:** address major specification gaps
**context-optimizer:** if context bloats mid-skill (long reads, many tool calls)

## Transitions

**verification-before-completion:** re-verify in same skill
**test-driven-development:** resume current task/phase
**multi-agent-development:** resume current task/phase
**multi-agent-dispatch:** resume INTEGRATE step
**receive-code-review:** resume Step 4 Implement
**codebase-init:** resume Failure Recovery step
**pr-workflow:** resume failed commit/push/PR step
**gh-actions:** resume failed CI/workflow/script step

## Exclusions

**test-driven-development:** use for writing new feature tests

## References

**references/feedback-loops.md:** setup patterns by system type
**references/phases.md:** detailed phases, hypothesis prioritization, profiling

## Output Format

**symptom:** [Description]
**root_cause:** [Correct Hypothesis]
**fix:** [Changes]
**feedback_loop:** [Reproduction Script]
**prevention:** [Architecture/Test improvement]
**next_steps:** [Follow-up tasks]
