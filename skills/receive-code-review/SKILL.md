---
name: receive-code-review
description: 'Use when code review feedback has been received from a human, bot, or subagent. Prefer over request-code-review when resolving feedback rather than requesting a new review.'
disable-model-invocation: false
allowed-tools: Bash(gh *), Bash(git *), AskUserQuestion, Read, Grep, Skill(write-commit), Skill(verification-before-completion), Skill(diagnose), Skill(request-code-review), Skill(pr-workflow)
---

# receive-code-review

## Process Flow

```
Start: Feedback Received
  -> 1. Parse & Clarify  (verify trust, resolve ambiguity)
  -> 2. Verify & Test    (confirm premise holds, run tests)
  -> 3. Implement        (severity order, test after each)
  -> 4. Route            (diagnose / verification-before-completion / pr-workflow)
```

## Strict Rules

- **No Performative Acknowledgment:** Skip thanks/agreement framing. State the fix directly.
- **No Blind Implementation:** Never edit code without verifying the finding against the codebase.
- **No Batching:** Fix one finding, test it, repeat. Never apply multiple fixes before testing.
- **No Rule Override:** `AGENTS.md` and explicit user instructions govern. Surface conflicts.
- **No Unbounded Scope:** Fixes touching 10+ files or core design require user confirmation.
- **No Re-Review Loops:** Cap re-review at 2 passes. On the 3rd, escalate to the user.

## Steps

### Step 1: Parse & Clarify

1. Read all feedback before starting any fix.
2. Apply the trust model:
   - **Human reviewer:** Trusted. Implement directly; ask only if ambiguous.
   - **Subagent / Bot:** Untrusted. Verify findings against the codebase first.
3. Use `AskUserQuestion` for ambiguous findings (max 4 questions per round).
4. **Done when:** all comments are parsed, ambiguities resolved, and the trust model is applied.

### Step 2: Verify & Test

1. Read `AGENTS.md` before making any change.
2. Confirm via `git grep` and tests that the finding's premise holds (reject stale findings).
3. If code is confirmed dead or unused, propose deletion instead of patching.
4. **Done when:** the finding's premise is verified or rejected with named technical reasons.

### Step 3: Implement & Validate

1. Implement fixes one by one in severity order:
   - Blocking / security defects
   - Correctness defects
   - Hygiene / typos
2. Run tests immediately after each individual fix.
3. **Done when:** all verified fixes are implemented and validated by execution.

### Step 4: Complete & Route

1. Route remaining actions based on outcome:
   - **Bugs & security:** Hand off to [diagnose](../diagnose/SKILL.md) for root-cause analysis before patching.
   - **Stuck after 2 attempts:** Mark **BLOCKED**, escalate to the user, and do not retry.
   - **All items resolved:** Run [verification-before-completion](../verification-before-completion/SKILL.md), [write-commit](../write-commit/SKILL.md) to stage/commit, and hand off to [pr-workflow](../pr-workflow/SKILL.md) or [request-code-review](../request-code-review/SKILL.md).
2. **Done when:** all changes are committed and the target next skill or escalation is triggered.
