# Implementation Plan: [Title]

## 1. Goal

Summary: 2-4 sentences on outcome, reason, and completion signal.

## 2. Requirements & Constraints

REQ-001: [Concrete functional requirement]
CON-001: [Technical constraint]
SEC-001: [Security requirement, if relevant]
PAT-001: Follow [existing pattern](path/to/file.ts)

## 3. Current Context

Relevant files: [verified markdown links]
Relevant symbols: [verified markdown links]
Existing commands: [test, lint, build, type-check commands]
Current behavior: [What's wrong or missing in one sentence]

## 4. Effort Estimation

**Total Duration**: X-Y hours (based on N tasks)

**Breakdown**:

- Average time per task: 20-40 minutes
- Team size recommended: N developers
- Critical path: [describe sequential dependency chain]
- Parallelization: [if possible] (e.g., "Phases 2-3 can run in parallel")
- Contingency: +20% for unexpected issues

**Formula**: Duration = (task_count × 30 min) + discovery_time (1 hour) + contingency (20%)

Example: 15 tasks → (15 × 30 min) + 60 min + 180 min = 5 hours

## 5. Implementation Phases

### PHASE-001: [Phase name]

**Goal**: [One measurable phase outcome]

**Tasks**: TASK-001, TASK-002, … (see Implementation Phases section below)

#### TASK-001: [Imperative title]

Depends on: none
Files: [verified link](path)
Symbols: [verified link](path#Lnn)
Action: Specific implementation action.
Validate: Run `exact command`
Expected result: Observable success signal.

[More tasks…]

## 6. Testing & Validation

[VAL-001](#6-testing--validation): [Expected result]

## 7. Acceptance Criteria

[AC-001](#7-acceptance-criteria): [Observable behavior when done]

## 8. Design Decisions & Trade-Offs (Optional)

[DECISION-001](#8-design-decisions--trade-offs): [Decision] — Why: [Reasoning]
[DECISION-002](#8-design-decisions--trade-offs): [Decision] — Why: [Reasoning]

**Examples**:
- DECISION-001: Atomic tasks vs phases? — Why: Enables agent execution and parallel workflows
- DECISION-002: Multi-repo per-service plans? — Why: Reduces cross-repo discovery complexity
- DECISION-003: Refactor vs rewrite? — Why: [Your context-specific reasoning]

## 9. Rollback Strategy (If Applicable)

**Trigger**: [Specific condition that requires rollback, e.g., "API error rate exceeds 5%"]
**Action**: [Exact command or manual step to revert, e.g., `git revert <commit-hash>` or "Restore DB from latest snapshot"]
**Validation**: [Command to verify rollback succeeded, e.g., `curl -I https://api.example.com/health`]

## 10. Risks / Notes

[RISK-001](#10-risks--notes): Risk and mitigation
[NOTE-001](#10-risks--notes): Key execution note
