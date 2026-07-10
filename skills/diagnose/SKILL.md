---
name: diagnose
description: 'Use when a bug, crash, test failure, or unexpected behavior needs root-cause analysis before a fix. Prefer over test-driven-development when diagnosing an existing defect, not building a feature.'
disable-model-invocation: false
argument-hint: '[symptom description or error trace]'
allowed-tools: Agent(researcher), Agent(implementer), AskUserQuestion, Bash(git *), Read, Grep, Glob, Skill(dispatch-agents)
---

# diagnose

Identify true root cause through systematic falsification. **DO NOT GUESS.**

## Process Flow

- **Phase 0:** Triage (serial vs. tournament)
- **Phase 1:** Build Feedback Loop (lock the Oracle)
- **Phase 2:** Reproduce (confirm bug; tournament-only: race repro strategies)
- **Phase 3:** Hypothesize & Falsify (3-5 propositions)
  - _serial_: probe one hypothesis directly; falsified -> next hypothesis
  - _tournament_: fan blind Falsifiers, 1 proposition/worktree
- **Phase 3.5:** Converge & Arbitrate (replay survivors; decide by mechanism)
  - _REVISE_ (entangled survivors): re-bracket, retry 3.5
  - _REJECT_ (0 survive, <2 rounds): retry Phase 3 with new hypotheses
  - _REJECT_ (0 survive, 2 rounds spent): fall back serial, escalate to user
- **Phase 4:** Instrumentation (targeted probes)
- **Phase 5:** Red-Green Fix (regression test on root-cause seam; tournament-only: race fixes)
- **Phase 6:** Finalization (de-instrument / verify / re-check for masked causes)

**constraint:** 1 falsifiable proposition per run (tournament mode: 1 per worktree)
**constraint:** modify working copy only
**constraint:** reject "works on my machine"

## Phase 0: Triage

**action:** default to serial — probe one hypothesis at a time, directly
**action:** escalate to tournament (Phase 3 tournament path) only when 3+ genuinely independent candidate causes exist, or the bug is flaky/stress-class
**Done when:** triage mode is selected — tournament only for 3+ independent causes or flaky/stress-class bugs; never tournament a single obvious cause (e.g. one-line null check).

## Phase 1: Feedback Loop

**action:** create <2s deterministic pass/fail signal — this loop is the **Oracle** Phase 3.5 arbitrates against
**action:** isolate filesystem, pin seeds/time
**action:** if no deterministic loop achievable, raise repro rate via stress (`references/feedback-loops.md`) — degrade to serial interactive debugging, never block the skill
**mandatory:** read `references/feedback-loops.md` (do NOT load `references/phases.md`)
**Done when:** a deterministic <2s Oracle is locked, or telemetry/logs requested and the loop is unbuildable.

## Phase 2: Reproduce

**action:** achieve >50% reproduction rate
**action (tournament only):** race 2-3 candidate repro strategies via `dispatch-agents`; keep the fastest deterministic >50% strategy and lock it as the Oracle
**Done when:** a logged reproduction signal at >50% rate is captured, ready for Phase 3.

## Phase 3: Hypothesize & Falsify

**mandatory:** read `references/phases.md` (do NOT load `references/feedback-loops.md`)
**action:** propose 3-5 falsifiable hypotheses via `AskUserQuestion` (surface top 3, queue rest)
**format:** "If [X] is the cause, then [Y] will change when I do [Z]." (conjunctions allowed: "If [X] AND [Y]...", for interaction bugs)
**serial path (default):** probe one hypothesis directly against the Oracle
**tournament path (Phase 0 escalated):** dispatch via `dispatch-agents`, one falsifiable proposition per worktree, lanes blind to siblings

- **role:** observational/static probe -> read-only `researcher` agent (`agents/researcher.md`); instrumented/executed probe -> worktree-isolated `implementer` agent (`agents/implementer.md`) with `isolation: worktree`
- **contract:** 5-field cold-start (SCOPE/OBJECTIVE/CONTEXT/CONSTRAINTS/OUTPUT) per `../dispatch-agents/references/subagent-contract.md`
- **concurrency:** background-exempt only with a notify primitive; else batch lanes in <=3
- **output:** `VERDICT: SURVIVED | KILLED` + EVIDENCE (the probe as a runnable block, asserting the predicted mechanism effect Y — not just the Oracle bit)
- **narration:** report each lane's verdict to the user as it completes — no silent background batch
  **Done when:** a confirmed probe result is in hand for each hypothesis (no guessing by elimination).

## Phase 3.5: Converge & Arbitrate

**action:** replay every `SURVIVED` lane's probe on the main checkout against the Oracle — never trust a lane's self-reported `VERDICT`
**action:** converge by mechanism, not count — collapse aliases (same cause, different abstraction) into one cause; report multiple causes if genuinely distinct; flag indistinguishable survivors as entangled
**rule:** never-self-arbitrate — the agent that proposed a hypothesis never declares it the root cause
**routing:** `APPROVED` (resolved) -> Phase 4 | `REVISE` (entangled survivors) -> re-bracket with disjoint probes, retry 3.5 | `REJECT` (0 survive) -> retry Phase 3 with new hypotheses
**Done when:** a survivor is `APPROVED` to Phase 4, or after max 2 unresolved rounds, fall back to serial and escalate to the user — never loop indefinitely.

## Phase 4: Instrumentation

**action:** instrument decision boundaries dynamically
**format:** prefix logs with `[DEBUG-XXXX]`
**constraint:** target logs strictly; use profilers for performance
**Done when:** all candidate root causes ranked by evidence AND the top hypothesis has a defined falsification probe

## Phase 5: Red-Green Fix

**action:** write a regression test targeting the root-cause seam (not the symptom point).
**action (tournament only):** race candidate fixes via `dispatch-agents` (`implementer`, `isolation: worktree`); reject any GREEN that suppresses the symptom without addressing the asserted invariant.
**delegation:** Apply the fix via test-driven-development (RED-GREEN-N-1) on the root-cause seam; in tournament mode, race implementer lanes and reject any GREEN that suppresses the symptom without addressing the asserted invariant.
**Done when:** the regression test is green, passes the N-1 check, and the minimal fix is committed to the working copy.

## Phase 6: Finalization

**action:** remove all `[DEBUG-XXXX]` tags
**action:** verify fix via Phase 1 loop
**action:** re-run the original hypothesis set against the post-fix Oracle to catch masked/latent causes
**action:** promote scripts to test suite or delete
**Done when:** no `[DEBUG-XXXX]` tags remain grep-clean AND the original hypothesis set re-runs clean on the post-fix Oracle

## Worked Example

Symptom: `POST /orders` 500s intermittently in staging, never locally.

- **Phase 0:** one plausible cause in the stack trace (null `cart.discount`) → serial, not tournament.
- **Phase 1:** Oracle = `curl` the endpoint with a cart fixture missing `discount`; deterministic, <1s.
- **Phase 2:** reproduces 10/10 → well above the 50% gate.
- **Phase 3:** hypothesis — "If `discount` is read before the null-check, setting `discount: undefined` in the fixture triggers the same 500." Probed directly against the Oracle: confirmed.
- **Phase 3.5:** single survivor, no entanglement → `APPROVED`, proceed.
- **Phase 4:** `[DEBUG-4471]` log at the read site confirms `discount` is `undefined` at the point of failure.
- **Phase 5:** regression test asserts 200 + default discount applied when the field is absent; RED before fix, GREEN after; N-1 (revert → RED → restore → GREEN) confirms the fix is load-bearing.
- **Phase 6:** `[DEBUG-4471]` removed, Oracle re-run clean, original hypothesis set re-run post-fix to rule out a masked second cause. Reported via `## Output Format` below.

## Next Skills

| Skill                                                          | Use Case                                        |
| :------------------------------------------------------------- | :---------------------------------------------- |
| [test-driven-development](../test-driven-development/SKILL.md) | For implementing new logic and regression tests |
| [project-audit](../project-audit/SKILL.md)                     | For cleaning up multiple files or modules       |
| [request-plan](../request-plan/SKILL.md)                       | For major specification gaps                    |

## References

| Reference                                         | Purpose                                                                     |
| :------------------------------------------------ | :-------------------------------------------------------------------------- |
| [feedback-loops.md](references/feedback-loops.md) | Setup patterns by system type to build the Oracle                           |
| [phases.md](references/phases.md)                 | Detailed phases, hypothesis prioritization, profiling, tournament mechanics |

## Output Format

**symptom:** [Description]
**root_cause:** [Correct Hypothesis]
**fix:** [Changes]
**feedback_loop:** [Reproduction Script]
**prevention:** [Architecture/Test improvement]
**next_steps:** [Follow-up tasks]
