# Spec Self-Check

Run this checklist after writing a spec. If any item fails, revise before handing off to `create-plan`.

---

## Mandatory — Contract & Blueprint

- [ ] **Goal**: One sentence. One measurable completion signal. No vague adjectives.
- [ ] **Requirements**: Each REQ/SEC/PERF/COMP states a single, testable obligation. No "and" joining two obligations in one line.
- [ ] **Constraints**: At least one CON statement defining what the solution does NOT do.
- [ ] **Interfaces**: Every public contract includes name, inputs, outputs, and error cases.
- [ ] **Acceptance Criteria**: At least one AC per core requirement, written as what the user observes.
- [ ] **Validation Steps**: At least one VAL per AC, with a specific verification command or action and expected outcome.

---

## Quality Signals

- [ ] No requirement uses unmeasured adjectives: "lightweight", "clean", "robust", "fast" — replace with thresholds (e.g., "< 200ms p99").
- [ ] No mixed requirements + design (design decisions go in Notes & Risks, not Requirements).
- [ ] All acronyms defined on first use (e.g., "JWT (JSON Web Token)").
- [ ] All unknowns labeled `UNKNOWN: [what and why]`, not left blank or guessed.
- [ ] Requirements use active voice: "The system MUST validate…" not "Validation MUST be performed…".

---

## Red Flags — Revise Before Handing Off

- Any REQ that cannot be tested → add a corresponding AC or split into smaller requirements.
- Interface section missing error cases → add at minimum: invalid input, auth failure, downstream/timeout failure.
- No edge cases in section 7 → add: null/empty input, boundary values, concurrent request behavior.
- Notes & Risks is empty for a Blueprint spec → add at least one RISK entry.
- Any section contains `CONFLICT:` → the conflict must be resolved or explicitly deferred with stakeholder sign-off.

---

## Ready Signal

If all mandatory items pass and no red flags remain, the spec is ready for the `create-plan` skill.
