# skill-audit-remediation

## 1. Goal

- One sentence: Remediate testing infrastructure gaps and standardize skill handoffs identified during the ecosystem audit.
- Completion signal: `npm test` executes without errors and all prioritized skills have verified triggering logic.

## 2. Requirements

- `REQ-001`: The `package.json` `test:node` script MUST only reference test files that exist on the filesystem.
- `REQ-002`: The `skills/multi-agent-development/` skill SHALL have an `evals.json` file for triggering verification.
- `REQ-003`: The `pyproject.toml` `testpaths` MUST include all `skills/*/tests` and `skills/*/scripts/tests` directories.
- `REQ-004`: Design-heavy skills (`brainstorming`, `planning`, `architecture`) SHALL produce a `*-brief.json` artifact to standardize handoffs.

## 3. Constraints

- `CON-001`: Do NOT remove actual test logic; only prune invalid references or add missing configurations.
- `CON-002`: Maintain ESM compatibility in all JavaScript changes.

## 4. Interfaces

The system uses standard CLI and filesystem interfaces.

### Test Runner

**Input:**

- `npm test` (command): Runs the full validation suite.

**Output:**

- Exit Code 0: All tests passed.
- Exit Code 1: Test or validation failure.

## 5. Context

- Files: `package.json`, `pyproject.toml`, `skills/multi-agent-development/evals.json`
- Current behavior: `test:node` script references 12 missing files, causing `npm test` to fail.
- Conventions: Skills use `evals.json` for LLM triggering tests; Node tests use `node --test`.

## 6. Acceptance Criteria & Validation

- `AC-001`: `npm test` completes successfully.
- `VAL-001`: `npm test`
- `AC-002`: `skills/multi-agent-development/evals.json` exists and contains valid trigger cases.
- `VAL-002`: `ls skills/multi-agent-development/evals.json`

## 7. Examples & Edge Cases

**Positive example:**

```bash
$ npm test
# Output shows all Node and Python tests passing, including new evals.
```

**Edge cases:**

- **Missing directories:** If a skill has no `tests` folder, `pytest` should gracefully skip it without failing the entire run.
