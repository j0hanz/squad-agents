---
name: write-commit
description: 'Use when staging changes and writing git commit messages. Prefer over pr-workflow when changes only need to be committed locally and not yet pushed or submitted as a PR.'
disable-model-invocation: false
allowed-tools: Bash(git *), Read
---

# Git Commit Agent

**Canonical source for commit mechanics.** Every other skill that stages and commits (`pr-workflow` Step 3, `multi-agent-development` Operational Rules, `parallel-brainstorming` Phase 6, `diagnose` Resume-after-fix, `receive-code-review` Routing) defers to the rules here. Do not duplicate these rules elsewhere — link to this skill instead.

```text
  ┌───────────────┐     git add      ┌──────────────┐   git commit    ┌──────────────┐
  │ Working Tree  │ ───────────────► │ Staging Area │ ──────────────► │ Local Branch │
  │ (Uncommitted) │                  │ (To Commit)  │  Conventional   │ (Committed)  │
  └───────────────┘                  └──────────────┘     Format      └──────────────┘
```

## STRICT RULES

- Exactly one logical change per commit.
- Stop if passwords, tokens, or keys are present.
- `git add <exact-file-name>` ONLY. No wildcards or `git add .`.

## FORMAT

`<type>(<scope>): <subject>`

- **Type**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- **Scope**: Lowercase, optional. Add `!` for breaking changes (`feat(api)!:`).
- **Subject**: Imperative mood ("add", not "added"). Max 50 chars. No trailing period.

**Body**: Only for non-obvious _why_, breaking changes, migration notes, or linked issues. Limit 72 chars/line. Use `-` bullets. Skip if self-explanatory.

**What NEVER goes in:**

- "This commit does X", "I", "we", "now", "currently" (diff shows _what_ changed).
- AI attributions ("Generated with...").
- **AI Vocabulary**: "crucial", "delve", "enhance", "intricate", "pivotal", "showcase", "additionally", "underscore", "valuable".
- **AI Punctuation**: Em/en dashes (—/–). Use commas, colons, or parentheses.

## WORKFLOW

1. `git status --porcelain` & `git diff` to find scope/intent.
2. Check commit policy: read `AGENTS.md` for `<!-- project-init:hard-rules ... commit=(strict|relaxed|minimal) -->`. No marker → treat as `relaxed`.
   - `strict`: include scope (`<type>(<scope>): <subject>`).
   - `relaxed` / `minimal`: scope is optional (`<type>: <subject>`).
3. Secret scan: `git diff --staged | grep -iE 'password|secret|api_key|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]+|token|BEGIN .*PRIVATE KEY'`. Stop and warn if anything matches.
4. `git add <exact-file-name>` — one logical group of files.
5. `git commit -m "<type>(<scope>): <subject>"` (append `-m "<body>"` if needed).
6. Repeat steps 4–5 for each additional logical change group.

**Done when:** `git status --porcelain` shows a clean working tree (or only intentionally-unstaged files) AND every staged logical group has its own commit.

## EXAMPLES

- `feat(api): add user profile endpoint`
- `fix(billing): resolve null pointer in webhook`
- `feat(auth)!: remove deprecated v1 auth endpoint`

## NEXT STEPS

- **Ready to push + open PR?** Hand off to `pr-workflow` (Steps 4–5).
- **Secret found?** Stop completely. Surface to user — do not commit.
- **Merge conflict?** Use `diagnose`.
