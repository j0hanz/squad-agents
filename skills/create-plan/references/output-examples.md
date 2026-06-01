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
