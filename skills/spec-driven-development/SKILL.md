---
name: spec-driven-development
description: |
  Use this skill to implement features or fixes using Spec-Driven Development (SDD). Follow the mandatory workflow: clarify scope → create spec → create plan → implement with governance → validate acceptance. Do not skip steps or sub-skills. This skill ensures implementation serves the spec, maintaining alignment and traceability from requirements to code.
disable-model-invocation: true
---

# Spec-Driven Development

> **Autonomy: low** — all gates are mandatory; do not skip or substitute sub-skills.

## When to Use

Use this skill when the user says "build X", "add X", "implement X", "how should we build this", "let's design X", or any time implementation is on the horizon. Even when the user says "just build it", invoke this skill first and offer a Sketch spec (15 min) before writing any code.

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

This skill orchestrates two sub-skills (`create-specs`, `create-plan`) that each bundle their own validators (`validate_spec.py`, `discover.mjs`, `validate_plan.py`, `generate_plan.py`) — there is nothing to install separately. Confirm they are discoverable before you start:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/diagnose_dependencies.py
```

If the check reports a missing sub-skill, confirm the `agent-dev` plugin is enabled and run `/reload-plugins`, then re-run. Do not substitute manual work for missing tooling — invoke the sub-skill by name so its own validators run.

## Required Sub-Skills

Both sub-skills are **mandatory**. Do not skip them or substitute manual work.

| Sub-Skill      | Invoked at step             | Produces                                                       |
| -------------- | --------------------------- | -------------------------------------------------------------- |
| `create-specs` | Step 2 (Specification Gate) | Validated `spec-*.md` with REQ, interfaces, AC, VAL            |
| `create-plan`  | Step 3 (Planning Gate)      | Executable `plan-*.md` with phases, tasks, validation commands |

Invoke each sub-skill by name when you reach its gate. The sub-skill's own instructions define how to execute it — do not summarize or shortcut them.

## Workflow

> **Escape hatch**: For small tasks (one-file changes, clear bug fixes), you can use **Sketch maturity** (see above) — a lightweight one-page spec that skips the create-specs and create-plan sub-skills. If the user prefers to code without a spec, note the decision and proceed, but recommend using SDD even for "simple" tasks since it prevents rework. Do not skip this check silently.

### 0. Brainstorming Gate ← `brainstorming` required

**HARD-GATE: Do NOT proceed past this step until a design has been explored and the user has approved it via the `brainstorming` skill.**

If you arrived here without running `brainstorming`, invoke it now. This is not optional.

**If brainstorming is already complete:** Skip Step 1 (Clarify Scope — brainstorming already covered goals, constraints, and scope) and proceed directly to Step 2 (Specification Gate).

**Exception**: If the user explicitly provides a pre-approved spec or says "skip brainstorming," note the decision inline and proceed to Step 2.

### 1. Clarify Scope

**MANDATORY — READ ENTIRE FILE**: `references/scope-interview.md` to conduct the scope interview, choose maturity level (Sketch/Contract/Blueprint), and complete the post-interview checklist before proceeding.

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
- Verify all file paths and code symbols via `discover.mjs`
- Produce an executable `plan-*.md` with phases, tasks, and validation commands
- Run `validate_plan.py` to confirm the plan has no structural errors

**Gate**: Do not begin implementation until the plan passes `validate_plan.py` with 0 errors.
_Failure mode_: If validation fails, or if `discover.mjs` reports missing symbols, fix the plan tasks to match reality. If reality contradicts the spec, loop back to Step 2.

### 4. Implementation Governance

**Sub-skill required**: Invoke `test-driven-development` for each task in the plan. Write the test first (red), then implement (green), then refactor. Do not skip this even for "obvious" tasks — the spec's `AC-###` items map directly to test assertions.

See [Implementation Governance](references/implementation-governance.md) for Tracer Bullet and Incremental Loop procedures.

This phase covers:

- Firing the "Tracer Bullet" (first task execution and handling external dependencies)
- The Incremental Loop (executing the remaining tasks, each via `test-driven-development`)
- Handling validation failures and spec drift

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
[ ] Spec validated: validate_spec.py = 0 errors, self-check passed
[ ] Plan validated: validate_plan.py = 0 errors, all paths verified by discover.mjs
[ ] Tasks executed in dependency order (Depends on: respected)
[ ] Each task's Validate command run and Expected result confirmed before next task
[ ] Spec changes (if any) propagated: spec → plan → code (in that order, never reversed)
[ ] All AC-### from spec confirmed as observable in the final system
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
