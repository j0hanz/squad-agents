---
topic: new-agent-skills-brainstorming
phase: 6
status: done
updated: 2026-06-24T14:24:00
---

# Memlog: Brainstorming New Agent-Dev Skills

## Phase 1: Discovery

### Codebase Context Report

**Feature area:** Brainstorming new skills (focused on Agent Workflow & Automation, and Agent-to-Agent Coordination) for the `claude-agent-dev-plugin`.

### Related Files
| File/Directory | Purpose |
| --- | --- |
| [skills/](file:///C:/agent-dev/skills) | Contains the existing 17 skills (such as `planning`, `multi-agent-dispatch`, etc.) |
| [hooks/](file:///C:/agent-dev/hooks) | Contains Bash-only lifecycle hooks like safety guards and telemetry capture |
| [AGENTS.md](file:///C:/agent-dev/AGENTS.md) | Lists hard rules, dependencies, and key conventions |
| [README.md](file:///C:/agent-dev/README.md) | Overview of the plugin, its features, and installation instructions |

### Terminology Found
- `skills` — `skills/` — Structured workflows/instructions configured with YAML frontmatter (name, description) that guide the agent.
- `hooks` — `hooks/` — Bash-only event-driven handlers (PreToolUse, PostToolUse, SessionStart, etc.) that run in the user's shell.
- `subagent` — `skills/multi-agent-dispatch` / `skills/multi-agent-development` — A secondary `general-purpose` agent context spawned to perform sub-tasks.

### Interface Shapes
None found (conceptual brainstorming).

### Technical Constraints
- Every skill in `skills/` must contain `SKILL.md` with flat YAML frontmatter (keys: `name`, `description`).
- Hook handlers must be Bash-only — no JS/Python/MJS files allowed in `hooks/hooks.json`.
- ESM import/export syntax only.

### Analogous Features
- Automation/Workflow skills: `context-optimizer`, `diagnose`, `planning`, `test-driven-development`.
- Coordination skills: `multi-agent-dispatch` (parallel fan-out), `multi-agent-development` (sequential, gate-checked implementation).

### Scope Signal
- **Estimate:** M
- **Reasoning:** Proposing and outlining new skills. Implementation would involve writing `SKILL.md` instructions and possible support scripts for new skill directories under `skills/`, which is low-to-medium risk.

### Key Unknowns
- Exact user pain points not covered by the current 17 skills.
- The degree of integration we can leverage from the CLI context (e.g. tracking token usage dynamically, monitoring git changes, or intercepting tools).

### Understanding Statement

The user wants to brainstorm new, highly valuable, intelligent, efficient, and convenient skills to implement in the `agent-dev` plugin. Based on the Stakeholder Probe, the brainstormed skills should specifically target:
1. **Agent Workflow & Automation** (automated debugging, code verification, context compression, test generation).
2. **Agent-to-Agent Coordination** (parallel multi-agent tasks, peer-review, auto-delegation).

These skills must fit the plugin's architectural guidelines (simple, robust, leveraging the `general-purpose` agent, Bash hooks for lifecycle events, and structured instructions).

---

## Phase 2: Domain Clarity
- **Resolved Term:** `Agent-Dev Principles` — Defined as: Minimizing agent bloat, avoiding custom agent runtimes, adhering to Bash-only hooks, and relying on structured instructions (KISS / Ponytail guidelines). Added to [glossary.md](file:///C:/agent-dev/glossary.md).

---

## Phase 3: Expert Clarification
- **Anti-Scope:**
  - Skills requiring heavy external infrastructure (databases, cloud queues, custom GUI wrappers).
  - Skills that overlap entirely with existing tools (e.g., refactor, planning) without a 10x workflow improvement.
- **Success Logic:** The new skills must save significant manual developer testing/verification time and reduce token usage during long sessions.

---

## Creative Checkpoint (Pre-Design)
- Checked for existing / analogous features. Currently, the repo contains 17 skills. None of the existing skills cover:
  1. Live telemetry-based debugging/replay or local session optimization based on CLI history.
  2. Peer-review orchestration where one subagent specifically plays the role of a QA engine or security checker to find bugs *before* submitting code.
  3. Dynamic context compilation or token auditing to optimize token usage of subagents.

---

## Phase 4: Design Proposal

### Design Proposals

#### Approach A — Declarative Workflow Validation Skill
**What:** A synchronous validation skill defined in `skills/workflow-validator/SKILL.md` that leverages a Bash-only hook handler in `hooks/hooks.json` to execute `bin/validate-plugin.mjs` on changes.
**Gains:** Drastically reduces manual testing/verification time by automatically running validation checks before/after agent tasks without modifying the agent runtime.
**Costs:** Lacks asynchronous capabilities or mechanisms for agents to coordinate with other agents.
**Fit:** Aligns with Constraint 1 (flat YAML frontmatter in `SKILL.md`) and Constraint 2 (Bash-only hooks in `hooks/hooks.json`), satisfying the stakeholder need for local plugin verification.
**First step:** Create `skills/workflow-validator/SKILL.md` with flat YAML frontmatter containing `name` and `description` keys.

#### Approach B — Decentralized File-Based Agent Coordination
**What:** An asynchronous, decentralized agent-to-agent coordination skill using text-based semaphores (markdown files in the workspace) to pass states between running agents, monitored by a Bash-only hook.
**Gains:** Facilitates coordination without requiring any heavy external infrastructure (such as databases or cloud queues) or custom agent runtimes.
**Costs:** Adds file polling overhead and carries minor risk of race conditions if multiple agents attempt to write to the same coordinator files simultaneously.
**Fit:** Avoids anti-scope infrastructure while adhering to the core principle of minimizing agent bloat and satisfying Constraint 2 (Bash-only hooks).
**First step:** Define the message board structure and locking schema in `skills/agent-coordinator/SKILL.md` with flat YAML frontmatter.

### Recommendation
**Approach A — Declarative Workflow Validation Skill**
This approach directly handles Constraint 2 (requiring hook handlers to be Bash-only) by using a lightweight Bash script to wrap the existing `bin/validate-plugin.mjs` validator, satisfying the internal agent developer stakeholder's need for automated verification. By automating validation on local hook execution, it directly meets the success criterion of saving significant manual developer testing time. Furthermore, it strictly avoids the anti-scope of custom runtimes or external databases, ensuring zero agent bloat for the internal agent developer.

**Deferred (YAGNI):**
- Database-backed multi-agent orchestration service (unjustified due to the anti-scope constraint against heavy external infrastructure).
- Real-time custom GUI monitoring wrapper (unjustified since the internal agent developer relies on CLI-based validation and structured rules).

---

## Phase 6: Transition

The final design brief has been persisted to [2026-06-24-workflow-validator-design.md](file:///C:/agent-dev/docs/design/2026-06-24-workflow-validator-design.md).
Chosen Approach: Approach A — Declarative Workflow Validation Skill.
