---
name: write-commit
description: 'Use during local git commit creation and file staging. Prefer over pr-workflow when changes are local and do not require remote pushing or a PR.'
disable-model-invocation: false
allowed-tools: Bash(git *), Read
---

# write-commit

**Canonical source for commit mechanics.** Sibling skills defer here: [pr-workflow](../pr-workflow/SKILL.md) Step 3, [parallel-brainstorming](../parallel-brainstorming/SKILL.md) Phase 6, [receive-code-review](../receive-code-review/SKILL.md) Routing. Link, do not duplicate.

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

Conventional Commits — apply when step 2 selects Conventional; scope mandatory only under `strict`.

`<type>(<scope>): <subject>`

- **Type**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- **Scope**: Lowercase, optional. Add `!` for breaking changes (`feat(api)!:`).
- **Subject**: Imperative mood ("add", not "added"). Max 50 chars. No trailing period.

**Body**: Only for non-obvious _why_, breaking changes, migration notes, or linked issues. Limit 72 chars/line. Use `-` bullets. Skip if self-explanatory.

**What NEVER goes in:**

- "This commit does X", "I", "we", "now", "currently" (diff shows _what_ changed).
- AI attributions: never add prose like "Generated with Claude Code." Add a `Co-Authored-By:` trailer only if `AGENTS.md` policy requires one.
- **AI Vocabulary**: "crucial", "delve", "enhance", "intricate", "pivotal", "showcase", "additionally", "underscore", "valuable".
- **AI Punctuation**: Em/en dashes (—/–). Use commas, colons, or parentheses.

## WORKFLOW

1. `git status --porcelain` & `git diff` to find scope/intent.
2. Check commit policy: read `AGENTS.md` for `<!-- project-init:hard-rules ... commit=(strict|relaxed|minimal|skip) -->`. No marker → treat as `relaxed`.
   - `strict`: Conventional required — `<type>(<scope>): <subject>` (scope mandatory).
   - `relaxed` / `minimal` / `skip`: match the repo's existing style (`git log --format=%s`). Conventional with scope optional when the repo already uses it; free-form otherwise.
3. `git add <exact-file-name>` — one logical group of files.
4. Secret scan: `git diff --staged | grep -iE 'password|secret|api_key|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]+|token|BEGIN .*PRIVATE KEY'`. Stop and warn if anything matches.
5. `git commit -m "<message per step 2>"` (append `-m "<body>"` if needed).
6. Repeat steps 3–5 for each additional logical change group.

**Done when:** `git status --porcelain` shows a clean working tree (or only intentionally-unstaged files) AND every staged logical group has its own commit.

## EXAMPLES

- `feat(api): add user profile endpoint`
- `fix(billing): resolve null pointer in webhook`
- `feat(auth)!: remove deprecated v1 auth endpoint`

## Next Steps

| Scenario                 | Next Action                                                    |
| :----------------------- | :------------------------------------------------------------- |
| Ready to push + open PR? | Hand off to [pr-workflow](../pr-workflow/SKILL.md) (Steps 4–5) |
| Merge conflict?          | Use [diagnose](../diagnose/SKILL.md)                           |
