---
name: planning
description: "Full planning pipeline: spec then plan, cross-aligned. Trigger on 'write a spec', 'create a plan', 'what should we build', 'define requirements', 'write specs', 'plan this feature', 'implementation plan', 'spec and plan', 'planning'. Produces two paired artifacts per invocation: NAME.specs.md and NAME.plan.md. Replaces create-specs and create-plan."
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash(python *) Bash(python3 *)
argument-hint: |
  [--depth sketch|contract|blueprint (default: contract)]
  [--spec-only] [--from-spec <file>]
  [--quick] [--assume-paths] [--domain api|cli]
  Examples:
  - /planning "Add JWT authentication"
  - /planning --depth blueprint "High-throughput event pipeline"
  - /planning --spec-only "Define the API contract"
  - /planning --from-spec plan/auth-jwt.specs.md
---

# Planning

| File                 | What it says                                                     |
| -------------------- | ---------------------------------------------------------------- |
| `plan/NAME.specs.md` | What must be built, why, interfaces, acceptance criteria         |
| `plan/NAME.plan.md`  | Atomic ordered tasks with verified paths and validation commands |

Every plan task carries `Satisfies: REQ-001, SEC-002` linking it to spec IDs. `validate.py --cross` enforces full coverage: no uncovered requirements, no orphan tasks.

## Depth Dial

| Depth                  | Spec rigor                                        | Plan format       | Use when                   |
| ---------------------- | ------------------------------------------------- | ----------------- | -------------------------- |
| `sketch`               | Goal + top REQs + rough interfaces                | Compact phases    | Early idea, exploratory    |
| `contract` _(default)_ | All 8 sections, interface errors mandatory        | Atomic tasks      | Feature-ready, build-ready |
| `blueprint`            | Contract + rollback, error cases, Mermaid diagram | Narrative runbook | Production-critical        |

## Modifiers

- `--spec-only` — write only `NAME.specs.md`; stop before planning
- `--from-spec <file>` — skip spec authoring, generate plan from an existing spec file (see Step 2 for error handling)
- `--quick` — _(agent-level flag, not passed to any script)_ skip `discover.py`; assume standard project structure and document intended paths using `[UNVERIFIED]` prefix
- `--assume-paths` — _(agent-level flag, not passed to any script)_ multi-repo: document all path assumptions with `[UNVERIFIED]` prefix instead of running `discover.py`
- `--domain api|cli` — inject domain-specific requirement + interface snippets

## Step-by-Step Execution

**skill-dir:** directory containing this `SKILL.md` file (use the absolute path of this file's parent directory if `$CLAUDE_PLUGIN_ROOT` is not set). All `python <skill-dir>/scripts/...` commands resolve against it.

### Step 1 — Intake

**If a Design Brief from the `brainstorming` skill is present in context**, map its fields directly and skip the corresponding interview questions:

- Brief **Scope** → planning Scope
- Brief **Constraints** → planning Constraints
- Brief **Interface** → planning Interface
- Brief **Acceptance criteria** → planning Success criteria
- Brief **Chosen approach / Why** → planning Goal (supplement with the approach rationale)

Only ask interview questions for fields that are still missing after mapping.

**Otherwise, trigger spec interview if the user's request does NOT explicitly state all five of:**
goal · scope · constraints · interface · success criteria

Exception: if all five are inferable from the request text (e.g., a fully specified API contract), proceed directly to scaffold and note what was inferred.

If triggered, ask in order, one at a time:

1. **Goal:** "What outcome or capability are you enabling? One sentence."
2. **Scope:** "Which system or component does this touch? What's explicitly out of scope?"
3. **Constraints:** "Any limitations: timeline, existing systems, compliance, tech stack?"
4. **Interface:** "How will users or systems interact with this? What input, what output?"
5. **Success:** "How will you know it's done? What does the user see to verify it works?"

Document all answers inline. Mark unknowns `UNKNOWN: [what and why]` — don't guess.

### Step 2 — Output Plan Intent (JSON)

**If `--from-spec <file>` was passed:**

- Verify the file exists.
- If missing: output `"Spec file not found: <path>. Create it first or omit --from-spec."` and stop.

**Otherwise (normal flow):**
Based on the intake, formulate the entire plan in `plan/NAME.plan.json`. This must include the structured array of tasks, dependencies, and requirements mapped for the feature.

**Required JSON output format (`plan/NAME.plan.json`):**
Write this structure to `plan/NAME.plan.json` to make inter-skill data extraction deterministic:

```json
{
  "name": "NAME",
  "tasks": [
    {
      "id": "TASK-001",
      "title": "Action title",
      "depends_on": ["TASK-000"],
      "files": ["path/to/file.ts"],
      "symbols": ["functionName"],
      "satisfies": ["REQ-001", "SEC-002"],
      "action": "Single specific imperative implementation action.",
      "validate": "npm test -- path/to/file.test.ts",
      "expected_result": "Observable success signal"
    }
  ]
}
```

### Step 3 — Author Markdown Artifacts

After outputting the JSON intent, manually author the `plan/NAME.specs.md` and `plan/NAME.plan.md` artifacts.

1. Run `python <skill-dir>/scripts/scaffold.py "NAME" --depth contract` to generate skeletons.
2. Fill `NAME.specs.md` with the requirements.
3. Fill `NAME.plan.md` tasks corresponding to the JSON.
   _Note: Use `discover.py` if needed to find paths._

### Step 4 — Run Validation Pipeline

Instead of running individual validation and sync scripts manually, use the consolidated pipeline tool to validate your artifacts:

```bash
python <skill-dir>/scripts/execute_plan_pipeline.py --input plan/NAME.plan.json
```

**GATE:** Resolve any ERRORS output by the pipeline. Do not proceed until the pipeline returns a success state.

### Step 5 — Reviewer (REQUIRED GATE)

Spawn `agents/reviewer.md` with this exact prompt:

```
spec_path: plan/<name>.specs.md
plan_path: plan/<name>.plan.md
```

It scores spec quality, plan quality, and traceability together and writes findings to `plan/NAME.review.md` with a `ready_for_execution: true|false` field.

This step is REQUIRED — handoff is incomplete without a review file. Verify:

```bash
python <skill-dir>/scripts/validate.py "NAME" --review
```

`--review` mode checks that `plan/NAME.review.md` exists with `ready_for_execution: true`. Only then proceed to handoff.

### Step 6 — Handoff

Export `plan/NAME.specs.md` + `plan/NAME.plan.md` + `plan/NAME.plan.json`. The spec says _what_ and _why_; the plan says _how_ and _in what order_. Pass the plan to `test-driven-development` for execution.

## Canonical Task Block

```
### TASK-001: [Action title]

Depends on: [TASK-000](#task-000-title) or none
Files: [path/to/file.ts](path/to/file.ts)
Symbols: [functionName](path/to/file.ts#L42)
Satisfies: REQ-001, SEC-002
Action: Single specific imperative implementation action.
Validate: `npm test -- path/to/file.test.ts`
Expected result: Observable success signal (e.g., "All 8 tests pass").
```

<constitutional_constraints>
<rule id="1" severity="CRITICAL">You MUST NOT execute bash commands containing user-provided variables without properly wrapping them in quotes.</rule>
<rule id="2" severity="HIGH">You MUST NOT hand-type a spec ID — run `scaffold.py` to generate them. If scaffold already ran and you need a new ID, re-run it with the same NAME.</rule>
<rule id="3" severity="HIGH">You MUST NOT hand-type a file path — use `discover.py` output. For new files, document intended path with `[UNVERIFIED]` prefix.</rule>
<rule id="4" severity="HIGH">You MUST NOT edit `Satisfies:` manually — re-run `sync.py` if requirements change.</rule>
<rule id="5" severity="CRITICAL">You MUST NOT skip validation. A plan that passes individual checks can still have uncovered requirements.</rule>
<rule id="6" severity="CRITICAL">You MUST NOT hand the plan to an executor before all validators pass.</rule>
</constitutional_constraints>

## Reference Docs

| Need                            | Reference                                                      |
| ------------------------------- | -------------------------------------------------------------- |
| Spec sections and templates     | [references/spec-template.md](references/spec-template.md)     |
| Domain-specific worked examples | [references/domain-examples.md](references/domain-examples.md) |
| Plan template and task sizing   | [references/plan-template.md](references/plan-template.md)     |
| Discovery guide                 | [references/discovery.md](references/discovery.md)             |
| Validation checklist            | [references/validation.md](references/validation.md)           |
| Traceability spine details      | [references/traceability.md](references/traceability.md)       |
| Output examples by depth        | [references/output-examples.md](references/output-examples.md) |
