# Plan Review: codebase-init-updater

This document provides a detailed quality audit of the specification ([codebase-init-updater.specs.md](file:///C:/agent-dev/plan/codebase-init-updater.specs.md)) and the implementation plan ([codebase-init-updater.plan.md](file:///C:/agent-dev/plan/codebase-init-updater.plan.md)) for adding the interactive Mode Selection gate to the `codebase-init` onboarding flow.

---

## 1. Goal Evaluation

The primary objective is to add an interactive Mode Selection gate when an existing `AGENTS.md` is detected, allowing the user to select between updating the existing instructions or overwriting them with a fresh skeleton.

- **Verdict:** **Clear and well-defined.** The goal is concrete, scoped to a single file change (`SKILL.md`), and has clear acceptance criteria.

---

## 2. Specification Audit

The requirements cover the core flow logically:
- `REQ-001`: Detect pre-existing `AGENTS.md` and prompt the user for Mode Selection (Update vs. Fresh).
- `REQ-002`: Confirm overwrite before starting a fresh skeleton.
- `REQ-003`: Skip policy survey on Update mode if a valid marker is found.
- `REQ-004`: Fall back to the policy survey on Update mode if the marker is missing.
- `REQ-005`: Update Graphviz visualization.

### Edge Cases & Critical Nuances Audited

1. **Cancellation of Mode Selection (REQ-001):**
   - *Audit finding:* The specification mentions that cancelling at the confirmation prompt halts execution, but does not explicitly specify behavior if the user cancels or dismisses the initial Mode Selection prompt.
   - *Recommendation:* During implementation, the agent must treat a cancelled or dismissed Mode Selection prompt as an immediate halt condition (no partial files modified, exit code 0/1 depending on execution context), matching the existing Phase 0 cancellation policy.

2. **Preservation Rule Applicability (Update vs. Fresh):**
   - *Audit finding:* The existing `SKILL.md` contains a "Preservation rule" which states: *"all of its other existing sections (whatever their origin) must be preserved, not discarded, when the file is regenerated."*
   - *Recommendation:* When implementing the new logic in `SKILL.md`, it must be made explicitly clear to the executing agent that:
     - **"Update existing instructions"** honors the preservation rule.
     - **"Generate fresh new skeleton"** bypasses the preservation rule and overwrites/discards all pre-existing custom sections (after the user confirms the action).

3. **Marker Schema Anchoring:**
   - *Audit finding:* The specification properly references the existing anchor behavior (validating the `v1` token, ignoring malformed/other version markers). This is robust and prevents parser errors.

---

## 3. Plan Audit

The implementation plan ([codebase-init-updater.plan.md](file:///C:/agent-dev/plan/codebase-init-updater.plan.md)) divides the work into 5 implementation tasks and 1 acceptance task.

- **Atomicity:** Each task represents a single, well-defined modification to `SKILL.md` corresponding to one requirement.
- **Dependencies:** The sequential dependency chain (`TASK-001` -> `TASK-002` -> `TASK-003` -> `TASK-004` -> `TASK-005` -> `TASK-006`) is logical, as each step builds upon the previous instructions.
- **Traceability:** Excellent. Every task lists its target files, satisfied requirements/acceptance criteria, and validation step.
- **Validation:**
   - The validation uses `python skills/codebase-init/scripts/run.py validate-skills`.
   - *Note on line count:* `SKILL.md` is currently 176 lines, which already exceeds `Config.MAX_SKILL_LINES = 150` and raises a `WARN` (not `FAIL`). Since adding Mode Selection instructions will increase the line count further, this warning will persist. This is acceptable as it does not fail the validation gate.

---

## 4. Key Recommendations for Execution

1. **Explicit Halting on Mode Selection Cancel:** Ensure `SKILL.md` states: *"If the user cancels or dismisses the Mode Selection prompt, halt immediately."*
2. **Explicit Overwrite Behavior:** Clarify in `SKILL.md` that choosing to generate a fresh skeleton results in discarding any pre-existing custom sections, whereas updating preserves them.
3. **Graphviz Flowchart Clarity:** Update the Graphviz flowchart to clearly branch from `InitMode` to `Mode Selection` if `AGENTS.md` exists, then to the respective update/fresh paths, ensuring proper visual documentation of the onboarding state machine.

---

## 5. Summary of Plan Audit Results

- **Specs Status:** VALID
- **Plan Status:** VALID
- **Cross-check Status:** VALID
- **Findings addressed:** All minor findings and recommendations can be integrated directly during implementation under their respective tasks (no plan modification required).

ready_for_execution: true
