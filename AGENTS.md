# Agent Instructions

Claude Code plugin workspace for building and testing skills, agents, and hooks.

## Toolchain

Use **npm** — Node.js ≥22, Python ≥3.10. `npm test` runs the full suite (validate + Node + Python); use the file-scoped commands below for targeted runs.

## File-Scoped Commands

| Task               | Command                                        |
| ------------------ | ---------------------------------------------- |
| Lint (JS)          | `npx eslint path/to/file.mjs`                  |
| Format check       | `npx prettier --check path/to/file.mjs`        |
| Test (Node)        | `node --test tests/specific-test.mjs`          |
| Test (Python)      | `python -m pytest skills/path/to/test_file.py` |
| Test (integration) | `npm run test:integration`                     |
| Lint (Python)      | `python -m ruff check path/to/file.py`         |
| Validate           | `npm run validate`                             |

## Key Conventions

- **Skills:** Only `SKILL.md` is required; add `scripts/`, `evals/`, `references/` subdirs as needed. Each skill lives in `skills/<name>/`
- **Hooks:** Config in `hooks/hooks.json`; handlers in `hooks/handlers/*.sh` (Bash only — no `.mjs` or `.py` handlers) — no `console.log` in hook files (ESLint `no-console` warns)
- **Node scripts:** Use `.mjs` extension with ESM (`import`/`export`); no `require()` or CommonJS
- **Subagents:** No custom agent definitions — every dispatch uses the built-in `general-purpose` agent, configured per-task via the prompt. See `skills/multi-agent-dispatch` (parallel fan-out) and `skills/multi-agent-development` (sequential, gate-checked implementation).
- **Validation gate:** Run `npm run validate` before committing plugin changes — validates `.claude-plugin/plugin.json` via `bin/validate-plugin.mjs`
- **Python tests:** Pytest discovers tests under `skills/`; new test files follow `test_<module>.py` naming

## Commit Attribution

AI commits MUST include a `Co-Authored-By:` trailer.
Example: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
