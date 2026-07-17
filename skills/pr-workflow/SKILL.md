---
name: pr-workflow
description: 'Use when ready to ship a change that needs push and PR. Prefer over write-commit when the work must land remotely; over request-code-review when already reviewed.'
disable-model-invocation: false
argument-hint: '[what to ship: "current diff", a branch, or "agent branches"]'
allowed-tools: Bash(git *), Bash(gh *), Read, AskUserQuestion, Skill(write-commit)
---

# pr-workflow

Terminal step: land work that's done (ideally reviewed) as a single, atomically-committed PR. Generate the branch name and PR body — don't make the human author plumbing. Reserve confirmation for **the push**: the first step that leaves the machine and is hard to retract.

**Commit mechanics → [write-commit](../write-commit/SKILL.md).** Step 3 delegates all staging, secret-scan, policy-detection, and message-format rules to [write-commit](../write-commit/SKILL.md). Do not duplicate them here.

## Process Flow

```
Start: Deliver Request
  -> 0. Scope: reviewed? any uncommitted changes? single branch vs many agent branches?
  -> 1. Detect & Group (git status / diff) -> logical change groups
  -> 2. Branch (auto-name <type>/<desc>, or reuse the current feature branch)
  -> 3. Commit (atomic per group, generated message, secret scan)
  -> 4. Push  ── CONFIRM HERE (first irreversible / outward-facing step)
  -> 5. PR (gh pr create, generated title + body + change summary)
       -- not yet reviewed --> request-code-review (handoff before merge)
       -- git/gh fails ------> root-cause the error trace before retrying
```

## Step 0: Check Status

1. **Reviewed?** If not reviewed, suggest `request-code-review`. Do not proceed unless the user says yes.
2. **Check Git:** Run `git status --porcelain` and `git branch --show-current`.

**Done when:** `git status --porcelain` and `git branch --show-current` output is captured and review status is confirmed.

## Step 1: Group Changes

1. Run `git status --porcelain`, `git diff --stat`, `git diff --name-only`, and `git diff --staged --stat` in parallel.
2. Group related files together. Keep features, fixes, and formatting in separate groups.
3. Show the groups to the user briefly.

**Done when:** changed files are grouped into logical change groups and shown to the user.

## Step 2: Create Branch

1. **Format:** `<type>/<short-name>` (max 50 characters).
2. **Types:** `feature`, `fix`, `refactor`, `docs`, `test`, `chore`.
3. **Action:** If on `main`, run `git checkout -b <name>` with a self-generated name. If already on a correct feature branch, stay there.

**Done when:** `git checkout -b <type>/<short-name>` succeeded, or the current branch is confirmed as a correct feature branch.

## Step 3: Commit Safely

1. Follow [write-commit](../write-commit/SKILL.md) for all staging, secret-scan, policy-detection, and message-format rules.
2. Show the generated commit message, then commit — one commit per file group.

**Done when:** one commit per file group is made.

## Step 4: Ask Before Pushing

1. **Gate:** Call `AskUserQuestion` (Yes/No, no manual "Other") asking permission to push. This is a separate turn — never call `git push` in the same response as the question.
2. **Action:** Run `git push -u origin <branch>` only after the answer is yes. Any other answer stops here; do not retry the push without asking again.
3. **Never force-push:** Never `git push -f` or skip branch rules — it rewrites history other agents or branches may depend on.

**Done when:** `AskUserQuestion` returned yes and `git push -u origin <branch>` succeeded.

## Step 5: Create Pull Request (PR)

1. Run: `gh pr create --title "<title>" --body "<body>"`
2. Use this exact template for the body:

```text
   ## Summary
   <1-3 lines explaining what and why>

   ## Changes
   - <file>: <what changed>

   ## Notes
   - <things intentionally left alone, follow-ups, or risks>

```

**Done when:** `gh pr create --title "<title>" --body "<body>"` returns a PR URL.

## Multi-Agent Rules (Working with other AI)

1. **Separate Folders:** Give each agent its own folder and branch via `git worktree add ../<repo>-<task> -b <type>/<task>`.
2. **Keep Commits Separate:** Never squash commits from different agents. Keep the exact history.
3. **Merging:** Open one PR per branch. If merging branches together, fix conflicts one by one. Root-cause the failure if a merge fails.
4. **Same Gate Applies:** Each agent's push still goes through Step 4 — one confirmation per branch, no exceptions for worktrees.

## Next Steps & Errors

| Scenario             | Next Action                                                |
| :------------------- | :--------------------------------------------------------- |
| Need review?         | Use [request-code-review](../request-code-review/SKILL.md) |
| Got review comments? | Use [receive-code-review](../receive-code-review/SKILL.md) |
| Got an error?        | Root-cause the failure from the error trace               |
