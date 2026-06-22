# ponytail-audit

Spec: [ponytail-audit.specs.md](ponytail-audit.specs.md)

## Goal

Clean up the over-engineered and dead code identified in the repository audit to maximize code health and minimize maintenance overhead.

## PHASE-001: Implementation

### TASK-001: Delete blackboard.py and test_blackboard.py

Depends on: none
Files: [skills/multi-agent-dispatch/scripts/blackboard.py](skills/multi-agent-dispatch/scripts/blackboard.py), [tests/integration/test_blackboard.py](tests/integration/test_blackboard.py)
Symbols: none
Satisfies: REQ-001
Action: Delete the unused/speculative blackboard script and its integration test file.
Validate: `git status` should show them deleted, and `python -m pytest` should still pass.
Expected result: The files are removed, and pytest does not fail due to missing references.

### TASK-002: Delete duplicate actions linter lint.sh

Depends on: TASK-001
Files: [skills/github-automation/scripts/lint.sh](skills/github-automation/scripts/lint.sh)
Symbols: none
Satisfies: REQ-002
Action: Delete the duplicate bash script lint linter.
Validate: `git status` should show the file deleted.
Expected result: The file is removed.

### TASK-003: Update references to lint.sh to lint.py

Depends on: TASK-002
Files: [skills/github-automation/references/troubleshooting.md](skills/github-automation/references/troubleshooting.md), [skills/github-automation/evals/evals.json](skills/github-automation/evals/evals.json)
Symbols: none
Satisfies: REQ-003
Action: Replace all instances of `lint.sh` with `lint.py` in documentation and evaluation files.
Validate: Run `git diff` to verify the text replacements.
Expected result: Documentation and evaluations correctly point to `lint.py`.

### TASK-004: Inline YAML parser in validate-plugin.mjs and delete validate_yaml.py

Depends on: TASK-003
Files: [bin/validate-plugin.mjs](bin/validate-plugin.mjs), [bin/validate_yaml.py](bin/validate_yaml.py)
Symbols: [validateFrontmatter](bin/validate-plugin.mjs), [getPythonPath](bin/validate-plugin.mjs)
Satisfies: REQ-004
Action: Implement a simple string-based YAML frontmatter parser in JS inside `validate-plugin.mjs`, delete `getPythonPath`, and delete the `validate_yaml.py` helper script.
Validate: Run `node bin/validate-plugin.mjs` and `npm run test:node` to verify validation still passes.
Expected result: Validation works perfectly without needing python/PyYAML to parse YAML.

### TASK-005: Remove agents folder validation from validate-plugin.mjs

Depends on: TASK-004
Files: [bin/validate-plugin.mjs](bin/validate-plugin.mjs)
Symbols: [main](bin/validate-plugin.mjs)
Satisfies: REQ-005
Action: Remove the validation block for the `agents` folder since custom agents are not permitted by project key conventions.
Validate: Run `npm run validate` to ensure plugin validation passes.
Expected result: The validation runs successfully.

## PHASE-END: Acceptance

### TASK-006: Final acceptance verification

Depends on: TASK-005
Files: none
Symbols: none
Satisfies: none
Action: Run all lint, formatting, and unit tests to ensure the workspace is in a green and validated state.
Validate: `npm test` and `npm run validate`
Expected result: All tests, linting, formatting, and validations pass successfully with exit code 0.

