# Reference: Phases

## Phase 0: Triage (serial vs. tournament)

- **Default:** serial. One hypothesis, one probe, directly against the Oracle — faster and correct for the common case (single obvious cause: null check, off-by-one, missing await).
- **Escalate to tournament when:** 3+ genuinely independent candidate causes survive initial triage, or the bug is flaky/stress-class (low/unclear repro rate, suspected race). Mirrors `dispatch-agents`'s "3+ tasks in separate files with unrelated causes" heuristic.
- **Anti-pattern:** tournament on a one-cause bug. Worktree setup + blind-lane dispatch + arbitration costs more than just fixing it — proportionality is load-bearing, not optional ceremony.

## Phase 1: Build a Feedback Loop

- **Importance:** Foundation. Single source of truth.
- **Loop_Selection_Tree:**
  - Testable code -> Unit/Integration/E2E test
  - API/HTTP -> Curl/REST script
  - UI/Frontend -> Headless browser (Playwright)
  - Timing issue -> Trace capture & replay
  - Complex system -> Minimal throwaway harness
  - Flakiness -> Stress loop (100+ iterations, concurrent)
  - Regression between commits -> Bisection harness (`git bisect`)
  - Manual flow -> Human-in-the-loop script
- **Improvement_Targets:**
  - **Speed:** Cache setup, skip unrelated initialization.
  - **Signal:** Assert exact error, avoid generic "didn't crash" checks.
  - **False_Negatives:** Assertion too loose.
  - **False_Positives:** Assertion too strict / env-specific.
- **Failure_Protocol:** If no loop is buildable, stop. Ask the user for environment access, captured artifacts, or permission to add production telemetry.

## Phase 2: Reproduce

- **Risk:** "Wrong Bug" Trap — reproduced bug must match the user report exactly.
- **Flakiness_Threshold:** <50% repro rate is un-debuggable — signal-to-noise is too low to tell whether a later fix worked or the bug just didn't fire. Return to Phase 1, add stress/concurrency to raise rate.
- **Capture_State:** Record full error, input, actual vs expected, timing, environment before proceeding.

## Phase 3: Hypothesize

- **Quality:** Must be testable (e.g., "Connection pool exhausted: increase MAX_CONNECTIONS to see if timeout vanishes").
- **Ranking:** Bayesian prior (Recent changes > Code > Environment > External).
- **Efficiency:** Rule out hypotheses cheaply — ask the user about recent changes or environment differences.
- **Conjunctions:** A hypothesis may be a conjunction ("if X AND Y, then Z") — how interaction bugs (only reproduce when two conditions co-occur) get represented as ONE falsifiable proposition rather than forced into two unfalsifiable single-variable lanes.
- **Tournament dispatch (Phase 0 escalated only):** one proposition per worktree, lanes blind to each other. Role by probe type — observational/static (read a value, check a log) -> read-only `researcher` agent (`agents/researcher.md`); instrumented/executed (add logging, run code, modify state) -> worktree-isolated `implementer` agent (`agents/implementer.md`) with Bash+Write. Never assign a write-requiring probe to a read-only agent.
- **Mechanism-linked probes:** a probe must assert the predicted intermediate effect Y, not just whether the Oracle flips. A probe that flips the Oracle bit via an unrelated side effect (touched shared state, shifted timing) is a false `SURVIVED` — Phase 3.5 inspects for the predicted signature, not the bare flip.

## Phase 3.5: Converge & Arbitrate

- **Replay, don't trust:** every `SURVIVED` verdict is replayed by the orchestrator on the main checkout against the Oracle before it counts. A lane's self-report is a claim, not evidence.
- **Converge by mechanism:** if 2+ lanes survive, check whether they describe the _same_ underlying cause at different abstraction levels (e.g., "null deref in parser" and "missing validation upstream of parser") — collapse aliases into one cause rather than picking arbitrarily. If genuinely distinct, report both; don't force a single answer.
- **Masking:** a hypothesis can report `KILLED` only because another still-latent cause is dominant in that worktree. Phase 6 re-runs the full original hypothesis set against the post-fix Oracle — a masked cause resurfaces once the masking cause is removed.
- **Entangled survivors:** if survivors produce indistinguishable probe evidence (same flip, no distinguishing trace), don't guess — `REVISE`: re-bracket with new, more targeted disjoint probes.
- **Never-self-arbitrate:** the agent (or reasoning thread) that proposed a hypothesis must not be the one that confirms it as root cause — mirrors `parallel-brainstorming`'s arbiter rule.
- **Termination:** 2 rounds max. A third unresolved round means the hypothesis space itself is wrong (missing variable, wrong abstraction level) — stop fanning out, escalate to the user with what was learned.

## Phase 4: Instrument

- **Debugger_Advantage:** Pausing state > printing state. Use if environment permits.
- **Targeted_Logging:** Log strictly at decision boundaries.
- **Log_Tagging:** MUST use unique prefix (`[DEBUG-XXXX]`). Makes cleanup a single grep.
- **Performance_Bugs:** Do NOT use logs (overhead distorts timing). Use profilers or `performance.now()` diffs.
  - **Python:** `python -m cProfile -s tottime script.py`, or `mprof run script.py && mprof plot`.
  - **Node.js:** `node --cpu-prof script.js`, analyze the `.cpuprofile` in Chrome DevTools (`chrome://inspect` -> Profiler -> Load).

## Phase 5: Fix + Regression Test

- **Seam_Definition:** The level of isolation where the test runs.
- **Bad_Seam:** Too shallow (mocking the buggy component) or too deep (full E2E for a simple math error).
- **Good_Seam:** Integration test for race conditions; Unit test for pure logic. Lock the test on this seam — the root cause — never on the symptom's observation point (e.g., assert the actual invariant the bug violated, not just "no exception thrown").
- **Exemption:** If no correct seam exists (e.g., hardware specific), document the limitation in the fix.
- **Fix race (tournament only):** if multiple plausible fixes exist, race them as `implementer` lanes in separate worktrees against the locked, root-cause-seam regression test. Reject any candidate that goes GREEN by suppressing the symptom (catching/swallowing, clamping a value) without addressing the asserted invariant — a race optimizes for "passes the gate," so the gate must encode the real seam.

## Phase 6: Cleanup + Post-Mortem

- **De-instrumentation:** Remove all `[DEBUG-XXXX]` tags.
- **Masked-cause check:** re-run the original hypothesis set (including `KILLED` ones) against the post-fix Oracle. A hypothesis killed only because the just-fixed cause masked it now resurfaces — catch it here, not in production.
- **Review_Question:** "What would have prevented this bug?"
- **Delegation_Paths:**
  - "Better test coverage" -> Activate `test-driven-development` skill.
  - "Tangled logic spanning multiple files/modules" -> Activate `project-audit` skill.
  - "API contract vague" -> Update docs.
