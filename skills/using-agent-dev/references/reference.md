# Quick Reference

## Tech Stack

- **Runtime:** Node.js ≥ 22 (ESM, no TypeScript — use `.mjs` for hook handlers)
- **Python:** ≥ 3.10, managed via `uv` / `pyproject.toml`
- **Package management:** `npm` (JS), `uv` (Python)
- **Validation:** `npm validate` (plugin health), `npm test` (full suite)
- **Hook dispatch:** `hooks/runner.mjs <domain> <action>` → `hooks/handlers/<domain>.mjs`
- **No logic outside runner pattern** — all hook logic lives in `hooks/handlers/`

## Key Paths

| Path                         | Purpose                                        |
| ---------------------------- | ---------------------------------------------- |
| `AGENTS.md`                  | Primary contributor guide — read this first    |
| `skills/<name>/SKILL.md`     | Each skill's instructions and frontmatter      |
| `agents/<name>.md`           | Each managed agent's system prompt and config  |
| `commands/<name>.md`         | Each slash command definition                  |
| `hooks/runner.mjs`           | Central hook dispatcher                        |
| `hooks/hooks.json`           | Event → handler registration                   |
| `hooks/handlers/*.mjs`       | Hook handler modules                           |
| `output-styles/agent-dev.md` | Output style spec (Design/Build/Validate/Ship) |
| `bin/validate-plugin.mjs`    | Plugin validation entrypoint                   |
