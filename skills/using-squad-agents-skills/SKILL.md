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

## Lifecycle Diagram

Read top-to-bottom. `──►` is a transition; `── cond ──►` is a branch. Skill targets are in `[brackets]`. Each gate has one entry question and fixed pass/fail exits — no skill re-evaluates an upstream gate.

```
START ─ new task
  │
  ▼
Gate 0 · Repo onboarded? ── no AGENTS.md ────────► [project-init] (recommendation) ──► Gate 1
  │  pass: AGENTS.md present
  ▼
Gate 1 · Task defined?
  │
  ├── vague / open solution space ───────► [parallel-brainstorming] ─► Gate 1.5
  ├── idea only, no plan/spec yet ───────► [request-plan] ───────────► Gate 1.5
  ├── spec+plan exist, Status: DRAFT ────► [receive-plan] ───────────► Gate 1.5
  └── pass: spec+plan exist, APPROVED ──► Gate 2
  ▼
Gate 1.5 · Plan approved? ── reached from any Gate 1 drafting route
  │
  ├── REVISE (High finding | ≥2 Med) ───► fix at origin ──► [receive-plan] (cap per its rules)
  └── pass: APPROVED ───────────────────► Gate 2
  ▼
Gate 2 · Systemic or localized?
  │
  ├── boundary / God class / circular deps / 2+ files ──► [project-audit] ──► Gate 3
  ├── crash / bug / unexpected behavior ───────────────► [diagnose] ──────► (resolved) Gate 2-resume
  ├── messy function, single file, no boundary crossed ► Gate 3 (fix inline via TDD)
  └── pass: new feature, scope clear ──────────────────► Gate 3
  ▼
Gate 3 · Execution strategy
  │
  ├── trivial (<~20 lines) OR standard/focused ──► [test-driven-development] ─► Gate 3.5
  └── 2+ tasks (any shape) ───────────────────────► [dispatch-agents] ────────► Gate 3.5
  ▼
Gate 3.5 · Stuck or clean? ── reached from either Gate 3 route
  │
  ├── TDD: 3 failed attempts on same test ──► [diagnose] ──► Gate 3 (retry)
  ├── TDD: spec ambiguous ──────────────────► [request-plan] ─► Gate 3 (retry)
  └── pass: clean GREEN + full coverage ───► Gate 4
  ▼
Gate 4 · Quality & delivery ── linear, no branching back upstream
  │
  ▼
Gate 4a · [verification-before-completion]  ── gate: execution evidence, never code-reading alone
  │  fail: trivial-only exit per its Decision Logic ──► DONE
  ▼
Gate 4b · [request-code-review]
  │
  ├── PASS ──────────────────────────────► Gate 4c
  └── FAIL ─────────────────────────────► [receive-code-review]
        │
        ├── blocking issue ──► [diagnose] ───────────► Gate 4b (re-review, cap 2)
        ├── hygiene issue ───► fix inline ───────────► Gate 4b (re-review, cap 2)
        └── re-review cap exceeded ──► escalate to user
  ▼
Gate 4c · [write-commit]  ── gate: atomic, secret-scanned
  ▼
Gate 4d · [pr-workflow]  ── CONFIRM PUSH (first irreversible / outward-facing step)
  │
  ├── not yet reviewed ──► [request-code-review] (handoff)
  └── git/gh fails ──────► [diagnose]
  ▼
Gate 4e · merge ── gate: explicit go-ahead only ── DONE
```

## Gate Reference

| Gate | Entry question                           | Pass route                                   | Fail route                                                                  |
| :--- | :--------------------------------------- | :------------------------------------------- | :-------------------------------------------------------------------------- |
| 0    | Repo onboarded (AGENTS.md)?              | → Gate 1                                     | [project-init] (recommended, never auto)                                    |
| 1    | Task fully defined (APPROVED spec+plan)? | → Gate 2                                     | vague→[parallel-brainstorming]; idea→[request-plan]; DRAFT→[receive-plan]   |
| 1.5  | Plan approved after drafting?            | → Gate 2                                     | REVISE → fix at origin → [receive-plan]                                     |
| 2    | Systemic issue or localized?             | new feature → Gate 3                         | structural→[project-audit]; bug→[diagnose]; single-file messy→Gate 3 inline |
| 3    | Execution strategy?                      | trivial/standard → [test-driven-development] | 2+ tasks → [dispatch-agents]                                                |
| 3.5  | TDD stuck or clean?                      | clean GREEN → Gate 4                         | 3 attempts→[diagnose]; ambiguous→[request-plan]                             |
| 4a   | Verified by execution?                   | → Gate 4b                                    | trivial-only → DONE                                                         |
| 4b   | Review PASS?                             | → Gate 4c                                    | FAIL → [receive-code-review]                                                |
| 4c   | Committed atomically?                    | → Gate 4d                                    | —                                                                           |
| 4d   | Pushed + PR open?                        | → Gate 4e                                    | not reviewed→[request-code-review]; fail→[diagnose]                         |
| 4e   | Merge approved?                          | DONE                                         | escalate to user                                                            |

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
