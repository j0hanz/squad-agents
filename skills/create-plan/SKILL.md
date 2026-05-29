---
name: create-plan
description: |
  Creates a structured implementation plan for a specific technical task. Use when you already have a validated spec (from `create-specs`) or are handed a well-scoped task and need an executable plan. ROUTING: if the user is starting a feature from scratch with no spec yet, invoke `spec-driven-development` first — this skill is its Step 3 sub-skill, not a replacement for the full workflow. Triggers directly on: 'create a plan', 'write a plan for', 'plan this out', 'what are the steps to', or when `spec-driven-development` reaches its Planning Gate. Also use standalone for: refactoring a known component, upgrading a dependency, migrating infrastructure — tasks where scope is already clear. Offers quick-start flags (--quick for simple features, --compact for overviews, --assume-paths for multi-repo). Do NOT skip this for multi-step technical work.
disable-model-invocation: true
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

### Example 1: Default `--atomic` (Detailed Tasks)

Perfect for implementation teams. Produces **15-40 atomic tasks** with exact code:

```markdown
# Task 1: Set Up JWT Utilities

**Files**: [src/utils/jwt.ts](src/utils/jwt.ts)  
**Symbols**: [generateToken](src/utils/jwt.ts#L15)  
**Action**: Create JWT generation function with error handling  
**Validate**: `npm test -- src/tests/jwt.test.ts`  
**Expected result**: All 8 tests pass, 0 skipped

# Task 2: Create Authentication Middleware

**Files**: [src/middleware/auth.ts](src/middleware/auth.ts)  
**Depends on**: Task 1  
**Action**: Implement middleware that validates JWT in Authorization header  
**Validate**: `npm test -- src/tests/middleware.test.ts`  
**Expected result**: All 6 tests pass
```

**Use when**: Building features, refactoring code, creating something new  
**Effort**: 1-2 hours per 5 tasks  
**Best for**: Developers, CI/CD pipelines, agent execution

---

### Example 2: `--compact` (Executive Summary)

Perfect for stakeholder approval. Produces **6-8 phases** with timeline:

```markdown
# JWT Authentication Implementation Plan

## Phase 1: Setup & Dependencies (1-2 hours)
- [ ] Install jsonwebtoken library
- [ ] Configure environment variables
- [ ] Design token payload structure

## Phase 2: Core Implementation (2-3 hours)
- [ ] Create JWT utilities (generation, verification)
- [ ] Build authentication middleware
- [ ] Integrate with user endpoints

## Phase 3: Testing & Validation (2-3 hours)
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Verify security best practices

**Total Effort**: 7-10 hours  
**Timeline**: 1-2 days with full team
```

**Use when**: Need executive approval, stakeholder reviews, quick go/no-go decisions  
**Effort**: Estimated upfront (no task breakdown)  
**Best for**: Managers, stakeholders, budget planning

---

### Example 3: `--narrative` (Runbook & Operations)

Perfect for DevOps handoff. Includes runbooks and procedures:

```markdown
# JWT Authentication Setup Runbook

## For: Platform Engineers & DevOps

### Pre-Flight Checklist
- [ ] Verify Node.js version: `node -v` (16+)
- [ ] Check available disk space: `df -h`
- [ ] Confirm JWT_SECRET is set: `echo $JWT_SECRET`

### Step 1: Install Dependencies
npm install jsonwebtoken @types/jsonwebtoken

Expected output: "added X packages"

### Step 2: Verify Installation
npm test -- src/tests/jwt.test.ts

Expected result: 8 passed tests

### Troubleshooting
If tests fail with "Cannot find module jsonwebtoken":
- [ ] Run: `npm cache clean --force`
- [ ] Run: `npm install` again
- [ ] Verify: `npm ls jsonwebtoken`
```

**Use when**: Ops/infrastructure work, team training, operational handoff  
**Includes**: Step-by-step procedures, troubleshooting, team training  
**Best for**: Operations teams, SREs, knowledge transfer

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

**For SDD integration**: If coming from `spec-driven-development` with a validated spec, pass the spec to Step 2 (discovery) and skip to Step 3 (decompose).

---

## The Workflow (5 Core Steps)

| Step | What                                                                         | Success Gate                                                    |
| ---- | ---------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 1    | **Intake**: Confirm purpose, component, context                              | Purpose is specific and achievable                              |
| 2    | **Discover**: Find files & symbols (skip with `--quick` or `--assume-paths`) | All required paths verified or documented assumptions           |
| 3    | **Decompose**: Break into phases & atomic tasks                              | Each task has one clear outcome, dependencies tracked           |
| 4    | **Author**: Fill plan template with verified content                         | No placeholders; all paths are markdown links                   |
| 5    | **Validate**: Verify links and structure                                     | Plan passes validation; UNVERIFIED markers resolved or accepted |

**For SDD integration**: If coming from `spec-driven-development` with a validated spec, copy the **Goals** and **Requirements** sections from your spec as input here.

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
- **transcript.md** — Planning session record (shows reasoning, decisions)
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

## Effort Estimation

Effort depends on **task type** and **code volume**. Use this rubric:

### Base Effort by Task Type

| Task Type | Complexity | Base Time |
|-----------|-----------|-----------|
| New file (implementation) | Simple (< 50 LOC) | 15-30 min |
| New file (utility/helper) | Medium (50-150 LOC) | 30-60 min |
| New file (integration) | Complex (150-300 LOC) | 60-90 min |
| Modify existing file | Simple (1-20 changes) | 10-20 min |
| Modify existing file | Complex (20+ changes) | 30-60 min |
| Test file (unit tests) | Per 10 test cases | 20-30 min |
| Test file (integration) | Per 5 test cases | 30-45 min |
| Configuration (env vars) | Per section | 5-10 min |
| Documentation | Per 500 words | 20-30 min |

### Multiplier for Context

| Situation | Multiplier |
|-----------|-----------|
| Using familiar tech (Express, React, etc.) | 1.0x |
| Using new library/framework | 1.3x |
| Complex architecture change | 1.5x |
| First time with this codebase | 1.2x |

### Examples

**Example 1: Simple feature (add validation)**
- 1 file, 30 LOC: 20 min
- 1 test file, 8 tests: 25 min
- Total: **45 min**

**Example 2: Medium feature (JWT auth)**
- 2 new files (utils + middleware), 200 LOC: 60 min
- 2 test files, 30 tests: 90 min
- 1 config file: 10 min
- Doc: 20 min
- Total: **3 hours**

**Example 3: Large feature (multi-service API gateway)**
- 5 new files, 500 LOC: 3 hours
- 5 test files, 80 tests: 3 hours
- 2 config sections: 15 min
- Docs: 45 min
- Discovery overhead (5 repos): 30 min
- Total: **7-8 hours**

---

## Step 5 — Validate Your Plan (Automated)

Before marking plan complete, run the validation script:

```bash
python skills/create-plan/scripts/validate_plan.py plan-feature-auth-middleware-1.md
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
$ python validate_plan.py plan-feature-auth-middleware-1.md

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
Symbols: [generateToken](src/utils/jwt.ts#L15)  # Verified via discover.mjs
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

## Version Control & Git Integration

Track plan evolution using Git:

### Branching Strategy

```bash
git checkout -b plans/auth-middleware
git add plan-feature-auth-middleware-1.md
git commit -m "Add JWT auth implementation plan"
git push origin plans/auth-middleware
```

### Committing Plans

Include the plan in your PR or branch:
```bash
git commit -m "Add auth implementation plan

Implements task: Add JWT auth to Express API
File: plan-feature-auth-middleware-1.md
Effort: 3-4 hours
Status: Ready for review"
```

### Plan Versioning

When updating a plan:
- Increment version: `plan-feature-auth-middleware-1.md` → `plan-feature-auth-middleware-2.md`
- Keep old versions for history (don't delete)
- Reference in commits: "Updates plan-feature-auth-middleware-1.md"

### Linking Plans in PRs

```
Implements plan: plan-feature-auth-middleware-1.md
See: /plan/feature-auth-middleware-1.md
```

---

## Team Collaboration & Reviews

### Plan Review Workflow

1. **Generate plan** and commit to feature branch: `plans/[purpose]-[component]`
2. **Create PR** with plan for stakeholder review
3. **Reviewers check**:
   - Are all dependencies tracked correctly?
   - Is the effort estimate realistic for our team?
   - Are there missing edge cases?
   - Does it match our team's standards?
4. **Approve and merge** after feedback
5. **Assign to executor** with link to the plan: `[Full Plan](./plan/plan-name.md)`

### Feedback & Iteration

If reviewers request changes:
1. Update the plan in place (don't create v2 yet)
2. Push updates to the same branch
3. Request re-review
4. Merge when approved

If plan scope changes mid-execution:
1. Create new version: `v2`, `v3`, etc.
2. Document what changed and why
3. Notify executor of the new plan version

### Team Standards Checklist

Before approving a plan, verify:
- ✅ Plan file follows naming: `[purpose]-[component]-[version].md`
- ✅ Passes automated validation: `python validate_plan.py [plan].md`
- ✅ Effort estimate is realistic for your team and codebase
- ✅ All external dependencies documented
- ✅ Security considerations addressed
- ✅ Testing strategy is comprehensive
- ✅ Rollback plan included (if applicable)

---

## Built-In Helper Scripts

These scripts are included with the skill. They run automatically when you use the skill, but you can also invoke them manually for debugging or standalone use.

### discover.mjs — File & Symbol Discovery

Find files matching a pattern and extract function/class symbols with line numbers.

**Syntax**:
```bash
node skills/create-plan/scripts/discover.mjs \
  --pattern "src/**/*.ts" \
  --filter "generateToken|verifyToken" \
  --output discovery.json
```

**Output** (`discovery.json`):
```json
{
  "matches": [
    {
      "file": "src/utils/jwt.ts",
      "symbols": [
        {
          "name": "generateToken",
          "type": "function",
          "line": 15,
          "markdown": "[generateToken](src/utils/jwt.ts#L15)"
        }
      ]
    }
  ]
}
```

**When to use**:
- Verifying file paths before writing plan
- Finding exact line numbers for symbols
- Multi-repo projects (run per repo)
- Ensuring symbols exist before referencing them

---

### generate_plan.py — Plan Skeleton Generator

Takes a spec and generates task structure with phases.

**Syntax**:
```bash
python skills/create-plan/scripts/generate_plan.py \
  --spec spec.yaml \
  --component auth-middleware \
  --profile atomic
```

**Profiles**: `atomic` (15-40 tasks), `compact` (6-8 phases), `narrative` (runbook)

**Output**: `plan-skeleton-[component]-1.md` with structure:
```markdown
# Phase 1: Setup
## Task 1: Configure Environment
...
## Task 2: Install Dependencies
...
```

**When to use**:
- Generating initial plan structure from spec
- Choosing task granularity (atomic vs compact vs narrative)
- Re-generating plan if scope changes

---

### validate_plan.py — Plan Validation

Check that completed plan follows all conventions.

**Syntax**:
```bash
python skills/create-plan/scripts/validate_plan.py \
  plan-feature-auth-middleware-1.md
```

**Checks**:
- All file paths are markdown-linked `[file.ts](path/to/file.ts)`
- All symbols have line anchors `[func](path#L42)`
- Every task has required fields: Depends on, Files, Symbols, Action, Validate, Expected result
- No circular task dependencies (valid DAG)
- All cross-references (TASK-001, PHASE-001) exist and link

**Output**:
```
✓ 27 tasks validated
✓ All 45 file links valid
✓ No circular dependencies detected
READY FOR EXECUTION
```

**When to use**:
- Before marking plan complete
- Before handing plan to executor
- When importing plans from other sources

## Reference Docs — Quick Navigation

Read these in order only if you need them. Most of the time, you won't:

### 1. [Plan Template](references/template.md)
**Read this if**: "What should my plan look like?"

**Covers**:
- Goal statement (2-3 sentences)
- Requirements & constraints format (REQ-001)
- Phases and tasks structure
- Testing & acceptance criteria sections
- Optional: Decision log, risks, alternatives

**Time**: 5 min

---

### 2. [Discovery Guide](references/discovery.md)
**Read this if**: "How do I find files and symbols?"

**Covers**:
- Using discover.mjs to find files
- Extracting function/class symbols
- Handling multi-repo projects
- Verifying paths before adding to plan

**When to use**: If plan discovery is failing or you're in an unfamiliar codebase

**Time**: 10 min

---

### 3. [Task Decomposition](references/decomposition.md)
**Read this if**: "How do I break work into tasks?"

**Covers**:
- Task sizing (how small is small?)
- Bundled vs. atomic tasks
- Dependency ordering
- What makes a good task

**When to use**: If your tasks feel too big, too small, or out of order

**Time**: 10 min

---

### 4. [Validation Checklist](references/validation.md)
**Read this if**: "Is my plan complete?"

**Covers**:
- Complete task block structure
- Markdown link requirements
- Dependency validation (no cycles)
- Common mistakes and fixes

**When to use**: Before marking plan done and handing to executor

**Time**: 5 min

---

### Quick Reference: Which Doc for Your Problem?

| Problem | Doc |
|---------|-----|
| "What goes in a plan?" | [Template](references/template.md) |
| "I can't find the file path" | [Discovery](references/discovery.md) |
| "My tasks are too vague" | [Decomposition](references/decomposition.md) |
| "Plan validation failed" | [Validation](references/validation.md) |
| "I don't know if I'm done" | [Validation](references/validation.md) |
| "How do I organize plans?" | (See Plan Directory section below) |
