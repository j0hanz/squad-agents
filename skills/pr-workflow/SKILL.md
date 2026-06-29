---
name: pr-workflow
description: 'Use when ready to ship a change — commit, push, and open a PR. Prefer using this for ordinary code changes, and over request-code-review when the work is already reviewed and just needs to land.'
disable-model-invocation: false
argument-hint: '[what to ship: "current diff", a branch, or "agent branches"]'
allowed-tools: Bash(git *), Bash(gh *), Read, AskUserQuestion
---

# pr-workflow

The convenient terminal step: take work that's done (and ideally reviewed) and land it as a single, atomically-committed PR with the least fuss. Generate the branch name, the commit messages, and the PR body — don't make the human author plumbing. Reserve confirmation for the one moment it matters: **the push**, because that's the first step that leaves the machine and is hard to retract.

**Canonical source for commit/branch mechanics.** Any other skill that commits, branches, or names a commit message (`multi-agent-development`, `parallel-brainstorming`, etc.) defers to Step 2/3 here rather than inventing its own format. Don't duplicate the rules below elsewhere — link to this skill instead.

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

1. Make one commit for each group of files — one logical change per commit, nothing bundled.
2. Add specific files: `git add -- path/to/file`. Do NOT use `git add -A`.
3. **Secret Check:** Run `git diff --staged | grep -iE 'password|secret|api_key|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]+|token|BEGIN .*PRIVATE KEY'` and `git diff --staged --name-only | grep -E '\.env($|\.)|\.pem$|\.pfx$|id_rsa$'`. Stop completely and warn the user if either finds anything. Pattern-based, not exhaustive — a bare credential in an unflagged variable name can still slip through; for high-stakes repos pair this with a real scanner (e.g. `gitleaks`).
4. **Detect commit policy:** Read `CLAUDE.md`/`AGENTS.md` for a `<!-- project-init:hard-rules ... commit=(strict|relaxed|minimal) -->` marker. No marker found → treat as `relaxed`.
5. **Message:**
   - Subject: `<type>(<scope>): <why you did it>` under `commit=strict` (scope = touched module/dir); `<type>: <why you did it>` otherwise. Imperative mood, max 72 characters, states _why_, not a restatement of the diff.
   - Body (only when the group spans multiple files or the why needs more than the subject): blank line, then 1-3 plain sentences on the problem solved.
   - Footer: `Refs #<n>` / `Closes #<n>` when an issue number is known from the branch name, user message, or linked ticket.
6. Show the commit to the user and wait for them to say "OK".

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

- **NEVER** force-push (`git push -f`) or skip branch rules — it rewrites history other agents or branches may depend on.
- **NEVER** bypass Step 4's push confirmation gate, even for automated or worktree branches.

## Next Steps & Errors

- **Need review?** Use `request-code-review`.
- **Got review comments?** Use `receive-code-review`.
- **Got an error?** Use `diagnose`.
