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
Phase 0: Triage (serial vs. tournament)
  -> Phase 1: Build Feedback Loop (lock the Oracle)
  -> Phase 2: Reproduce (confirm bug; tournament-only: race repro strategies)
  -> Phase 3: Hypothesize & Falsify (3-5 propositions)
       -- serial --> probe one hypothesis directly; falsified -> next hypothesis
       -- tournament --> fan blind Falsifiers, 1 proposition/worktree
  -> Phase 3.5: Converge & Arbitrate (replay survivors; decide by mechanism)
       -- REVISE (entangled survivors) --> re-bracket, retry 3.5
       -- REJECT (0 survive, <2 rounds) --> retry Phase 3 with new hypotheses
       -- REJECT (0 survive, 2 rounds spent) --> fall back serial, escalate to user
  -> Phase 4: Instrumentation (targeted probes)
  -> Phase 5: Red-Green Fix (regression test on root-cause seam; tournament-only: race fixes)
  -> Phase 6: Finalization (de-instrument / verify / re-check for masked causes)
```

**trigger:** debug, fix crash, unexpected behavior
**constraint:** 1 falsifiable proposition per run (tournament mode: 1 per worktree)
**constraint:** modify working copy only
**constraint:** reject "works on my machine"

## Phase 0: Triage

**action:** default to serial — probe one hypothesis at a time, directly
**action:** escalate to the tournament (Phase 3 tournament path) only when 3+ genuinely independent candidate causes exist, or the bug is flaky/stress-class
**gate:** never tournament a single obvious cause (e.g. one-line null check) — serial is faster and correct for the common case

## Phase 1: Feedback Loop

**action:** create <2s deterministic pass/fail signal — this loop is the **Oracle** that Phase 3.5 arbitrates against
**action:** isolate filesystem, pin seeds/time
**action:** if no deterministic loop is achievable (slow/flaky/timing-sensitive), raise repro rate via stress (`references/feedback-loops.md`) rather than blocking — degrade to serial interactive debugging, never block the skill
**mandatory:** read `references/feedback-loops.md` (do NOT load `references/phases.md`)
**gate:** require loop or request telemetry/logs

## Phase 2: Reproduce

**action:** achieve >50% reproduction rate
**action (tournament only):** race 2-3 candidate repro strategies via `multi-agent-dispatch`; keep the fastest deterministic >50% strategy and lock it as the Oracle
**gate:** require logged repro signal before Phase 3

## Phase 3: Hypothesize & Falsify

**mandatory:** read `references/phases.md` (do NOT load `references/feedback-loops.md`)
**action:** propose 3-5 falsifiable hypotheses via `AskUserQuestion` (surface top 3, queue rest)
**format:** "If [X] is the cause, then [Y] will change when I do [Z]." (conjunctions allowed: "If [X] AND [Y]...", for interaction bugs)
**serial path (default):** probe one hypothesis directly against the Oracle
**tournament path (Phase 0 escalated):** dispatch via `multi-agent-dispatch`, one falsifiable proposition per worktree, lanes blind to siblings

- **role:** observational/static probe -> read-only `detective` (fallback `general-purpose`); instrumented/executed probe -> worktree-isolated `general-purpose` Investigator (Bash+Write), `isolation: worktree`
- **contract:** 5-field cold-start (SCOPE/OBJECTIVE/CONTEXT/CONSTRAINTS/OUTPUT) per `../multi-agent-development/references/subagent-contract.md`
- **concurrency:** background-exempt only with a notify primitive; else batch lanes in <=3
- **output:** `VERDICT: SURVIVED | KILLED` + EVIDENCE (the probe as a runnable block, asserting the predicted mechanism effect Y — not just the Oracle bit)
- **narration:** report each lane's verdict to the user as it completes — no silent background batch
  **gate:** require confirmed probe result (no guessing by elimination)

## Phase 3.5: Converge & Arbitrate

**action:** replay every `SURVIVED` lane's probe on the main checkout against the Oracle — never trust a lane's self-reported `VERDICT`
**action:** converge by mechanism, not count — collapse aliases (same cause, different abstraction) into one cause; report multiple causes if genuinely distinct; flag indistinguishable survivors as entangled
**rule:** never-self-arbitrate — the agent that proposed a hypothesis never declares it the root cause
**routing:** `APPROVED` (resolved) -> Phase 4 | `REVISE` (entangled survivors) -> re-bracket with disjoint probes, retry 3.5 | `REJECT` (0 survive) -> retry Phase 3 with new hypotheses
**gate:** max 2 rounds total; if still unresolved, fall back to serial interactive debugging and escalate to the user — never loop indefinitely

## Phase 4: Instrumentation

**action:** instrument decision boundaries dynamically
**format:** prefix logs with `[DEBUG-XXXX]`
**constraint:** target logs strictly; use profilers for performance

## Phase 5: Red-Green Fix

**action:** write regression test targeting the root-cause seam (not the symptom point)
**action:** confirm RED
**action (tournament only):** race candidate fixes via `multi-agent-dispatch` (`implementer`, `isolation: worktree`); pick the diff that is GREEN, passes N-1, and does not merely suppress the symptom
**action:** apply minimal fix on working copy
**action:** confirm GREEN
**action:** execute N-1 test (revert fix -> confirm RED -> restore fix)

## Phase 6: Finalization

**action:** remove all `[DEBUG-XXXX]` tags
**action:** verify fix via Phase 1 loop
**action:** re-run the original hypothesis set against the post-fix Oracle to catch masked/latent causes
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

**references/feedback-loops.md:** setup patterns by system type — these patterns build the Oracle
**references/phases.md:** detailed phases, hypothesis prioritization, profiling, tournament mechanics

## Output Format

**symptom:** [Description]
**root_cause:** [Correct Hypothesis]
**fix:** [Changes]
**feedback_loop:** [Reproduction Script]
**prevention:** [Architecture/Test improvement]
**next_steps:** [Follow-up tasks]
