---
name: spec-driven-development
description: "Use when requirements are explored and it's time to formalize: spec then plan then code. Trigger on 'write the spec', 'formalize this', 'spec-driven', 'spec first', 'ready to build'. NOT for initial idea exploration — use brainstorming for that."
disable-model-invocation: false
---

# Spec-Driven Development

> **Autonomy: low** — all gates are mandatory; do not skip or substitute sub-skills.

## NEVER

- **NEVER retrofit a spec from existing code** — a spec that merely describes what the code already does is not a contract; it protects nothing and will drift instantly as the code changes
- **NEVER patch code and backfill the spec afterward** — when implementation conflicts with the spec, stop, resolve at the spec level, then resume; reversing this order makes the spec meaningless
- **NEVER skip `validate_spec.py`** because the spec "looks right" — structural errors (missing REQ→AC traceability, unresolvable VAL commands) only surface when the validator runs, and they invalidate the planning step
- **NEVER skip sub-skills for Contract or Blueprint maturity tasks** — the Trivial Fast-Path (Sketch) is limited to unambiguous one-file changes with no interface impact; "time pressure" and "manager says skip docs" are not Sketch qualifiers

## Context Disambiguation (Run Before All Steps)

Before applying the SDD workflow, establish which codebase is being discussed:

- **User describes a feature for the current working directory** → proceed normally.
- **User describes a feature for a different project or codebase** → note this inline: _"Applying SDD to the described feature. I will not explore the current working directory."_ Then follow the workflow for the described system without reading the local filesystem.
- **Ambiguous** → ask one focused question: _"Is this feature for the codebase I'm currently in, or for a different project?"_

Never explore the local filesystem to determine whether the user's described feature exists in the current repo. The SDD workflow applies to the project the user is describing, regardless of what is checked out locally.

---

## When to Use

Use this skill when the user says "build X", "add X", "implement X", "how should we build this", "let's design X", or any time implementation is on the horizon. Even when the user says "just build it", invoke this skill first and offer a Sketch spec (15 min) before writing any code.

## Response Length Calibration

Match response length to the stage and maturity level. Do not over-explain.

| Stage | Guideline |
|---|---|
| **Trivial fast-path (Sketch)** | 1 page max. Goal, ACs, validation. Nothing else. |
| **Scope interview (Contract/Blueprint)** | Answer the 5 interview questions in < 400 words. Do NOT pre-draft REQ/AC/VAL items here — that is `create-specs`' job. |
| **Spec recovery (mid-impl change)** | Numbered list of steps. ≤ 15 items. Include the git command and the validation command. |
| **Blueprint / decomposition** | Full detail appropriate. Focus on open questions and the decomposition table. |

**Avoid these patterns in every response:**
- Pre-drafting spec content (REQ/AC/VAL) before `create-specs` runs. It will be replaced — do not produce it during the scope interview.
- Pre-drafting plan phases before `create-plan` runs. Same reason.
- Repeating the full 5-step workflow at the bottom of every response. State where the conversation is and what the next action is.

---

## Philosophy

**Core principle**: A spec defines the contract. Implementation serves the spec, not the other way around.

Writing code before the spec is done doesn't save time — it borrows time at high interest. Early implementation commits you to design decisions before you understand the problem. The spec is how you understand the problem. Without a spec, you're optimizing a guess.

**Good SDD produces three artifacts in order:**

1. **Spec** — what must be built, why, and how it connects to other systems (`create-specs`)
2. **Plan** — atomic ordered tasks derived from the spec, with verified paths and validation commands (`create-plan`)
3. **Implementation** — code that satisfies the plan and is verified against the spec's acceptance criteria

Specs use three notation types — `REQ` (requirements), `AC` (acceptance criteria), and `VAL` (validation commands) — defined and scaffolded by the `create-specs` sub-skill.

**The spec is the single source of truth.** When implementation decisions conflict with the spec, stop and resolve at the spec level. When requirements change, update the spec first — then the plan — then the code. Never patch code and backfill the spec.

For common mistakes and how to avoid them: [Anti-Patterns](references/anti-patterns.md).

## When to Use This Skill vs. Other Planning Approaches

Different skills for different situations:

| Situation | Skill | Output | Time |
|-----------|-------|--------|------|
| **Implementing a single feature or bug fix** (small-to-medium scope) | spec-driven-development (you are here) | spec-*.md + plan-*.md + validated code | 1–3 hours |
| **Planning a large initiative, roadmap, or multi-sprint effort** | `create-plan` | high-level plan with phases and milestones | 2–4 hours |
| **Designing system architecture, component interactions, API contracts** | `architecture` | architecture.md, ADRs, diagrams | 2–6 hours |
| **Exploring unknown problem space or evaluating technologies** | `research-engineer` | research findings, recommendations, proof-of-concepts | varies |

**Typical workflow** (large projects):
1. Research → Understand the landscape (research-engineer)
2. Architecture → Design system and interfaces (architecture)
3. Multiple SDD cycles → Implement features one-by-one (spec-driven-development)
4. Integration → Test across features

## Prerequisites

This skill orchestrates two sub-skills (`create-specs`, `create-plan`) that each bundle their own validators (`validate_spec.py`, `validate_plan.py`, `generate_plan.py`) — there is nothing to install separately.

If a sub-skill fails to invoke, run `python <skill-dir>/scripts/diagnose_dependencies.py` to check availability. If it reports a missing sub-skill, confirm the `agent-dev` plugin is enabled and run `/reload-plugins`. Do not substitute manual work for missing tooling — invoke the sub-skill by name so its own validators run.

## Required Sub-Skills

Both sub-skills are **mandatory**. Do not skip them or substitute manual work.

| Sub-Skill      | Invoked at step             | Produces                                                       |
| -------------- | --------------------------- | -------------------------------------------------------------- |
| `create-specs` | Step 2 (Specification Gate) | Validated `spec-*.md` with REQ, interfaces, AC, VAL            |
| `create-plan`  | Step 3 (Planning Gate)      | Executable `plan-*.md` with phases, tasks, validation commands |

Invoke each sub-skill by name when you reach its gate. The sub-skill's own instructions define how to execute it — do not summarize or shortcut them.

## Workflow

### Pre-Workflow Check: Trivial Fast-Path

Before running the full workflow, ask: **Is this unambiguously a one-file change with no behavior observable by external callers?**

Examples that qualify: changing a constant, fixing a typo in an error message, updating a config default, renaming a local variable, adjusting a log level.

Examples that do NOT qualify: any change that touches an API endpoint, database schema, UI component, test file, or more than one file.

**If YES** → Use Sketch maturity directly:
1. Write the one-page spec using [sketch-template.md](references/sketch-template.md) (5 min).
2. Confirm with the user.
3. Proceed to Implementation Governance — no brainstorming, no `create-specs`, no `create-plan` required.

**If NO or UNSURE** → Continue with the full workflow starting at Step 0 (Brainstorming Gate).

Do not default to "NO" out of caution. If the change is genuinely one-file with no interface impact, use the fast-path — forcing a full SDD cycle on a constant change is process overhead, not rigor.

### 0. Brainstorming Gate

Before proceeding, ask: has the design space already been explored for this request?

- **New request, no prior design discussion** → Invoke `brainstorming` now. Do not proceed to scope clarification until the brainstorming skill has finished.
- **User provided a detailed description with explicit decisions already made** → Treat brainstorming as complete. Note it inline: "Treating description as brainstorming complete." Proceed to Step 1.
- **User says "skip brainstorming"** → See [Brainstorming Skip Handling](#brainstorming-skip-handling) below.

When in doubt, run a short brainstorm (5 min) rather than skipping — it often surfaces constraints that change the scope entirely.

**If the `brainstorming` sub-skill is unavailable in this environment**, run an inline proxy instead. Keep it to ≤ 200 words covering exactly these five questions:
1. What is the underlying problem this feature solves (not just the feature itself)?
2. What are 2–3 different ways to implement it and their key tradeoff?
3. What assumptions in the request might be wrong?
4. What hidden dependencies might exist?
5. What would make the scope larger than it appears?

Label the section "Brainstorm Output (inline proxy)" and proceed to Step 1 after answering all five. Do not exceed 200 words — brevity forces prioritization.

### Brainstorming Skip Handling

When the user says "skip brainstorming" or "I've already done the brainstorming":

1. Check: has the user provided a description with explicit design decisions already made (approach chosen, tradeoffs resolved, constraints named)?
   - **If YES** → note inline: "Treating provided description as brainstorming complete." Proceed to Step 1.
   - **If NO** → warn once: "Skipping brainstorming on an underspecified request increases the chance that the scope interview surfaces a constraint that changes the approach. I'll skip it — but if the scope interview reveals a fundamental assumption gap, we may need to revisit." Then proceed to Step 1.
2. Do not argue or repeat the warning. One note, then move forward.

### 1. Clarify Scope

**MANDATORY — READ ENTIRE FILE**: `references/scope-interview.md` to conduct the scope interview, choose maturity level (Sketch/Contract/Blueprint), and complete the post-interview checklist before proceeding.

Also check: does this feature depend on an interface owned by another team (API, schema, infrastructure)?

If **yes** — identify the dependency owner before proceeding to Step 2. Find their spec if one exists. An unresolved external interface cannot be validated and will block spec completion. See [Multi-Team Specs](references/multi-team-specs.md).

### 2. Specification Gate ← `create-specs` required

**How to invoke the `create-specs` skill:**

- **In Claude Code**: Use the `Skill` tool with `create-specs` as the skill name
- **In Claude.ai**: Request spec creation; the skill may trigger automatically
- **In Copilot CLI**: Run `copilot -s create-specs`

If the `create-specs` skill is not available in your environment:
1. Contact your workspace admin to ensure it's installed
2. As a fallback, use the [Sketch Spec Template](references/sketch-template.md) and follow it directly (note: automated validation will not be available)

**Do not write the spec manually** — the create-specs skill provides traceability and validation.

The `create-specs` skill will:

- Gather requirements, constraints, interfaces, and acceptance criteria via the Spec Interview
- Scaffold and populate the 8-section spec template
- Run `validate_spec.py` to check structural integrity and traceability
- Produce a `spec-*.md` file ready for planning

**Gate**: Do not proceed to Step 3 until `validate_spec.py` returns 0 errors and the `create-specs` self-check passes.
_Failure mode_: If `validate_spec.py` fails, analyze the output, run the `create-specs` refinement loop again to fix the structural errors, and re-verify. Do not manually force it past the gate.

### 3. Planning Gate ← `create-plan` required

**How to invoke the `create-plan` skill:**

- **In Claude Code**: Use the `Skill` tool with `create-plan` as the skill name, passing the spec file
- **In Claude.ai**: Request plan creation from the spec; the skill may trigger automatically
- **In Copilot CLI**: Run `copilot -s create-plan -- <spec-file>`

If the `create-plan` skill is not available:
1. Contact your workspace admin to ensure it's installed
2. As a fallback, manually create the plan by running `generate_plan.py <spec.md>` directly (note: automated validation will not be available)

**Pass the validated spec file as input.**

The `create-plan` skill will:

- Run `generate_plan.py <spec.md>` to scaffold tasks from REQ → Task mappings
- Verify all file paths and code symbols via `discover.py`
- Produce an executable `plan-*.md` with phases, tasks, and validation commands
- Run `validate_plan.py` to confirm the plan has no structural errors

**Gate**: Do not begin implementation until the plan passes `validate_plan.py` with 0 errors.
_Failure mode_: If validation fails, or if `discover.py` reports missing symbols, fix the plan tasks to match reality. If reality contradicts the spec, loop back to Step 2.

### 4. Implementation Governance

**Sub-skill required**: Invoke `test-driven-development` for each task in the plan. Write the test first (red), then implement (green), then refactor. Do not skip this even for "obvious" tasks — the spec's `AC-###` items map directly to test assertions.

See [Implementation Governance](references/implementation-governance.md) for Tracer Bullet and Incremental Loop procedures.

This phase covers:

- Firing the "Tracer Bullet" (first task execution and handling external dependencies)
- The Incremental Loop (executing the remaining tasks, each via `test-driven-development`)
- Handling validation failures and spec drift

**If implementation reveals a scope gap** — apply this sequence immediately:

1. Stop coding
2. `git commit -m "WIP: partial implementation of [spec-name]"` (checkpoint)
3. Classify: **minor** (1–2 new ACs, no architecture change) or **major** (3+ ACs, or new DB table / API endpoint / external service)
4. Update `spec-*.md` with new REQ/AC/VAL items
5. Run `python validate_spec.py spec-*.md` — hard gate: 0 errors before resuming
6. If **major**: `python generate_plan.py spec-*.md > plan-*.md && python validate_plan.py plan-*.md`
7. Evaluate: are previously completed tasks still valid? If yes, resume from first new task. If not, `git reset --hard HEAD~1` and restart from the new plan.

Full recovery reference: [Spec Recovery](references/spec-recovery.md)

### 5. Acceptance Validation

After all tasks complete, verify the full spec is satisfied:

- [ ] Run all `VAL-###` commands from the spec's Validation Steps section
- [ ] Confirm each `AC-###` from the spec is observable in the running system
- [ ] If any AC fails: trace back to the spec requirement — determine whether implementation is wrong or the spec was incomplete, and resolve at the spec level

Ask: _"Does the system now do what the spec says it must do?"_ If yes: done. If no: update spec → update plan → fix implementation.

**REQUIRED NEXT SKILL:** After all AC pass, invoke `verification-before-completion` before reporting the feature complete. Do not skip this.

## Checklist Per Cycle

```
[ ] Scope clarified: goal, in/out-of-scope, constraints, maturity level
[ ] External dependencies identified (multi-team interfaces resolved before spec is finalized)
[ ] Spec validated: validate_spec.py = 0 errors, self-check passed
[ ] Plan validated: validate_plan.py = 0 errors, all paths verified by discover.py
[ ] Tasks executed in dependency order (Depends on: respected)
[ ] Each task's Validate command run and Expected result confirmed before next task
[ ] Spec changes (if any) propagated: spec → plan → code (in that order, never reversed)
[ ] All AC-### from spec confirmed as observable in the final system
[ ] verification-before-completion invoked before declaring the feature done
```

## Refining the Spec After Validation

Once the spec is validated, what if new information arrives or stakeholders request changes?

### Minor Clarification (Wording, Examples)
Update the spec directly (no validation needed for cosmetic changes). Keep implementation on track.

### New Requirement (Additional AC/REQ)
1. Add new REQ/AC/VAL to the spec alongside existing ones
2. Run `validate_spec.py` again
3. If validation passes: Update plan (add new tasks for new AC)
4. Continue implementation

### Fundamental Change (Requirement Changes)
1. Update the affected REQ items in the spec
2. Run `validate_spec.py` again
3. Evaluate: Does this change any AC/VAL items? If yes: update, revalidate, update plan
4. Continue implementation

### Major Change (Spec is Fundamentally Different)
See [Spec Recovery](references/spec-recovery.md) for how to handle major changes mid-implementation.

---

**Golden Rule**: Never implement against an unvalidated change. If the spec changes, validate it before resuming code.

## Starting with Existing Code

If you have partial implementations or code from another team, see [Starting with Existing Code](references/starting-with-existing-code.md).

The key principle: **Do NOT retrofit a spec from existing code.** This creates a redundant spec that's not a real contract. Instead, create a spec for _remaining work_ or start fresh if the code is fundamentally wrong.

## Multi-Team Coordination

If your feature depends on other teams' APIs, schemas, or infrastructure, see [Multi-Team Specs](references/multi-team-specs.md).

Key guidance:
- Find the owning team's spec before finalizing yours
- Model dependencies explicitly in the plan
- Coordinate timelines and breaking changes

## References

- [Anti-Patterns](references/anti-patterns.md) — common mistakes and how to avoid them
- [Implementation Governance](references/implementation-governance.md) — Tracer Bullet, Incremental Loop, drift resolution
- [Example Cycle](references/example-cycle.md) — complete walkthrough of a minimal SDD cycle
