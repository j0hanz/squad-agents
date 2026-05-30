---
description: Create or update plugin documentation — AGENTS.md, CLAUDE.md, skill docs, or README.
argument-hint: [agents-md|claude-md|readme|skill <name>]
---

# Docs: $ARGUMENTS

Author or update plugin documentation for: `$ARGUMENTS`

If no target is provided, ask:

> "What documentation do you want to create or update? Options: `agents-md`, `claude-md`, `readme`, or `skill <name>`."

## Routing

| Target           | Action                                                                  |
| ---------------- | ----------------------------------------------------------------------- |
| `agents-md`      | Invoke `agents-maintainer` skill to update `AGENTS.md`                  |
| `claude-md`      | Invoke `agents-maintainer` skill to update `CLAUDE.md`                  |
| `readme`         | Use the `documenter` agent to regenerate or update `README.md`          |
| `skill <name>`   | Invoke `agents-maintainer` skill to document `skills/<name>/SKILL.md`   |

## Guidelines

- `AGENTS.md` / `CLAUDE.md`: The `agents-maintainer` skill enforces conciseness — trim repeated linter rules, dead conventions, and content that drifts from real usage.
- `README.md`: The `documenter` agent derives content from the actual plugin structure. Confirm the component counts (skills, hooks, commands) match reality before publishing.
- Skill docs: ensure the `description` frontmatter triggers accurately; the `agents-maintainer` skill audits trigger phrase specificity.

---

<!-- Usage: /docs agents-md -->
<!-- Usage: /docs readme -->
<!-- Usage: /docs skill brainstorming -->
