# ponytail-audit

## 1. Goal

Clean up the over-engineered and dead code identified in the repository audit to maximize code health and minimize maintenance overhead.
Completion signal: All target files/sections removed or refactored, and all project tests passing successfully (including validation and integration tests).

## 2. Requirements

- `REQ-001`: Remove `skills/multi-agent-dispatch/scripts/blackboard.py` and its integration test `tests/integration/test_blackboard.py`.
- `REQ-002`: Remove duplicate bash actions workflow linter `skills/github-automation/scripts/lint.sh`.
- `REQ-003`: Update `skills/github-automation/references/troubleshooting.md` and `skills/github-automation/evals/evals.json` to reference `lint.py` instead of the deleted `lint.sh`.
- `REQ-004`: Inline YAML frontmatter parser in Javascript in `bin/validate-plugin.mjs`, eliminating `bin/validate_yaml.py` and the `getPythonPath` function.
- `REQ-005`: Remove the forbidden custom `agents` folder validation logic from `bin/validate-plugin.mjs`.

## 3. Constraints

- `CON-001`: Must not break existing plugin validations or runtimes.
- `CON-002`: Must not add any third-party npm dependencies.

## 4. Interfaces

- Command line interface runs `npm test` and `npm run validate` to ensure correct execution.

