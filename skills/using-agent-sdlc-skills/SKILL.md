---
name: using-agent-sdlc-skills
description: 'Use when starting a new task and the correct starting point, lifecycle gate, or routing among skills is unclear.'
disable-model-invocation: true
allowed-tools: Skill, Read, Glob
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<ROUTING-PRINCIPLE>
Route to any skill with strong relevance to the task. Routing decisions follow the gate matrix below. Skip a skill only if (1) Gate 3 triviality fast-path applies (<~20 line changes), (2) the Skip Disclaimer marks it unavailable, or (3) the task is a subagent delegation (see SUBAGENT-STOP). Otherwise follow the routing decisively.
</ROUTING-PRINCIPLE>

## When to Use

```
Start: New Task
  -> Gate 0: Repo Onboarded?
       -- no AGENTS.md (recommendation) --> project-init --> Gate 1
       -- onboarded ------------------------------------------> Gate 1

Gate 1: Fully Defined?
  -- vague/no spec ------------------> parallel-brainstorming
  -- idea only -----------------------> request-plan
  -- spec+plan exist, unverified -----> receive-plan
  -- spec+plan exist, verified -------> Gate 2

Gate 2: Systemic Issue?
  -- boundary/God class/2+ files ----------------------> project-audit
  -- messy function, single file, no boundary crossed -> Gate 3 (fix inline)
  -- crash/bug --------------------------------------> diagnose
  -- new feature -------------------------------------> Gate 3

Gate 3: Execution Strategy
  -- trivial (<~20 lines) OR standard/focused --> test-driven-development
  -- independent --------------------------------> multi-agent-dispatch
  -- sequential/complex -------------------------> multi-agent-development
  test-driven-development -- stuck after 3 attempts --> diagnose --> back to Gate 3 (retry)
  test-driven-development -- spec ambiguous ----------> request-plan --> back to Gate 3
  [dispatch | development | TDD] --> Gate 4

Gate 4: Quality & Delivery
  -> verification-before-completion -> request-code-review
       -- PASS (recommendation) --> write-commit --> pr-workflow
       -- FAIL ----------------------> receive-code-review
                                          -- blocking issue ------> diagnose
                                          -- hygiene issue -------> fix inline
                                          -- re-review (cap 2) ---> back to request-code-review

diagnose -- bug resolved, resume feature --> Gate 3
diagnose -- bug resolved, merge-ready ----> Gate 4
```

## Rules

- **Skill Shadowing:** Warn the user if a global skill version overrides the local `skills/` version.
- **Immediate Invocation:** Activate and follow a skill immediately once a route is identified.
- **Notification:** Announce the route as plain text: `✅ Routing to [<skill-name>]: [reason]`. FYI only — don't spend a blocking `AskUserQuestion` to acknowledge a routing the matrix/gates already determined.
- **No Skips:** Never bypass process gates for "simple" or "quick" tasks.
- **Gate Matrix Scope:** The Gate 0–4 matrix governs entry-routing only (Gate 0 onboarding through first dispatch at Gate 3); it does not re-describe a skill's own exit transitions. Each skill's `## Next Skills` section stays canonical for its outbound routing.
- **Hard-to-reverse decisions, mid-skill:** any skill hitting a hard-to-reverse branch point with the user (locking a design, picking which finding to act on, accepting risk vs. re-drafting) calls `interview` rather than hand-rolling its own question loop. A single isolated yes/no gate inside a tight loop is a confirmation, not a session — this does not apply.
- **Auto-invoke:** `test-driven-development`, `request-code-review`, `multi-agent-development`, and `multi-agent-dispatch` are safe to invoke without asking first — each is safety-gated (test-gated, read-only agent, or worktree-isolated). Ask first only for irreversible steps (push, migration, destructive command) or the first dispatch of the session.

## Strict Constraints (NEVER List)

- **NEVER** route to `test-driven-development` if Gate 1 is incomplete.
- **NEVER** use `multi-agent-dispatch` for tasks with shared state or dependencies.
- **NEVER** skip `diagnose` when a bug interrupts feature work.
- **NEVER** allow infinite TDD retries (strictly capped at 3).
- **NEVER** skip `request-code-review` after multi-agent development.
- **NEVER** auto-invoke `project-init`; `pr-workflow` is recommended at Gate 4 but never pushes without an explicit go-ahead.
- **NEVER** dispatch subagents (Gate 3) for trivial inline edits.

## Auxiliary Information

- **Next Skills:** Ecosystem skills determine successors based on the identified route.
- **Missing Skill Protocol:** Apply intent manually and output: `The <skill-name> skill is not installed. Proceeding without it.`
