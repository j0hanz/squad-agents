Chosen Approach:: Approach A — Declarative Workflow Validation Skill
Why:: It automates verification of codebase health using existing validation logic on files changed by the agent/developer, preventing regression and satisfying the stakeholder requirement for saved manual verification time while keeping the system lightweight and aligned with Bash-only hook constraints.
Scope:: M
Success Criteria:: Saves significant manual developer validation/testing time and runs checks synchronously during development sessions.
Constraints::
- Flat YAML frontmatter in `SKILL.md` (keys: `name`, `description`).
- Hook handlers must be Bash-only (no JS/Python/MJS in `hooks/hooks.json`).
- ESM import/export syntax only.
Interface::
- Skill file: [skills/workflow-validator/SKILL.md](file:///C:/agent-dev/skills/workflow-validator/SKILL.md)
- Hook file: [hooks/workflow-validation.sh](file:///C:/agent-dev/hooks/workflow-validation.sh)
- Hook config: [hooks/hooks.json](file:///C:/agent-dev/hooks/hooks.json)
Architecture::
- An event-triggered Bash hook (`hooks/workflow-validation.sh`) intercepts file changes or session stops, calling the existing plugin validator (`bin/validate-plugin.mjs`).
- The `workflow-validator` skill provides detailed instructions guiding the agent on how to interpret validation reports, resolve structural violations, and auto-fix lints.
Risk Register::
- Risk: Too frequent validation runs could slow down quick tool iterations.
- Mitigation: Hook only runs on key events (e.g. SessionEnd or PostToolUse with debounce, or pre-commit).
Review Disposition:: Approved (Phase 5 skipped as scope is M and no high-risk flags were set).
First Step:: Create the `skills/workflow-validator` directory and populate `SKILL.md` with YAML metadata.
