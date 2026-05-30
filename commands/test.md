---
description: Run the plugin test suite — Node.js unit tests, Python tests, or integration tests.
argument-hint: [all|node|python|integration]
---

# Test: $ARGUMENTS

Run the plugin test suite for scope: `$ARGUMENTS`

**Default (no args):** runs `all`.

## Scopes

| Scope           | Command                          | Covers                                              |
| --------------- | -------------------------------- | --------------------------------------------------- |
| `all` (default) | `npm test`                       | Node.js unit tests + Python tests                   |
| `node`          | `npm run test:node`              | Hook handler unit tests (`node --test`)             |
| `python`        | `npm run test:python`            | Skill scripts and agent-dev scripts (`pytest`)      |
| `integration`   | `npm run test:integration`       | Hooks fire + skills load end-to-end                 |

Run the command for the requested scope. If tests fail:

1. Show the failing test name and error message
2. Identify whether the failure is pre-existing or caused by recent changes (`git stash` to check)
3. If caused by recent changes, invoke the `diagnose` skill to find the root cause before attempting a fix

---

<!-- Usage: /test -->
<!-- Usage: /test node -->
<!-- Usage: /test python -->
<!-- Usage: /test integration -->
