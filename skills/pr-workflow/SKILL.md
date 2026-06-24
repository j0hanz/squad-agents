---
name: pr-workflow
description: 'Delivers a code change to GitHub the convenient way — ideally reviewed, but proceeds unreviewed on explicit confirmation: smart change detection, automatic branch naming, atomic commits, push, and a pull request with a generated description — the terminal "ship it" step of the dev lifecycle. Use when the user says "open a PR", "ship it", "push my work", "raise a PR", "create a pull request", or "deliver the change". Multi-agent aware: isolates parallel agents in git worktrees and assembles their branches into PRs, conflict-aware. Trigger on: "commit and push", "open/raise/create a PR", "ship this", "deliver this change", "branch and commit", "assemble agent branches". Always prefer this over gh-actions for shipping an ordinary diff, and over request-code-review when the change is already reviewed and just needs to land. Not for authoring CI/Actions YAML or gh batch scripts — that is gh-actions.'
disable-model-invocation: false
argument-hint: '[what to ship: "current diff", a branch, or "agent branches"]'
allowed-tools: Bash(git *), Bash(gh *), Read, Edit, AskUserQuestion
---

# pr-workflow

The convenient terminal step: take work that's done (and ideally reviewed) and land it as a single, atomically-committed PR with the least fuss. Generate the branch name, the commit messages, and the PR body — don't make the human author plumbing. Reserve confirmation for the one moment it matters: **the push**, because that's the first step that leaves the machine and is hard to retract.

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
       -- git/gh fails ------> diagnose (handoff with the error trace)
```

## Step 0: Check Status

1. **Reviewed?** If not reviewed, suggest `request-code-review`. Do not proceed unless the user says yes.
2. **Check Git:** Run `git status --porcelain` and `git branch --show-current`.

## Step 1: Group Changes

1. Run `git status --porcelain`, `git diff --stat`, `git diff --name-only`, and `git diff --staged --stat` in parallel.
2. Group related files together. Keep features, fixes, and formatting in totally separate groups.
3. Show the groups to the user clearly and briefly.

## Step 2: Create Branch

1. **Format:** `<type>/<short-name>` (max 50 characters).
2. **Types:** `feature`, `fix`, `refactor`, `docs`, `test`, `chore`.
3. **Action:** If on `main`, run `git checkout -b <name>` with a self-generated name. If already on a correct feature branch, stay there.

## Step 3: Commit Safely

1. Make one commit for each group of files.
2. Add specific files: `git add -- path/to/file`. Do NOT use `git add -A`.
3. **Secret Check:** Run `git diff --staged | grep -iE 'password|secret|api_key|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]+|token|BEGIN .*PRIVATE KEY'` and `git diff --staged --name-only | grep -E '\.env($|\.)|\.pem$|\.pfx$|id_rsa$'`. Stop completely and warn the user if either finds anything. Pattern-based, not exhaustive — a bare credential in an unflagged variable name can still slip through; for high-stakes repos pair this with a real scanner (e.g. `gitleaks`).
4. **Message:** `<type>: <why you did it>` (max 72 characters).
5. Show the commit to the user and wait for them to say "OK".

## Step 4: Ask Before Pushing

1. **Gate:** Call `AskUserQuestion` (Yes/No, no manual "Other") asking permission to push. This is a separate turn — never call `git push` in the same response as the question.
2. **Action:** Run `git push -u origin <branch>` only after the answer is yes. Any other answer stops here; do not retry the push without asking again.

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

## Multi-Agent Rules (Working with other AI)

1. **Separate Folders:** Give each agent its own folder and branch using `git worktree add ../<repo>-<task> -b <type>/<task>`.
2. **Keep Commits Separate:** Never squash (squish together) commits from different agents. Keep the exact history.
3. **Merging:** Open one PR per branch. If merging branches together, fix conflicts one by one. Use `diagnose` if a merge fails.
4. **Same Gate Applies:** Each agent's push still goes through Step 4 — one confirmation per branch, no exceptions for worktrees.

## STRICT RULES (NEVER DO THIS)

- **NEVER** push or open a PR without asking the user first (the push is the first step that leaves the machine — see Step 4).
- **NEVER** commit passwords, secret keys, or `.env` files (see Step 3's secret check).
- **NEVER** mix different tasks in one commit (like fixing a bug and changing spacing) — it breaks `git bisect` and makes a single-commit revert impossible.
- **NEVER** force-push (`git push -f`) or skip branch rules — it rewrites history other agents or branches may depend on.

## Next Steps & Errors

- **Need review?** Use `request-code-review`.
- **Got review comments?** Use `receive-code-review`.
- **Got an error?** Use `diagnose`.
- **Too much text to read?** Use `context-optimizer`.
