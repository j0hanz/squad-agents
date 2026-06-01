# Managed Agents — Detailed Reference

## `coder`

- **Job:** Autonomous code execution — implement, refactor, fix, test
- **Isolation:** Git worktree (changes land in a branch, not your working tree)
- **Preloaded skills:** `refactor`, `diagnose`
- **Use when:** A task requires many file edits, a known implementation approach, or you want to protect the main session from churn
- **Invoke:** Mention `@coder` or use the `coder` skill

## `detective`

- **Job:** Root-cause analysis — stack traces, logic bugs, resource leaks
- **Read-only:** Cannot modify files; returns a structured bug report with diff proposals
- **Output format:** Severity / Category / Root cause / Evidence / Proposed fix
- **Use when:** A bug is non-obvious, cross-file, or you want an independent diagnosis
- **Invoke:** Mention `@detective`

## `documenter`

- **Job:** Generate or update AGENTS.md, README, CLAUDE.md, skill docs
- **Use when:** Structure changed, new components added, or docs are stale
- **Invoke:** Mention `@documenter` or `/docs`

## `explorer`

- **Job:** Read-only code search and research (Haiku model — low cost)
- **Use when:** You need to find symbols, trace usage, or research a library before acting
- **Invoke:** Mention `@explorer`
