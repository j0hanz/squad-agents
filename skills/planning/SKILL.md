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

Produces two paired, cross-linked artifacts per invocation:

| File                 | What it says                                                     |
| -------------------- | ---------------------------------------------------------------- |
| `plan/NAME.specs.md` | What must be built, why, interfaces, acceptance criteria         |
| `plan/NAME.plan.md`  | Atomic ordered tasks with verified paths and validation commands |

Every plan task carries a `Satisfies: REQ-001, SEC-002` field that links it back to spec IDs. `validate.py --cross` enforces a coverage matrix: no uncovered requirements, no orphan tasks.

## Depth Dial

| Depth                  | Spec rigor                                        | Plan format       | Use when                   |
| ---------------------- | ------------------------------------------------- | ----------------- | -------------------------- |
| `sketch`               | Goal + top REQs + rough interfaces                | Compact phases    | Early idea, exploratory    |
| `contract` _(default)_ | All 8 sections, interface errors mandatory        | Atomic tasks      | Feature-ready, build-ready |
| `blueprint`            | Contract + rollback, error cases, Mermaid diagram | Narrative runbook | Production-critical        |

## Modifiers

- `--spec-only` — write only `NAME.specs.md`; stop before planning
- `--from-spec <file>` — skip spec authoring, generate plan from an existing spec file (see Step 2 for error handling)
- `--quick` — skip file discovery, assume standard structure
- `--assume-paths` — multi-repo: document path assumptions instead of discovering
- `--domain api|cli` — inject domain-specific requirement + interface snippets

## Step-by-Step Execution

### Step 1 — Intake

Confirm: purpose (what are we adding/fixing?), scope (which component?), constraints (hard limits?).

**Trigger spec interview if the user's request does NOT explicitly state all five of:**
goal · scope · constraints · interface · success criteria

Exception: if all five are inferable from the request text (e.g., a fully specified API contract), proceed directly to scaffold and note what was inferred.

If triggered, ask IN ORDER (one at a time, wait for answer before next):

1. **Goal:** "What outcome or capability are you enabling? One sentence."
2. **Scope:** "Which system or component does this touch? What's explicitly out of scope?"
3. **Constraints:** "Any limitations: timeline, existing systems, compliance, tech stack?"
4. **Interface:** "How will users or systems interact with this? What input, what output?"
5. **Success:** "How will you know it's done? What does the user see to verify it works?"

Document all answers inline. Mark unknowns `UNKNOWN: [what and why]` — don't guess.

**Script path:** All `python <skill-dir>/scripts/...` commands resolve `<skill-dir>` to the directory containing this `SKILL.md` file. If `${CLAUDE_PLUGIN_ROOT}` is set in the environment, use that. Otherwise, derive the path from the location of this file.

### Step 2 — Scaffold

**If `--from-spec <file>` was passed:**

- Check the file exists before continuing.
- If missing: output `"Spec file not found: <path>. Create it first or omit --from-spec."` and stop.
- If exists: skip Steps 2–3 and go directly to Step 4 (Sync).

```bash
python <skill-dir>/scripts/scaffold.py NAME --depth contract [--domain api|cli] [--goal "..."]
```

Creates `plan/NAME.specs.md` and `plan/NAME.plan.md` with matching ID skeletons.

### Step 3 — Author spec

Fill the scaffolded `NAME.specs.md`. Use `REQ-###`/`SEC-###`/`PERF-###`/`CON-###`/`AC-###`/`VAL-###` labels exactly as placed by scaffold. Never invent IDs by hand.

**GATE:** Run `validate.py --spec` — resolve all ERRORS before continuing.

```bash
python <skill-dir>/scripts/validate.py NAME --spec --level <depth>
```

**Self-check:** Use the checklist in `references/spec-template.md` to catch what the validator cannot: unmeasured adjectives, compound REQs, and missing interface error cases. Fix all before proceeding.

### Step 4 — Sync plan stubs

```bash
python <skill-dir>/scripts/sync.py plan/NAME.specs.md
```

Populates `NAME.plan.md` with one task stub per requirement, `Satisfies:` pre-filled. Idempotent — safe to re-run after spec edits.

### Step 5 — Discover paths & symbols

For each task that touches real files, run:

```bash
python <skill-dir>/scripts/discover.py --files "src/**/*.ts" --names "functionName"
```

Paste the markdown link output directly into the task `Files:` and `Symbols:` fields.

**For new features (greenfield, no existing files):** If `discover.py` returns "No matches", document intended paths using conventional project structure (e.g., `src/routes/auth.ts`). Mark with `[UNVERIFIED]` prefix in the task. This is normal for new features — the anti-pattern applies to modifications of existing code only.

### Step 6 — Author plan tasks

Fill in each stub's `Action`, `Validate`, and `Expected result`. Rules:

- One task = one observable outcome (no "and" joining two outcomes)
- `Validate:` must be a verbatim shell command in backticks
- `Files:` and `Symbols:` must be markdown links `[name](path#L42)`
- Do NOT edit the `Satisfies:` field — it was set by sync.py

See `references/plan-template.md` for the canonical task block format.

**GATE:** Run `validate.py --plan` — resolve all ERRORS.

```bash
python <skill-dir>/scripts/validate.py NAME --plan
```

### Step 7 — Cross-validate

```bash
python <skill-dir>/scripts/validate.py NAME --cross
```

Checks: every spec requirement covered by ≥1 task; every `Satisfies:` ID exists in spec; every AC mapped. Fix all ERRORS — do not proceed with an uncovered requirement or orphan task.

### Step 8 — Reviewer (REQUIRED GATE)

Spawn `agents/reviewer.md` with this exact prompt:

```
spec_path: plan/<name>.specs.md
plan_path: plan/<name>.plan.md
```

It scores spec quality, plan quality, and traceability together and writes findings to `plan/NAME.review.md` with a `ready_for_execution: true|false` field.

This step is REQUIRED — handoff is incomplete without a review file. Verify:

```bash
python <skill-dir>/scripts/validate.py NAME --review
```

`--review` mode checks that `plan/NAME.review.md` exists with `ready_for_execution: true`. Only then proceed to handoff.

### Step 9 — Handoff

Export `plan/NAME.specs.md` + `plan/NAME.plan.md`. The spec says _what_ and _why_; the plan says _how_ and _in what order_. Pass the plan to `test-driven-development` for execution.

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

**`Satisfies:` is the spine.** It links this task back to spec IDs. Never remove or edit it after `sync.py` sets it.

## Anti-Patterns

- **Never hand-type a spec ID** — run `scaffold.py` to generate them. If scaffold already ran and you need a new ID, re-run it with the same NAME (it is idempotent).
- **Never hand-type a file path** — use `discover.py` output. For new (non-existent) files, document the intended path with an `[UNVERIFIED]` prefix (see Step 5).
- **Never edit `Satisfies:` manually** — re-run `sync.py` if requirements change.
- **Never skip `validate.py --cross`** — a plan that passes `--spec` and `--plan` can still have uncovered requirements.
- **Never hand the plan to an executor before all three validators pass.**

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
