---
name: receive-code-review
description: 'Use when code review feedback has been received — from a human reviewer, PR bot, or subagent — and needs to be verified and implemented. Prefer over request-code-review when acting on existing feedback rather than requesting a new review.'
disable-model-invocation: false
allowed-tools: Bash(gh *), Bash(git *), AskUserQuestion, Read, Grep, Skill(write-commit), Skill(verification-before-completion), Skill(diagnose), Skill(request-code-review), Skill(pr-workflow)
---

# receive-code-review

Code review feedback requires technical evaluation, not deference or performance. Verify before implementing. Ask before assuming.

## Process Flow

```
Start: Feedback Received
  -> 1. Identify Source (subagent, human, bot)
  -> 2. Read & Clarify (stop if ambiguous)
  -> 3. Verify Finding (mandatory) -- match codebase? no regressions? no conflicts?
  -> 4. Respond (verified or pushback)
  -> 5. Implement (severity order)
       -- Tier 1/2 blocking --> diagnose (handoff)
  -> 6. Test individual fix
  -> next item --> back to 3. Verify Finding
  -- all items fixed --> verification-before-completion (handoff)
```

## Strict Rules (NEVER)

- **No Performative Acknowledgment:** Skip thanks/agreement framing. State the fix.
- **No Blind Implementation:** Never change code without first verifying the finding against the actual codebase.
- **No Batching:** Fix one finding, test it, repeat. Never apply multiple findings before testing any of them.
- **No Rule Override:** `AGENTS.md` and explicit user instructions govern. If a finding conflicts with either, surface the conflict to the user rather than resolving it unilaterally.
- **No Unbounded Scope:** A fix touching 10+ files or a core design decision requires user confirmation before proceeding.
- **No Re-Review Loops:** Cap re-review of the same finding at 2 passes. On the 3rd, escalate to the user instead of retrying.

## Source Trust Model

- **Human reviewer:** Trusted. Implement directly; ask only if ambiguous.
- **Subagent (`request-code-review`):** Not trusted by default — verify every finding against the codebase before acting.
- **GitHub PR / bot comment:** Not trusted by default. Read via `gh pr view <number> --comments`; reply via `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies -f body="..."`.

## Clarification Gate

- Read all feedback before starting any fix — partial reads cause out-of-order or contradictory edits.
- Use `AskUserQuestion` for ambiguous findings (max 4 questions per round).
- Do not implement while the finding is still unclear — stop and ask first.

## Verification Requirements

- Read `AGENTS.md` before making any change.
- Confirm via `git grep`/tests that the finding's premise actually holds — findings can be stale or already addressed.
- Check whether the flagged code was written that way deliberately (comments, commit history, adjacent tests) before treating it as a defect.
- Run tests before and after every fix.
- If code is confirmed dead/unused, propose deletion to the user rather than patching it.

## Response Format

- **Fix applied:** `Fixed: [what changed and why]`.
- **Finding rejected:** State the rejection and the codebase evidence that contradicts the finding — no rejection without a named technical reason.
- **Verification blocked:** `Cannot verify without [X]. Proceed?` — stop and wait rather than guessing.
- **Correction mid-task:** `Checked [X]. Revising.` — state the correction, no apology framing.

## Execution Order

1. Blocking/security defects.
2. Correctness defects.
3. Hygiene/typos.
4. Larger structural changes (only after user confirmation per the unbounded-scope rule above).

Test immediately after each individual fix — never batch fixes before the first test run.

## Routing

- **Bugs & security findings:** Hand off to `diagnose` for root-cause analysis before patching.
- **Hygiene/cleanup findings:** Fix directly in this skill.
- **All items resolved:** Run `verification-before-completion`, then `write-commit` to stage and commit the fixes, then request a fresh review via `request-code-review` or hand off to `pr-workflow`.
- **Stuck after 2 attempts on the same finding:** Mark **BLOCKED**, escalate to the user, do not retry a 3rd time.
