---
name: using-squad-agents-skills
description: 'Use when starting a new task and the correct starting point, lifecycle gate, or routing among skills is unclear.'
disable-model-invocation: true
allowed-tools: Skill, Read, Glob
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<ROUTING-PRINCIPLE>
Route to any skill with strong relevance to the task. Routing follows the gate matrix below. Skip a skill only if (1) Gate 3 triviality fast-path applies (<~20 line changes), (2) the Skip Disclaimer marks it unavailable, or (3) the task is a subagent delegation (see SUBAGENT-STOP). Otherwise follow the routing decisively.
</ROUTING-PRINCIPLE>

## Lifecycle Reference

_See the Gate Reference table below for the complete skill routing lifecycle._

## Gate Reference

| Gate | Entry question                           | Pass route                                   | Fail route                                                                  |
| :--- | :--------------------------------------- | :------------------------------------------- | :-------------------------------------------------------------------------- |
| 0    | Repo onboarded (AGENTS.md)?              | → Gate 1                                     | [project-init] (recommended, never auto)                                    |
| 1    | Task fully defined (APPROVED spec+plan)? | → Gate 2                                     | vague→[parallel-brainstorming]; idea→[request-plan]; DRAFT→[receive-plan]   |
| 1.5  | Plan approved after drafting?            | → Gate 2                                     | REVISE → fix at origin → [receive-plan]                                     |
| 2    | Systemic issue or localized?             | new feature → Gate 3                         | structural→[project-audit]; bug→[diagnose]; single-file messy→Gate 3 inline |
| 3    | Execution strategy?                      | trivial/standard → [test-driven-development] | 2+ tasks → [dispatch-agents]                                                |
| 3.5  | TDD stuck or clean?                      | clean GREEN → Gate 4                         | 3 attempts→[diagnose]; ambiguous→[request-plan]                             |
| 4    | Quality & delivery (Verify, Review, PR)? | DONE (merged)                                | verification-fail→DONE; review-fail→[receive-code-review]                   |

## Rules

- **Skill Shadowing:** Warn if a global skill version overrides the local `skills/` version.
- **Immediate Invocation:** Activate a skill the instant a route is identified.
- **Notification:** Announce the route as plain text: `✅ Routing to [<skill-name>]: [reason]`. FYI only — never spend a blocking `AskUserQuestion` to re-acknowledge a route the matrix already determined.
- **No Skips:** Never bypass a gate for "simple" or "quick" tasks; the triviality fast-path lives only at Gate 3.
- **Gate Matrix Scope:** Gates 0–4 govern entry-routing only (onboarding through first dispatch). Each skill's own `## Next Skills` stays canonical for its outbound transitions.
- **Hard-to-reverse decisions, mid-skill:** any skill hitting a hard-to-reverse branch (locking a design, picking a finding to act on, accepting risk vs re-drafting) calls `interview` rather than hand-rolling a question loop. A single isolated yes/no inside a tight loop is a confirmation, not a session — this does not apply.
- **Auto-invoke:** `test-driven-development`, `request-code-review`, and `dispatch-agents` are safe to invoke without asking — each is safety-gated (test-gated, read-only reviewer, worktree-isolated). Ask first only for irreversible steps (push, migration, destructive command) or the first dispatch of the session.

## Strict Constraints (NEVER List)

- **NEVER** route to `test-driven-development` if Gate 1 is incomplete.
- **NEVER** skip `diagnose` when a bug interrupts feature work.
- **NEVER** allow infinite TDD retries (strictly capped at 3).
- **NEVER** skip `request-code-review` after multi-agent development.
- **NEVER** auto-invoke `project-init`; `pr-workflow` is recommended at Gate 4 but never pushes without an explicit go-ahead.
- **NEVER** dispatch subagents (Gate 3) for trivial inline edits.
- **NEVER** merge (Gate 4e) without an explicit go-ahead — push confirmation at Gate 4d is not merge consent.

## Auxiliary Information

- **Next Skills:** Ecosystem skills determine successors based on the identified route.
- **Missing Skill Protocol:** Apply intent manually and output: `The <skill-name> skill is not installed. Proceeding without it.`
