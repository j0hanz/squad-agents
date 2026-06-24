# Agent Instructions

purpose: A plugin to help with agent development and testing.

## Hard Rules

commit: no enforced message format, no required attribution trailer
maturity: breaking changes are fine — never add fallback/legacy-compat shims, rewrite to the better approach directly
testing: test/typecheck files you changed; don't require full-suite runs
ci: no automated CI, local-only test execution and deployment

<!-- codebase-init:hard-rules v1 commit=minimal maturity=development testing=touched-files ci=local-only -->

## Package Manager

pm: npm
install: npm install
validate: npm run validate
test: npm test

## Dependency Locations

node_modules: `node_modules/`
.venv: `.venv/`

## File-Scoped Commands

| Task          | Command                                 |
| ------------- | --------------------------------------- |
| Lint (JS)     | `npx eslint path/to/file.js`            |
| Test (JS)     | `node --test path/to/file.test.mjs`     |
| Lint (Python) | `python -m ruff check path/to/file.py`  |
| Test (Python) | `python -m pytest path/to/file_test.py` |

## Key Conventions

esm: ESM import/export syntax only — no CommonJS require()
hooks: hook handlers must be Bash-only — no JS/Python/MJS files allowed in `hooks/hooks.json`
manifest: `plugin.json` must use schema validation (`https://json.schemastore.org/claude-code-plugin-manifest.json`)
skills: every skill in `skills/` must contain `SKILL.md` with flat YAML frontmatter (keys: `name`, `description`)
dependencies: Python dev dependencies are declared in `pyproject.toml` — never run `pip` directly

## Commit Attribution

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
