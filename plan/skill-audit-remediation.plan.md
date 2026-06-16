# skill-audit-remediation

Spec: [skill-audit-remediation.specs.md](skill-audit-remediation.specs.md)

## Goal

Remediate testing infrastructure gaps and standardize skill handoffs identified during the ecosystem audit.

## PHASE-001: Infrastructure Remediation

### TASK-001: Prune invalid test references in package.json

Depends on: none
Files: [package.json](package.json)
Symbols: none
Satisfies: REQ-001
Action: Remove the 12 non-existent test file paths from the `test:node` script in `package.json`.
Validate: `npm run test:node`
Expected result: The command executes without "file not found" errors.

### TASK-002: Add evals.json to multi-agent-development

Depends on: none
Files: [skills/multi-agent-development/evals.json](skills/multi-agent-development/evals.json)
Symbols: none
Satisfies: REQ-002
Action: Create a new `evals.json` file in the `multi-agent-development` skill directory with standard trigger cases.
Validate: `ls skills/multi-agent-development/evals.json`
Expected result: File exists and is valid JSON.

### TASK-003: Expand Python test discovery in pyproject.toml

Depends on: none
Files: [pyproject.toml](pyproject.toml)
Symbols: none
Satisfies: REQ-003
Action: Update `testpaths` in `pyproject.toml` to include all `skills/*/tests` and `skills/*/scripts/tests`.
Validate: `python -m pytest --collect-only`
Expected result: Pytest discovers tests across all skill directories.

## PHASE-002: Workflow Standardization

### TASK-004: Implement brief artifacts for design skills

Depends on: none
Files: [skills/brainstorming/SKILL.md](skills/brainstorming/SKILL.md), [skills/planning/SKILL.md](skills/planning/SKILL.md), [skills/architecture/SKILL.md](skills/architecture/SKILL.md)
Symbols: none
Satisfies: REQ-004
Action: Update design-heavy skills to explicitly state they produce `*-brief.json` for handoff.
Validate: Verify `SKILL.md` updates.
Expected result: Skills document the production of brief artifacts.

## PHASE-END: Acceptance

### TASK-005: Final acceptance verification

Depends on: TASK-001, TASK-002, TASK-003, TASK-004
Files: none
Symbols: none
Satisfies: AC-001, AC-002
Action: Verify all Acceptance Criteria from spec are observable in the running system.
Validate: `npm test`
Expected result: All AC items confirmed observable.
