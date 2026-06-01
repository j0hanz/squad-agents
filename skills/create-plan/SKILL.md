---
name: create-plan
description: "Structured implementation plan for scoped tasks. Trigger on 'create plan', 'write plan', 'what are steps'. For specs, refactoring, upgrades, infrastructure. Flags: --quick, --compact, --assume-paths."
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash(python *) Bash(python3 *)
argument-hint: |
  [--atomic (default) | --compact (executive) | --narrative (runbook)]
  [--quick (skip discovery)] [--assume-paths (multi-repo)]
  Examples:
  - /create-plan --atomic "Add login feature"
  - /create-plan --compact --assume-paths "Migrate to K8s"
---

# Create Plan

Creates one **executable implementation plan file** for a specific technical task. Plans include structured phases, atomic tasks, verified file paths, validation commands, and acceptance criteria—designed for stateless execution so agents can pick up mid-way and understand current state.

## Get Started Now (30 Seconds)

```bash
/create-plan "Add JWT authentication to Express API"
```

This creates `plan-feature-auth-middleware-1.md` with 9 atomic tasks, complete code examples, and test cases ready for execution.

**Available flags** (optional):
- `--atomic` — 15-40 detailed tasks for implementation (default, best for engineers)
- `--compact` — 6-8 phases with executive summary (best for stakeholders/approval)
- `--narrative` — With runbooks and operational procedures (best for DevOps/SRE)
- `--quick` — Skip file discovery, assume standard structure (best for well-known patterns)
- `--assume-paths` — For multi-repo/microservices (skip cross-repo discovery)

**Examples**:
```bash
/create-plan --atomic "Add JWT auth to Express API"
/create-plan --compact "Migrate to Kubernetes"
/create-plan --narrative --assume-paths "Deploy monitoring across 3 services"
/create-plan --quick "Add form validation to React"
```

## Output Examples by Flag

**MANDATORY — READ ENTIRE FILE**: [`references/output-examples.md`](references/output-examples.md) for --atomic, --compact, and --narrative flag output examples.

---

## Pre-Flight Checks (Before You Start)

Before creating a plan, confirm these three things:

### ✅ Check 1: Do You Have Clear Scope?

Ask yourself:
- **Purpose**: What are we adding/changing/fixing? (be specific — "add login" not "improve auth")
- **Component**: Which part of the system? (ideally 1-3 files, 1-2 main functions)
- **Constraints**: Any hard limits? (deadline, tech stack, team size)

**If you're vague on any of these** ➜ Use `/create-specs` first (or invoke spec-driven-development). Come back here with a spec.

---

### ✅ Check 2: Single Repo or Multiple?

- **Single repo** (typical): Go ahead, skill will discover files automatically
- **Multiple repos** (microservices, multi-org): Use `--assume-paths` flag
  - Example: `/create-plan --assume-paths "Add auth across 3 services"`
  - Skill will document assumptions instead of failing on cross-repo discovery
- **Don't know**: Ask yourself — do you have 1 repo or 5? If unsure, it's probably 1.

---

### ✅ Check 3: Do You Know the File Structure?

- **Well-known pattern** (Express, Next.js, Django, Rails): Use `--quick`
  - Example: `/create-plan --quick "Add validation"`
  - Skill skips discovery, assumes `src/`, `tests/`, standard structure
- **Custom/unfamiliar structure**: Don't use `--quick`, let skill discover
  - Skill will ask about structure and find files
- **Completely unknown**: Provide example paths or context upfront

---

### Example Pre-Flight Decision

**Your task**: "Add JWT auth to Express API"

- ✅ Clear scope? YES — add JWT generation and middleware
- ✅ Single repo? YES
- ✅ Known structure? YES — standard Express layout

**Result**: ✅ READY
**Command**: `/create-plan --atomic "Add JWT auth to Express API"`

---

**If ANY check fails**, use `/create-specs` first, then come back here.

## The Workflow (5 Core Steps)

| Step | What                                                                         | Success Gate                                                    |
| ---- | ---------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 1    | **Intake**: Confirm purpose, component, context                              | Purpose is specific and achievable                              |
| 2    | **Discover**: Find files & symbols (skip with `--quick` or `--assume-paths`) | All required paths verified or documented assumptions           |
| 3    | **Decompose**: Break into phases & atomic tasks                              | Each task has one clear outcome, dependencies tracked           |
| 4    | **Author**: Fill plan template with verified content                         | No placeholders; all paths are markdown links                   |
| 5    | **Validate**: Verify links and structure                                     | Plan passes validation; UNVERIFIED markers resolved or accepted |

**For SDD integration**: If coming from `spec-driven-development` with a validated spec, generate a plan skeleton with `generate_plan.py` before Step 4:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_plan.py \
  spec.md --purpose <purpose> --component <component>
```

This produces a task scaffold with UNVERIFIED markers; fill in verified paths and symbols during Steps 2 and 4. See [references/scripts.md](references/scripts.md) for full syntax.

---

## Detailed Guidance

For detailed guidance on:

- **Discovery** (file/symbol verification): See [references/discovery.md](references/discovery.md)
- **Validation** (checking plans): See [references/validation.md](references/validation.md)
- **Task decomposition** (phase/task sizing): See [references/decomposition.md](references/decomposition.md)
- **Multi-repo scenarios**: See guidance below

---

## Multi-Repo & Cross-Repo Scenarios

**When files are in separate repositories** (e.g., 5 microservices, each with its own repo):

1. **Option A: `--assume-paths`** — Assume paths exist; skip discovery; note assumptions in plan
2. **Option B: Per-repo plans** — Create separate plan file for each service, linked via `Depends on: [service-B plan]()`
3. **Option C: Generate per-service** — Run skill once per service with focused context

**Note**: Cross-repo discovery (discovering symbols in external repos) is not supported. Use `--assume-paths` to proceed or provide manual path list.

---

## Output Files

- **plan-[purpose]-[component]-[version].md** — Main plan (saved to `/plan/` or user-specified directory)
- Optional: **README.md**, **validation-output.txt** (if `--verbose`)

---

## Canonical Task Block

Every task follows this structure (enforced by validation):

```
Depends on: [TASK-001](#task-001-title) or none
Files: [path/to/file.ts](path/to/file.ts)
Symbols: [functionName](path/to/file.ts#L42)
Action: Single specific, imperative implementation action.
Validate: Run `npm test -- path/to/file.test.ts`
Expected result: Observable success signal (e.g., "All 8 tests pass", "Exit code 0")
```

All file paths and symbols must be markdown links verified by discovery.

---

For effort estimation tables by task type, see [references/decomposition.md](references/decomposition.md).

---

## Step 5 — Validate Your Plan (Automated)

Before marking plan complete, run the validation script:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_plan.py plan-feature-auth-middleware-1.md
```

This checks **all of these automatically**:

| Check | What It Verifies | If It Fails |
|-------|------------------|------------|
| **File paths** | Every reference is markdown-linked `[file.ts](path)` | Plan has broken links |
| **Symbols** | Every symbol has line anchor `[func](path#L42)` | Executor can't find functions |
| **Task structure** | Each task has all required fields | Plan is incomplete |
| **Dependencies** | Tasks form a valid DAG (no cycles) | Plan can deadlock |
| **Cross-references** | TASK-001, PHASE-001 exist and link | Plan is internally broken |

### Example Validation

```bash
$ python ${CLAUDE_SKILL_DIR}/scripts/validate_plan.py plan-feature-auth-middleware-1.md

Validating plan-feature-auth-middleware-1.md...
✓ 27 tasks
✓ 45 file links
✓ 0 broken references
✓ No circular dependencies

RESULT: READY FOR EXECUTION

$ echo $?
0  # Exit code 0 = validation passed
```

**If validation fails**, the output shows exactly what needs fixing:

```
ERROR: Task 5 missing "Validate:" field
ERROR: File path [src/auth.ts] is not markdown-linked
FIX: See lines 52-55 in plan-feature-auth-middleware-1.md
```

**Don't skip validation.** A plan that passes validation is ready for agent execution; a plan that doesn't will fail partway through.

**After `validate_plan.py` returns READY FOR EXECUTION — use the Agent tool** to spawn a quality review subagent for semantic checks that structural validation cannot catch. First read `agents/reviewer.md`, then call the Agent tool:

- **description**: `"Semantic quality review of [plan filename]"`
- **prompt**: Paste the full contents of `agents/reviewer.md`, then append:
  ```
  plan_path: [absolute path to the plan file]
  project_root: [project root, if available]
  ```

The agent samples tasks and scores four dimensions: atomicity (one observable outcome per task), validation runability (commands that can execute verbatim), dependency order correctness, and effort estimate realism. Check the output:
- `ready_for_execution: false` → resolve `blocking_issues` before handing the plan to an executor
- `plan_wide_issues` → address pattern-level problems across the plan
- `ready_for_execution: true` → plan is ready for execution

---

## Anti-Patterns (NEVER Do These)

Learn what breaks plans, and how to fix them:

### Anti-Pattern 1: Vague Validation

❌ **WRONG**:
```
Validate: Check that it works
Expected result: Middleware is functioning
```

Why this breaks: An agent can't execute "check that it works" — it's not a command. Plan will fail.

✅ **RIGHT**:
```
Validate: npm test -- src/tests/auth.middleware.test.ts --verbose
Expected result: All 6 tests pass, 0 skipped
```

Why this works: The agent can run the command and observe the exact result.

---

### Anti-Pattern 2: Bundled Tasks

❌ **WRONG**:
```
Task 1: Create utils, add middleware, and write tests
```

Why this breaks: "And" means multiple outcomes. Agent doesn't know when task is complete.

✅ **RIGHT**:
```
Task 1: Create JWT utilities
Task 2: Create authentication middleware
Task 3: Write unit tests for both
```

Why this works: One task = one observable outcome. Clear completion criteria.

---

### Anti-Pattern 3: Guessed Paths

❌ **WRONG** (without discovering):
```
Files: src/utils/jwt.ts
Symbols: [generateToken](src/utils/jwt.ts#L42)
```

Why this breaks: Path might not exist, line might be wrong. Plan fails during execution.

✅ **RIGHT** (discovered and verified):
```
Files: [src/utils/jwt.ts](src/utils/jwt.ts)
Symbols: [generateToken](src/utils/jwt.ts#L15)  # Verified via discover.py
```

Why this works: Paths are markdown-linked and verified. Agent can follow them.

---

### Anti-Pattern 4: Circular Dependencies

❌ **WRONG**:
```
Task 1: Implement utils → Depends on Task 2
Task 2: Implement middleware → Depends on Task 1
```

Why this breaks: Neither can start; plan is deadlocked forever.

✅ **RIGHT**:
```
Task 1: Create JWT utilities
Task 2: Create middleware → Depends on Task 1
Task 3: Integrate middleware → Depends on Task 2
```

Why this works: Clear ordering; each task has prerequisites available.

---

## Plan Template

When authoring, follow [references/template.md](references/template.md) structure:

1. **Goal** (2-3 sentences)
2. **Requirements & Constraints** (REQ-001, CON-001, SEC-001, PAT-001 format)
3. **Current Context** (existing files, commands, behavior)
4. **Implementation Phases** (with tasks)
5. **Testing & Validation**
6. **Acceptance Criteria**
7. **Rollback Strategy** (if applicable)

Optional sections: Risks, Decision Log, Alternatives

---

## Plan Directory & Naming

Plans are saved to repository's plan directory (e.g., `/plan/`, `docs/plans/`).

**Format**: `[purpose]-[component]-[version].md`

**Purpose**: `feature`, `refactor`, `upgrade`, `architecture`, `infrastructure`, `design`, `process`, `data`

**Component**: kebab-case (e.g., `auth-module`, `react-components`, `infra-k8s`)

**Version**: Start at `1`; increment if same purpose+component exists

### Single Project Organization

```
project/
├── plan/
│   ├── feature-auth-middleware-1.md
│   ├── refactor-db-layer-1.md
│   └── infrastructure-k8s-migration-1.md
├── src/
└── tests/
```

### Multi-Service Project Organization

```
microservices/
├── services/
│   ├── auth-service/
│   │   ├── plan-feature-oauth-1.md
│   │   └── src/
│   ├── user-service/
│   │   ├── plan-refactor-queries-1.md
│   │   └── src/
│   └── api-gateway/
│       ├── plan-feature-rate-limiting-1.md
│       └── src/
├── shared/
│   └── plan-integration-auth-oauth-1.md  # Links to service plans
└── docs/
```

---

For version control conventions and team review checklist, see [references/git-workflow.md](references/git-workflow.md).

---

For detailed script documentation (syntax, output format, flags), see **MANDATORY — READ ENTIRE FILE**: [references/scripts.md](references/scripts.md) before running any script manually.

## Reference Docs

| Problem | Reference |
| --- | --- |
| Plan structure & template | [references/template.md](references/template.md) |
| Finding files & symbols | [references/discovery.md](references/discovery.md) |
| Task sizing & decomposition | [references/decomposition.md](references/decomposition.md) |
| Validation checklist | [references/validation.md](references/validation.md) |
| Script syntax (manual use) | [references/scripts.md](references/scripts.md) |
| Git workflow & team reviews | [references/git-workflow.md](references/git-workflow.md) |
