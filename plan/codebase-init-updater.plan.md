# codebase-init-updater

Spec: [codebase-init-updater.specs.md](file:///C:/agent-dev/plan/codebase-init-updater.specs.md)

## Goal

Add an interactive Mode Selection gate to codebase-init's onboarding flow when `AGENTS.md` already exists, allowing the user to select between updating or overwriting.

## PHASE-001: Implementation

### TASK-001: Implement REQ-001 (Phase 0 Mode Selection survey)

Depends on: none
Files: [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md)
Symbols: none
Satisfies: REQ-001
Action: Insert the initial Mode Selection step into [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md). Instruct the agent that if root `AGENTS.md` exists, they must prompt the user with "Update existing instructions (Recommended)" or "Generate fresh new skeleton".
Validate: `python skills/codebase-init/scripts/run.py validate-skills`
Expected result: The validation command prints PASS.

### TASK-002: Implement REQ-002 (Overwrite confirmation gate)

Depends on: TASK-001
Files: [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md)
Symbols: none
Satisfies: REQ-002
Action: Update [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) to instruct that if "Generate fresh new skeleton" is selected, the agent must require an explicit confirmation prompt ("Are you sure you want to overwrite...?") and halt if cancelled.
Validate: `python skills/codebase-init/scripts/run.py validate-skills`
Expected result: The validation command prints PASS.

### TASK-003: Implement REQ-003 (Marker-based survey bypass for Update mode)

Depends on: TASK-002
Files: [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md)
Symbols: none
Satisfies: REQ-003
Action: Update [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) instructions so that if "Update existing" is selected and a valid marker is found, the agent bypasses the policy survey and proceeds directly to Phase 1.
Validate: `python skills/codebase-init/scripts/run.py validate-skills`
Expected result: The validation command prints PASS.

### TASK-004: Implement REQ-004 (Survey fallback when marker absent in Update mode)

Depends on: TASK-003
Files: [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md)
Symbols: none
Satisfies: REQ-004
Action: Update [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) instructions so that if "Update existing" is selected but the marker is absent, the agent must ask the 4 policy questions (Phase 0 survey) before proceeding.
Validate: `python skills/codebase-init/scripts/run.py validate-skills`
Expected result: The validation command prints PASS.

### TASK-005: Implement REQ-005 (Graphviz diagram update)

Depends on: TASK-004
Files: [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md)
Symbols: none
Satisfies: REQ-005
Action: Update the dot diagram block at the top of [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) to document the Mode Selection gate and update-vs-fresh paths.
Validate: `python skills/codebase-init/scripts/run.py validate-skills`
Expected result: The validation command prints PASS.

## PHASE-END: Acceptance

### TASK-006: Final acceptance verification

Depends on: TASK-005
Files: none
Symbols: none
Satisfies: AC-001, AC-002, AC-003, AC-004
Action: Run full validation suite on the skill directory and review Graphviz formatting.
Validate: `python skills/codebase-init/scripts/run.py validate-skills`
Expected result: Skill validation command reports PASS.

