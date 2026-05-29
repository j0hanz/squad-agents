# Reference: Phases

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
- **Failure_Protocol:** If impossible to build a loop, stop. Explicitly ask user for environment access, captured artifacts, or permission to add production telemetry.

## Phase 2: Reproduce

- **Risk:** "Wrong Bug" Trap. Ensure reproduced bug matches user report exactly.
- **Flakiness_Threshold:** <50% repro rate is un-debuggable. Go back to Phase 1 and add stress/concurrency to increase rate.
- **Capture_State:** Record full error, input, actual vs expected, timing, and environment before proceeding.

## Phase 3: Hypothesize

- **Quality:** Must be testable. (e.g., "Connection pool exhausted: increase MAX_CONNECTIONS to see if timeout vanishes")
- **Ranking:** Bayesian prior (Recent changes > Code > Environment > External).
- **Efficiency:** Rule out hypotheses cheaply by asking user about recent changes or environment differences.

## Phase 4: Instrument

- **Debugger_Advantage:** Pausing state > printing state. Use if environment permits.
- **Targeted_Logging:** Log strictly at decision boundaries.
- **Log_Tagging:** MUST use unique prefix (`[DEBUG-XXXX]`). Makes cleanup a simple grep command.
- **Performance_Bugs:** Do NOT use logs (overhead distorts timing). Use profilers or `performance.now()` diffs.

## Phase 5: Fix + Regression Test

- **Seam_Definition:** The level of isolation where the test runs.
- **Bad_Seam:** Too shallow (mocking the buggy component) or too deep (full E2E for a simple math error).
- **Good_Seam:** Integration test for race conditions; Unit test for pure logic.
- **Exemption:** If no correct seam exists (e.g., hardware specific), document limitation in fix.

## Phase 6: Cleanup + Post-Mortem

- **De-instrumentation:** Remove all `[DEBUG-XXXX]` tags.
- **Review_Question:** "What would have prevented this bug?"
- **Delegation_Paths:**
  - "Better test coverage" -> Activate `test-driven-development` skill.
  - "Tangled logic" -> Activate `architecture` skill.
  - "API contract vague" -> Update docs.
