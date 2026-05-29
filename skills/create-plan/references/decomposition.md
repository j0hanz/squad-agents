# Decomposition Guide: Phases & Task Sizing

## Phase vs Task

**Phase**: A major work unit with one measurable goal. Groups related tasks.

Example: "JWT Authentication for Express API"
- PHASE-001: Implement JWT token generation and validation
- PHASE-002: Integrate JWT into middleware and routes
- PHASE-003: Test and validate end-to-end

**Task**: An atomic unit of work—one code change, one file modified, one clear outcome.

Example: Under PHASE-001
- TASK-001: Create JWT signing/verification utilities (touches src/utils/jwt.ts)
- TASK-002: Add JWT configuration module (touches src/config/jwt.ts)

## Task Sizing Heuristics

A well-sized task:
- **Duration**: 15-60 minutes for an experienced developer
- **Files**: Touches 1-3 files max
- **Outcomes**: One clear, observable result
- **Dependencies**: Minimum task-to-task coupling

### When to Split a Task

Split into separate tasks if:
- More than 3 distinct logical changes in a single file
- Writing tests for more than 2 unrelated components
- Spans unrelated modules or systems
- Has multiple independent outcomes
- Task description includes "and" or "plus" (sign of bundling)

### When Tasks Are Too Small

Combine if:
- Single file, single function, <5 minutes work
- Trivial boilerplate (e.g., imports, type definitions)
- No independent value without the next task
- Creates >50 tasks for <10 hours of work

## Phase Design

Good phases:
- Each has **one measurable goal** (e.g., "infrastructure ready", "all tests passing")
- Related tasks grouped logically
- Phases progress sequentially (early phases unblock later ones)
- 3-8 tasks per phase (depending on complexity)

Example phase structure:
```
### PHASE-001: Setup & Configuration
Goal: All dependencies installed and configuration validated
Tasks: [TASK-001](#), [TASK-002](#), [TASK-003](#)

### PHASE-002: Core Implementation
Goal: All core logic implemented and unit-tested
Tasks: [TASK-004](#), [TASK-005](#), [TASK-006](#), [TASK-007](#)

### PHASE-003: Integration & Testing
Goal: Integration tests passing, end-to-end flow validated
Tasks: [TASK-008](#), [TASK-009](#)
```

## Dependency Tracking

Every task explicitly declares its dependencies:

```
Depends on: none  (can start immediately)
Depends on: [TASK-001](#task-001-title)  (waits for TASK-001)
Depends on: [TASK-001](#task-001-title), [TASK-003](#task-003-title)  (waits for both)
```

**Rules**:
- No circular dependencies (TASK-A depends on TASK-B depends on TASK-A is invalid)
- Dependencies should follow phase order when possible
- Tasks in same phase often don't depend on each other

## Effort Estimation

**Rough formula**: 1-2 hours per 5 tasks, +1 hour for discovery

- **12 tasks** → 2-3 hours (small feature)
- **30 tasks** → 6-8 hours (migration, major refactor)
- **50+ tasks** → 10-15 hours (infrastructure, multi-component)

Adjust based on:
- **Complexity**: Add 50% for unfamiliar frameworks/languages
- **Testing**: Add 1 hour per 10 tasks if comprehensive testing required
- **External dependencies**: Add 2-4 hours if waiting on external services

## Plan Profiles

### Atomic Profile (Default)
- **Goal**: Agent execution, maximum granularity
- **Task count**: 15-40 tasks
- **Granularity**: Every change is a separate task
- **Best for**: Teams with CI/CD, automated execution
- **Effort est**: 3-8 hours for typical medium refactor

### Compact Profile
- **Goal**: Executive overview, quick understanding
- **Phases**: 6-8 phases
- **Task count**: 0 (phases only, no atomic tasks)
- **Granularity**: Groups related work into phases
- **Best for**: Stakeholder communication, planning, approvals
- **Effort est**: Same total, grouped into higher-level units

### Narrative Profile
- **Goal**: Ops/team understanding, learning
- **Format**: Phases + deep runbooks
- **Includes**: Deployment runbooks, team training, decision log
- **Best for**: Operations, large organizations, knowledge transfer
- **Effort est**: Includes 2-4 hours for runbooks/docs

## Examples

### Simple Feature (JWT Auth) — Atomic Profile
12 tasks, 4 phases, ~3 hours
- PHASE-001: Configuration (2 tasks)
- PHASE-002: Utilities (2 tasks)
- PHASE-003: Middleware (2 tasks)
- PHASE-004: Endpoints & Tests (6 tasks)

### Complex Refactor (React Components) — Atomic Profile
32 tasks, 8 phases, ~6 hours
- PHASE-001: Create composition utilities (6 tasks)
- PHASE-002: Refactor high-priority components (8 tasks)
- PHASE-003-008: Refactor medium/low priority + testing

### Infrastructure (Kubernetes) — Narrative Profile
4 phases + 10 tasks, includes runbooks
- PHASE-001: Foundation & Planning
- PHASE-002: Helm Chart Development
- PHASE-003: Validation & Testing
- PHASE-004: Production Deployment
- Plus: Deployment runbook, troubleshooting guide, team training plan
