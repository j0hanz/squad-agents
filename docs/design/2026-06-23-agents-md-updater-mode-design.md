# Codebase-Init Updater Mode Design Brief

* **Chosen Approach:** Approach A — Pre-Survey Mode Gate
* **Why:** Gating the flow behind an initial mode selection prompt is the safest approach when `AGENTS.md` exists. It prevents accidental overwrites and preserves the marker-based survey skip logic for existing configurations.
* **Scope:** 
  * **In-scope:** 
    * Add `Phase 0: Mode Selection` to [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md).
    * If `AGENTS.md` exists, prompt: "Update existing instructions (Recommended)" or "Generate fresh new skeleton".
    * If "Generate fresh" is selected, require an explicit confirmation prompt.
    * Update the dot/graphviz diagram in [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) to reflect this new gate.
  * **Out-of-scope:** Modifying CLI arguments in `run.py` (since CLI behavior already supports scaffolding with `--out`).
* **Success Criteria:**
  * [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md) passes validation via `python skills/codebase-init/scripts/run.py validate-skills`.
* **Constraints:** Maintain instructions clarity for the interpreting agent, as the model invocation is disabled for the skill execution.
* **Interface:**
  * Initial Mode Selection `AskUserQuestion` call.
  * Overwrite confirmation `AskUserQuestion` call.
* **Architecture:** 
  * Orchestrated entirely within [SKILL.md](file:///C:/agent-dev/skills/codebase-init/SKILL.md).
* **First Step:** Write the design brief to `docs/design/2026-06-23-agents-md-updater-mode-design.md`.
