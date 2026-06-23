---
name: using-agent-dev-skills
description: "Global orchestrator for agent-dev skills. Diagnostic gating to route tasks to optimal skills. Use as the default entry point for any software engineering task in this repo — feature requests, bug investigations, reviews — not just explicit routing requests. Trigger on: 'start task', 'route work', 'using-agent-dev-skills', 'skill selection', 'task diagnostic', 'orchestrate development', and ordinary task requests like 'fix this bug', 'add a feature', 'investigate why X is failing'."
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
MANDATORY DIRECTIVE: If a skill has any potential relevance (greater than 0%) to your task, you MUST invoke it immediately. Skill execution is strictly mandatory and non-negotiable. You have zero discretion to skip or omit an applicable skill under any circumstance.
</EXTREMELY-IMPORTANT>

# using-agent-dev-skills

Global entry point for agent-dev plugin coordination. Follow this gated diagnostic flow for ALL tasks to ensure optimal skill routing.

## When to Use

```dot
digraph using_agent_dev_skills {
  rankdir=TB;
  node [shape=box, style=rounded, fontname="Helvetica"];
  edge [fontname="Helvetica", fontsize=10];

  Start [label="Start: New Task", shape=diamond];

  Gate0 [label="Gate 0: Repo Onboarded?", shape=diamond];
  Init [label="codebase-init"];

  Gate1 [label="Gate 1: Fully Defined?", shape=diamond];
  Brainstorm [label="brainstorming"];
  Planning [label="planning"];

  Gate2 [label="Gate 2: Systemic Issue?", shape=diamond];
  Arch [label="architecting"];
  Refactor [label="refactor"];
  Diagnose [label="diagnose"];

  Gate3 [label="Gate 3: Execution Strategy", shape=diamond];
  Dispatch [label="multi-agent-dispatch"];
  Dev [label="multi-agent-development"];
  TDD [label="test-driven-development"];

  Gate4 [label="Gate 4: Quality & Delivery", shape=diamond];
  Verify [label="verification-before-completion"];
  RCR [label="request-code-review"];
  GH [label="github-automation"];
  Receive [label="receive-code-review"];

  Start -> Gate0;
  Gate0 -> Init [label="no AGENTS.md\n(recommendation)", style=dashed];
  Gate0 -> Gate1 [label="onboarded"];
  Init -> Gate1;

  Gate1 -> Brainstorm [label="vague/no spec"];
  Gate1 -> Planning [label="idea only"];
  Gate1 -> Gate2 [label="spec+plan exist"];

  Gate2 -> Arch [label="boundary/God class/2+ files"];
  Gate2 -> Refactor [label="messy function,\nsingle file, no boundary crossed"];
  Gate2 -> Diagnose [label="crash/bug"];
  Gate2 -> Gate3 [label="new feature"];

  Gate3 -> TDD [label="trivial (<~20 lines) OR\nstandard/focused"];
  Gate3 -> Dispatch [label="independent"];
  Gate3 -> Dev [label="sequential/complex"];
  TDD -> Diagnose [label="stuck after 3 attempts"];
  TDD -> Planning [label="spec ambiguous"];

  Dispatch -> Gate4;
  Dev -> Gate4;
  TDD -> Gate4;

  Gate4 -> Verify -> RCR;
  RCR -> GH [label="PASS\n(recommendation)", style=dashed];
  RCR -> Receive [label="FAIL"];
  Receive -> Diagnose [label="blocking issue"];
  Receive -> Refactor [label="hygiene issue"];
  Receive -> RCR [label="re-review, capped at 2"];

  Diagnose -> Gate3 [label="bug resolved,\nresume feature"];
  Diagnose -> Gate4 [label="bug resolved,\nmerge-ready"];
}
```

## Rules

1. **Run Diagnostic Gates:** Evaluate the current task through the 3-Gate decision tree before any action.
2. **Skill Shadowing Check:** Before invoking a skill, verify that the local version in `skills/` is active. If the system is using a global version (e.g. from `~/.gemini/skills/`) that differs from the local one, warn the user.
3. **Invoke Immediately:** Once a route is identified, immediately activate and follow that skill.

**action: Notify Route**
Announce the identified route and confirm via `AskUserQuestion` — the tool supplies a free-text "Other" automatically (covers "apply intent manually, no skill"), so don't add a manual option for it:

1. ✅ **Recommended** — Routing to [`<skill-name>`]: [reason] based on [gate evaluation].
2. **Alternative** — Routing to [Alternative Skill] + the gate condition that would make it the better fit instead.

3. **No Skips:** Do NOT skip because a task seems \"simple\" or \"quick\". Every change deserves the appropriate rigor.

## Diagnostic Decision Tree

### Gate 0: Is the repo onboarded?

- **IF** no `AGENTS.md`/`CLAUDE.md` exists at the repo root:
  -> **ROUTE TO:** `codebase-init`. Note: this skill has `disable-model-invocation: true` — it must be explicitly invoked by the user, not auto-triggered. Surface it as a recommendation, not an automatic route.
- **IF** the repo is already onboarded:
  -> **Proceed to Gate 1.**

### Gate 1: Is the task fully defined?

- **IF** the user has a vague idea, OR if there is no documented specification:
  -> **ROUTE TO:** `brainstorming`
- **IF** there is an idea, but we need a concrete execution plan and architecting:
  -> **ROUTE TO:** `planning`
- **IF** the spec and plan exist:
  -> **Proceed to Gate 2.**

### Gate 2: Is this a systemic issue or localized?

- **IF** the code has circular dependencies, \"God classes\", or boundary violations, OR the change spans 2+ files / crosses a module boundary:
  -> **ROUTE TO:** `architecting`
- **IF** the issue is localized to a messy function within a single file and crosses no module boundary:
  -> **ROUTE TO:** `refactor`
- **IF** we are actively debugging a crash or traceback:
  -> **ROUTE TO:** `diagnose` (returns to **Gate 3** when bug is resolved)
- **IF** implementing a planned feature:
  -> **Proceed to Gate 3.**

**Tie-break (single file, but the fix logically touches a second file, e.g. an import or call-site update):** default to `refactor` only if the second file's change is a trivial one-line follow-on; escalate to `architecting` for anything broader. `refactor`'s own scope is single-file/single-function (see its description) — never route genuinely multi-file work to it.

### Gate 3: Execution Strategy

- **IF** the change is trivial (single file, roughly under 20 lines, no new public surface):
  -> **ROUTE TO:** `test-driven-development` directly, skip the subagent-dispatch question entirely — don't spend an `AskUserQuestion` round-trip deciding dispatch strategy for a one-line fix.
- **IF** tasks are completely independent (no shared state) AND wall-time is the primary constraint:
  -> **ROUTE TO:** `multi-agent-dispatch`
- **IF** tasks must be done sequentially OR if token-context usage must be minimized:
  -> **ROUTE TO:** `multi-agent-development`
- **IF** tasks are a mixed DAG:
  -> **ROUTE TO:** `multi-agent-development`, instructed to batch the independent tasks into one wave with gated reviews.
- **IF** writing standard code (single focused feature/fix):
  -> **ROUTE TO:** `test-driven-development` ⚠️
- **IF** `test-driven-development` fails to reach GREEN after 3 attempts:
  -> **ROUTE TO:** `diagnose` (implementation stuck, returns here after resolution) or `planning` (spec ambiguous) — see NEVER list.

⚠️ **Agentic Skill Warning:** `test-driven-development`, `request-code-review`, `multi-agent-development`, and `multi-agent-dispatch` execute autonomously (each dispatches multiple subagent calls). Output `This will start an autonomous session (~N calls). Proceed?` and wait for user confirmation. `multi-agent-development` is the most expensive of these (N tasks × up to 3 subagent phases × up to 2 retries) — never skip its confirmation gate.

### Gate 4: Quality & Delivery

After Gate 3's execution skill completes:

- **ALWAYS** -> **ROUTE TO:** `verification-before-completion` to gather execution evidence.
- **THEN** -> **ROUTE TO:** `request-code-review` (mandatory for non-trivial changes — it is the only security gate in the multi-agent-development flow).
  - **IF PASS** -> **ROUTE TO:** `github-automation` to open the PR. Note: `disable-model-invocation: true` — this is a deliberate human-invoked delivery gate, not an automatic hop.
  - **IF FAIL** -> **ROUTE TO:** `receive-code-review` to process feedback, which may loop back to `diagnose` (blocking issues) or `refactor` (hygiene), then re-review (capped at 2 cycles before escalating to the user).

## Diagnose Return Paths

The `diagnose` skill is a specialized gate that may be entered from multiple points in the lifecycle when a bug or critical issue is encountered. Once `diagnose` resolves the underlying issue, control must return to an execution gate to resume feature work or complete QA:

- **From Gate 2 (systemic bug):** After diagnosing the crash or bug, return to **Gate 3** to resume the planned feature implementation with the bug fix in place.
- **From Gate 3 (TDD stuck):** After diagnosing why `test-driven-development` failed to pass after 3 attempts, return to **Gate 3** and retry the implementation with the identified fix.
- **From Gate 4 (blocking code-review issue):** After diagnosing a blocking issue found during code review, return to **Gate 4** to re-run `request-code-review` with the fix applied. If the issue becomes a systemic refactor, escalate to `refactor` instead.

**Key principle:** `diagnose` is never a terminal state. Every diagnosed issue has a concrete next step that routes back into the main lifecycle. The graph now reflects these return edges explicitly.

## Mandatory Rules (NEVER List)

- **NEVER** route to `test-driven-development` if Gate 1 (spec/plan) is not fully GREEN.
- **NEVER** skip `architecting` for `refactor` if changes span 2+ files or cross module boundaries — `refactor`'s own scope is single-file/single-function.
- **NEVER** use `multi-agent-dispatch` if tasks have _any_ shared mutable state or logical dependencies.
- **NEVER** ignore the `diagnose` step when a bug is encountered during a feature implementation.
- **NEVER** let `test-driven-development` retry indefinitely — if it fails to pass after 3 attempts, escalate to `diagnose` (implementation stuck) or `planning` (spec ambiguous). This is now reflected directly in Gate 3 above (`references/lifecycle.md` Transition States is the longer-form rationale).
- **NEVER** treat Gate 4 (`request-code-review`) as optional after `multi-agent-development` — its quality gate does not check security; `request-code-review` is the only skill in the ecosystem that does.
- **NEVER** auto-invoke `codebase-init` or `github-automation` — both have `disable-model-invocation: true` by design. Recommend them; let the user trigger them.
- **NEVER** route a request to author/scaffold/validate a skill anywhere except `make-a-skill` — it is not reachable through Gates 0-4, it's a parallel entry point triggered directly by skill-authoring language (see Auxiliary Skills).
- **NEVER** dispatch subagents (Gate 3) for a change trivial enough to finish in a single inline edit — check the triviality condition before asking the user to confirm a dispatch strategy.

**next skills:**

- All skills in the `agent-dev` ecosystem are potential successors depending on the diagnostic route identified.

## Reference Library

- **Lifecycle:** [lifecycle.md](references/lifecycle.md) (Mermaid diagram and state transitions).

## Auxiliary Skills

- **Quality/Validation:** `verification-before-completion`, `request-code-review`, `receive-code-review` — see Gate 4.
- **Delivery:** `github-automation` — see Gate 4.
- **Repo Onboarding:** `codebase-init` — see Gate 0.
- **Skill Authoring:** `make-a-skill` — not part of the Gate 0-4 flow. Route here directly whenever the task is to scaffold, draft, or validate a _skill_ itself (e.g. "make a skill", "validate this skill"), bypassing Gates 0-4 entirely since it operates on the plugin's own skills/, not the target repo's code.

## Skip Disclaimer

If a skill is missing: `The \`<skill-name>\` skill is not installed. Proceeding without it.` then apply intent manually.
