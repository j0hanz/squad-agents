---
name: using-agent-sdlc-skills
description: "Orchestrates software engineering tasks by analyzing user prompts and routing them to the optimal workflow in the development lifecycle. Accepts any high-level task description, bug report, or feature request as input, and outputs a diagnostic recommendation or transition to the target tool. Trigger on: 'start task', 'route work', 'using-agent-sdlc-skills', 'skill selection', 'task diagnostic', 'orchestrate development'. Also triggers when the workspace requires a multi-stage routing check for new issues, PR reviews, or system refactoring. Always prefer this orchestrator over individual tools (like diagnose or request-plan) for initial user prompts to ensure correct lifecycle gating."
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<ROUTING-PRINCIPLE>
If a skill has strong relevance to your task, route to it. Routing decisions follow the gate matrix below. You may skip a skill only if: (1) Gate 3 triviality fast-path applies (trivial <~20 line changes), (2) the Skip Disclaimer indicates a skill is unavailable, or (3) the current task is clearly a subagent delegation (see SUBAGENT-STOP above). Otherwise, follow the routing decisively.
</ROUTING-PRINCIPLE>

## When to Use

```
Start: New Task
  -> [Any Gate] Context Bloated / Token Limit Near? --> context-optimizer --> resume same gate
  -> Gate 0: Repo Onboarded?
       -- no AGENTS.md (recommendation) --> codebase-init --> Gate 1
       -- onboarded ------------------------------------------> Gate 1

Gate 1: Fully Defined?
  -- vague/no spec ------------------> parallel-brainstorming
  -- idea only -----------------------> request-plan
  -- spec+plan exist, unverified -----> receive-plan
  -- spec+plan exist, verified -------> Gate 2

Gate 2: Systemic Issue?
  -- boundary/God class/2+ files ----------------------> architecting
  -- messy function, single file, no boundary crossed -> Gate 3 (fix inline)
  -- crash/bug --------------------------------------> diagnose
  -- new feature -------------------------------------> Gate 3

Gate 3: Execution Strategy
  -- CI/CD workflow (GitHub Actions, gh CLI scripting) --> gh-actions (User invocation required)
  -- trivial (<~20 lines) OR standard/focused --> test-driven-development
  -- independent --------------------------------> multi-agent-dispatch
  -- sequential/complex -------------------------> multi-agent-development
  test-driven-development -- stuck after 3 attempts --> diagnose --> back to Gate 3 (retry)
  test-driven-development -- spec ambiguous ----------> request-plan --> back to Gate 3
  [dispatch | development | TDD] --> Gate 4

Gate 4: Quality & Delivery
  -> verification-before-completion -> request-code-review
       -- PASS (recommendation) --> pr-workflow
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
- **Notification:** Announce the route as plain text: `✅ Routing to [<skill-name>]: [reason]`. This is an FYI, not a decision — don't spend a blocking `AskUserQuestion` just to acknowledge a routing choice the matrix/gates already determined.
- **No Skips:** Never bypass process gates for "simple" or "quick" tasks.
- **Context Constraints:** Route to `context-optimizer` at any gate if the active context is bloated or token limits are approached, pruning memory before continuing the task (see the `[Any Gate]` branch in the diagram above — it preempts whichever gate is active).

---

## Diagnostic Decision Tree

### Gate 0: Repository Onboarding

- **Missing `AGENTS.md`/`CLAUDE.md`:** Recommend `codebase-init` (User invocation required).
- **Onboarded:** Proceed to Gate 1.

### Gate 1: Task Definition

- **Vague concept:** Route to `parallel-brainstorming`.
- **Needs concrete plan:** Route to `request-plan`.
- **Spec and plan exist, unverified:** Route to `receive-plan` directly (skip drafting).
- **Spec and plan exist, verified:** Proceed to Gate 2.

### Gate 2: Scope & System

- **Systemic / 2+ files / module boundaries:** Route to `architecting`.
- **Localized / single file / messy function:** Fix inline, then proceed to Gate 3.
- **Active bug / crash:** Route to `diagnose`.
- **Tie-break (1 main file + 1 trivial edit):** Proceed to Gate 3.
- **Planned feature:** Proceed to Gate 3.

### Gate 3: Execution Strategy

- **CI/CD workflow (GitHub Actions YAML, gh CLI batch/API scripting):** Recommend `gh-actions` (User invocation required — never auto-invoked).
- **Trivial change (<20 lines, 1 file):** Route to `test-driven-development` (skip dispatch question).
- **Independent tasks (time constrained):** Route to `multi-agent-dispatch`.
- **Sequential tasks (context constrained):** Route to `multi-agent-development`.
- **Mixed DAG tasks:** Route to `multi-agent-development` (batch tasks with gated reviews).
- **Standard single feature:** Route to `test-driven-development`.
- **TDD fails 3 times:** Route to `diagnose` (stuck) or `request-plan` (ambiguous spec).
- **Autonomous by default:** `test-driven-development`, `request-code-review`, `multi-agent-development`, and `multi-agent-dispatch` are all safe enough to run directly and announce the route without stopping for a go-ahead — but each earns that safety differently: `test-driven-development` edits directly in the main thread and is test-gated (red-green-refactor) rather than isolated; `request-code-review` dispatches a read-only agent (`diff-reviewer`, Write/Edit denied) that never writes, so there's nothing to isolate — its safety is tool-restriction; `multi-agent-development` and `multi-agent-dispatch` dispatch Writer-role agents under `isolation: worktree` and are test-gated before merge. Ask first only when a step is genuinely irreversible outside whatever guard applies (a destructive command, a push, a migration) or it's the first dispatch of the session and the user hasn't seen the behavior yet.

### Gate 4: Quality & Delivery

- **Execution Complete:** Route to `verification-before-completion`.
- **Security & Quality Check:** Route to `request-code-review` (Mandatory).
- **Review Passes:** Recommend `pr-workflow` (User invocation required — confirms before push).
- **Review Fails:** Route to `receive-code-review` (loops to `diagnose`, capped at 2 cycles).

---

## Diagnose Return Paths

- **From Gate 2 (Systemic Bug):** Return to Gate 3 after resolution to resume feature work.
- **From Gate 3 (TDD Stuck):** Return to Gate 3 to retry implementation post-fix.
- **From Gate 4 (Review Blocker):** Return to Gate 4 for re-review. Escalate to `architecting` if systemic.

---

## Strict Constraints (NEVER List)

- **NEVER** route to `test-driven-development` if Gate 1 is incomplete.
- **NEVER** use `multi-agent-dispatch` for tasks with shared state or dependencies.
- **NEVER** skip `diagnose` when a bug interrupts feature work.
- **NEVER** allow infinite TDD retries (strictly capped at 3).
- **NEVER** skip `request-code-review` after multi-agent development.
- **NEVER** auto-invoke `codebase-init` or `gh-actions`; `pr-workflow` is recommended at Gate 4 but never pushes without an explicit go-ahead.
- **NEVER** dispatch subagents (Gate 3) for trivial inline edits.

---

## Auxiliary Information

- **Reference:** `references/lifecycle.md` (State transitions).
- **Next Skills:** Ecosystem skills determine successors based on the identified route.
- **Missing Skill Protocol:** Apply intent manually and output: `The <skill-name> skill is not installed. Proceeding without it.`
