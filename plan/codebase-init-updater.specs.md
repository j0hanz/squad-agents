# codebase-init-updater

## 1. Goal

- One sentence: Add an interactive Mode Selection gate to codebase-init's onboarding flow when `AGENTS.md` already exists, allowing the user to select between updating or overwriting.
- Completion signal: Skill validation succeeds and the Graphviz workflow shows the mode selection logic.

## 2. Requirements

- `REQ-001`: If `AGENTS.md` exists, the agent MUST ask the user whether they want to "Update existing instructions" (Recommended) or "Generate fresh new skeleton" via `AskUserQuestion` before proceeding.
- `REQ-002`: If "Generate fresh new skeleton" is selected, the agent MUST prompt for confirmation via a separate `AskUserQuestion` call before overwriting the file.
- `REQ-003`: If the user selects "Update existing instructions", the agent MUST bypass the policy survey upon detecting a valid marker.
- `REQ-004`: If "Update existing instructions" is selected but the marker is absent, the agent MUST run the 4 policy questions survey before regenerating.
- `REQ-005`: The developer MUST update the Graphviz diagram in [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) to document the new `Phase 0: Mode Selection` step.

## 3. Constraints

- `CON-001`: Do not bypass overwrite confirmation when generating a fresh skeleton over an existing `AGENTS.md` file.

## 4. Interfaces

The system exposes the following interfaces:

### Initial Mode Selection Prompt

**Input:**
- Choice between "Update existing instructions (Recommended)" and "Generate fresh new skeleton".

**Output:**
- Selected mode passed to the next step of the skill execution.

### Overwrite Confirmation Prompt

**Input:**
- Choice between "Yes, overwrite" and "Cancel".

**Output:**
- Confirmation decision.

## 5. Context

- Files: [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md)
- Current behavior: Gating checks only for marker presence to skip survey. It has no Mode Selection question.

## 6. Acceptance Criteria & Validation

- `AC-001`: The modified [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) passes the `validate-skills` command.
- `VAL-001`: `python skills/codebase-init/scripts/run.py validate-skills` runs and passes successfully.
- `AC-002`: The Graphviz flowchart in [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) has `Mode Selection` block correctly integrated.
- `VAL-002`: Inspect [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) for Graphviz definitions and verify they are valid.
- `AC-003`: Survey questions are successfully bypassed during update mode when a marker is present.
- `VAL-003`: Verify that the update flow skips policy prompts.
- `AC-004`: Overwriting prompts for confirmation if the user chooses to fresh-scaffold.
- `VAL-004`: Verify that the overwrite flow asks for confirmation.

## 7. Examples & Edge Cases

**Positive example:**
- User selects "Update existing instructions", marker is present: Survey skipped, discovery and scaffolding run preserving existing custom blocks.

**Edge cases:**
- User cancels at the confirmation prompt: Execution halts immediately.


