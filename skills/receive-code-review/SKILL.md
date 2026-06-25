---
name: receive-code-review
description: "Processes, verifies, and implements code review feedback received from human reviewers, pull request bots, or subagents. Accepts markdown or text review comments as input, checks them against the codebase to prevent regression or conflict, and outputs verified, atomic file edits. Also triggers when addressing automated git comments, fixing lints, or updating changes from a previous review. Always prefer this skill over request-code-review when modifying code based on existing feedback rather than requesting a new review. Trigger on: 'review feedback', 'reviewer said', 'PR comments', 'fix review comments', 'receive-code-review', 'implement feedback', 'address feedback', 'PR feedback', 'address review comments'."
disable-model-invocation: false
---

# receive-code-review

Code review feedback requires technical evaluation, not emotional performance or blind compliance. Verify before implementing. Ask before assuming.

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

## Strict Prohibitions

**Sycophancy**: NEVER say "you're right" or thank the reviewer. Just fix it.
**Blind Fixes**: NEVER apply a fix without checking if it fits this specific code.
**Batching**: NEVER fix many things and test once. Fix one, test one, repeat.
**Conflicts**: NEVER ignore user choices or `AGENTS.md`. Tell the user if rules clash.
**Giant Changes**: NEVER rewrite more than 10 files or change core design without asking first.
**Endless Loops**: NEVER do a 3rd code review on the same code. Ask the user instead.

## Source Handling

**Subagent (`request-code-review`)**: Untrusted. Check everything it says.
**Human**: Trusted. Fix it, but ask if you are confused.
**GitHub PR/Bot**: Untrusted. Read with `gh pr view <number> --comments`. Reply directly in the thread using `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies -f body="..."`.

## Clarify First

**Read First**: Read all feedback before doing any work.
**Confusion**: Use `AskUserQuestion` to ask about unclear items all at once (up to 4 questions).
**Pausing**: Do not start fixing if related parts are still confusing.

## Mandatory Checks

**Docs**: Always read `AGENTS.md` before writing code.
**Local Match**: Check if the code actually needs this fix (use `git grep` and tests).
**Breaks**: Run tests before and after to make sure you didn't break anything.
**On Purpose**: Check if the code was written this way for a specific reason.
**Dead Code (YAGNI)**: If the code is never used, ask to delete it instead of fixing it.

## How to Reply

**Good Fix**: "Fixed. [what changed]"
**Bad Idea**: Push back. Say why it is wrong using proof from the code.
**Needs Proof**: "Can't verify this without [X]. Should I proceed?"
**Oops**: "Checked [X]. Fixing." (NEVER say sorry).

## Doing the Work

**Order**: 1. Big bugs (Security/Correctness). 2. Easy typos. 3. Hard changes.
**Testing**: Test every single fix immediately.

## Routing & Skills

**Tier 1/2 (Bugs/Security)**: Use `diagnose` to find the real problem.
**Tier 4 (Cleanup)**: Fix directly inline.
**Done**: Use `verification-before-completion`, then ask for a new review.
**Failing Twice**: Stop. Mark as **BLOCKED**. Wait for the user to tell you what to do next. Do not keep trying.
