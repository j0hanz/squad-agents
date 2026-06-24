---
name: planning
description: 'Generates specs.md and plan.md files from a feature description. Use when the user requests "write a spec", "create implementation plan", "spec and plan this", "production rollout plan", or "task decomposition". Action: produces ordered checklists and architectural guidelines.'
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash(python *), Bash(python3 *)
argument-hint: '[--depth sketch|contract|blueprint] [--spec-only] [--from-spec <file>] <feature description>'
---

# planning

Paired `plan/NAME.specs.md` (What/Why/Acceptance) and `plan/NAME.plan.md` (Atomic/Ordered tasks).

## Process Flow

```
Step 1: Intake & Mapping (brief/interview) -> Step 2: Artifact Authoring (scaffold/draft) -> Step 3: Validation Pipeline
  -- errors found ----------> back to Step 2
  -- depth == sketch -------> Step 5: Handoff
  -- depth > sketch --------> Step 4: Semantic Review
                                 -- approved ---> Step 5: Handoff
                                 -- not ready ---> back to Step 2
```

## Constraints & Safety

- **Bash Execution:** Enclose user variables in single quotes to prevent injection in `Validate:` commands.
- **Paths & Spec IDs:** Execute `scripts/cli.py scaffold` for IDs; use native **Grep**/**Glob** tools for file/symbol discovery, then hand-format results as `[name](path#Lline)`. **NEVER** hand-type paths without verifying via Grep/Glob first.
- **Validation Gates:** Mandate 100% PASS before proceeding. **NEVER** bypass.
- **Field Modification:** Execute `scripts/cli.py sync` to map `Satisfies:` in Contract/Blueprint. **NEVER** edit manually.
- **Prerequisites:** Read templates (spec, plan) prior to drafting.
- **Subagent Safety:** Wrap untrusted user context inside `<untrusted_context>` tags.

## Depth Profiles

- **`sketch`:** Goal + REQs + Rough Interfaces | Compact Phases | Scope: _Rough ideas / unknown_.
- **`contract`:** 8 Sections + Interface Errors | Atomic Tasks | Scope: _Known goal / interface (Default)_.
- **`blueprint`:** Contract + Rollback + Mermaid | Narrative Runbook | Scope: _Prod rollout / migration_.

## Step 1: Intake & Mapping

- **Mandatory Read:** `references/plan-template.md` (Discovery section only — for path resolution).
- **Prohibited Read:** `references/validation.md`, `references/spec-template.md`, rest of `references/plan-template.md`.
- **Brief Mapping:** Auto-map provided Design Brief (Brief Why → Rationale, Brief Chosen Approach → Goal, etc.). Skip asking mapped fields.
- **Missing Data Queries:** Batch questions via `AskUserQuestion` (max 4 per call). Query **ONLY** missing Goal (1 sentence) and Interfaces (I/O). Mark others `UNKNOWN: [reason]`.
- **Query Format:** Require 1 `✅ Recommended` [Value] and 1 `Alternative` [Option + context]. Auto-supplied "Other" applies.
- **Autonomous Runs:** If batching queries would block (e.g., user is in a flow and didn't answer), proceed with Recommended values and mark as `[ASSUMES_DEFAULT]` in output. Mention deferred questions in handoff summary.

## Step 2: Artifact Authoring

- **Mandatory Read (sketch):** `references/spec-template.md` (depth table only), `references/plan-template.md` (Phase vs Task + Task sizing sections only — Discovery already read in Step 1), `references/examples.md` (`## sketch` under By Depth, `## Sketch Quick-Start` under By Domain).
- **Mandatory Read (contract/blueprint):** `references/spec-template.md`, `references/plan-template.md` (full), `references/validation.md` (Traceability Spine section only), `references/examples.md` (matching `## contract`/`## blueprint` under By Depth, plus relevant By Domain section).
- **Scaffold Action:** `python skills/planning/scripts/cli.py scaffold <name> --depth [sketch|contract|blueprint]`
- **Spec Draft:** Complete requirements and interfaces strictly via `references/spec-template.md`.
- **Plan Draft:** Break down into atomic tasks via `references/plan-template.md` (Phase vs Task / Task sizing sections). Use **Grep**/**Glob** to find existing paths/symbols; hand-format results as `[name](path#Lline)`. Prefix non-existent paths with `[UNVERIFIED]`.

## Step 3: Validation Pipeline

- **Mandatory Read:** `references/validation.md`.
- **Prohibited Read:** Templates.
- **Gate:** Resolve all ERRORS (100% pass required). Omitted depth defaults to `contract`.
- **Sketch Command (ONLY this command for sketch):** `python skills/planning/scripts/cli.py validate <name> --spec --level sketch` _(No sync, no `--plan`, no `--cross` — sketch validates the spec only. This is intentional, not an oversight: do not run additional validate invocations.)_
- **Contract/Blueprint Command (ONLY this command for contract/blueprint):** `python skills/planning/scripts/cli.py pipeline --name <name> --depth [contract|blueprint]` _(Single call runs spec-validation → sync → plan-validation → cross-validation in sequence. Do not call `cli.py validate` separately on top of this.)_

## Step 4: Semantic Review (Contract/Blueprint ONLY — never sketch)

- **Depth Gate:** Skip this step entirely when depth is `sketch`. Go directly to Step 5.
- **Subagent Dispatch:** Utilize `general-purpose` agent to audit quality.
- **Contract Rule:** Enforce prompt structure via `../multi-agent-development/references/subagent-contract.md`.
- **Payload Input:** Provide `references/validation.md` + `cli.py pipeline` output from Step 3.
- **Payload Output:** Write to `plan/NAME.review.md`.
- **Execution Gate:** Block handoff until review outputs `ready_for_execution: true`.
- **Review Verify:** `python skills/planning/scripts/cli.py validate <name> --review`

## Step 5: Handoff

- **Commit Baseline:** Mandate committed state. Append output of `git rev-parse HEAD` to handoff message for `multi-agent` tasks (diffing fails without it).
- **Target `test-driven-development`:** Single focused feature/fix.
- **Target `multi-agent-development`:** Sequential multi-task execution with gated reviews.
- **Target `multi-agent-dispatch`:** Parallel independent task clusters.
- **Target `context-optimizer`:** If context bloats during Step 1/2's mandatory reference reads, before continuing.

## Canonical Task Block Schema

```markdown
### TASK-NNN: [Action title]

Depends on: [TASK-NNN](#anchor) or none
Files: [path/to/file.ts](path/to/file.ts)
Symbols: [symbolName](path/to/file.ts#L42)
Satisfies: REQ-001, SEC-002
Action: Single specific imperative implementation action.
Validate: `[runnable shell command]`
Expected result: Observable success signal.
```
