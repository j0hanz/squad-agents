# Squad Agents

A Claude Code plugin for authoring and maintaining skills and hooks. Node.js ≥ 22 + Python ≥ 3.10.

## Hard Rules

- **commit:** no enforced message format, no required attribution trailer.
- **maturity:** breaking changes are fine — never add fallback/legacy-compat shims, rewrite to the better approach directly.
- **testing:** test/typecheck only files you changed; don't run the full suite.
- **ci:** local-only — no automated CI; run tests locally before pushing.

## Commands

| Task            | Command                                                           |
| --------------- | ----------------------------------------------------------------- |
| Lint (JS)       | `npm run lint`                                                    |
| Lint (Python)   | `python -m ruff check .`                                          |
| Validate plugin | `npm run validate`                                                |
| Test (Python)   | `python -m pytest`                                                |
| Release         | `npm version patch\|minor\|major` (syncs manifests, tags, pushes) |

## Conventions

- **ESM only** — no CommonJS `require()`.
- **Hooks are Bash-only** — no JS/Python/MJS handlers in `hooks/hooks.json`.
- **`plugin.json`** uses the schema validation URL.
- **Every skill** in `skills/` has a `SKILL.md` with flat frontmatter (`name`, `description`).
- **Python dev deps** live in `pyproject.toml` — don't run `pip install` directly.
