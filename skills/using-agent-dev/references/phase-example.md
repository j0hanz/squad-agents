# Phase Discipline: Worked Example

Here's how the `/lint` command flows through all four phases:

**Design Phase Output:**

| Component       | Trigger                               | Approach                                                    |
| --------------- | ------------------------------------- | ----------------------------------------------------------- |
| `/lint` command | User says "lint" or "validate plugin" | New slash command that validates plugin.json against schema |

**Build Phase Intent:**
"Creating validation logic for plugin.json schema and integration with `/check` command"

**Validate Phase Triple:**

- Component: `/lint` command validation
- Rule: Must validate plugin.json structure, required fields, semver format
- Evidence: Tests pass for valid and invalid plugin.json files

**Ship Phase Artifacts:**

- `commands/lint.md` (command definition)
- `bin/lint-plugin.mjs` (implementation)
- `tests/integration/test-lint.mjs` (test suite)
