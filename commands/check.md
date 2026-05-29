---
description: Run plugin health checks — structure, skills, agents, hooks, and manifest validation.
argument-hint: [all|structure|skills|agents|hooks|manifest|validate]
---

# Check — Plugin Health Scan

Run targeted plugin health checks on the current workspace.

**Mode format:** `$ARGUMENTS` = `[mode]`
**Default (no args):** runs `all` checks

## Health Check Pipeline

| Mode            | Command                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------- |
| `all` (default) | `python skills/agents-maintainer/scripts/run.py check-all` then `claude plugin validate --strict` |
| `structure`     | `python skills/agents-maintainer/scripts/run.py scan-structure`                                   |
| `skills`        | `python skills/agents-maintainer/scripts/run.py validate-skills`                                  |
| `agents`        | `python skills/agents-maintainer/scripts/run.py lint-agents-md`                                   |
| `hooks`         | `python skills/agents-maintainer/scripts/run.py check-hooks`                                      |
| `manifest`      | `python skills/agents-maintainer/scripts/run.py check-manifest`                                   |
| `validate`      | `claude plugin validate --strict` (official CLI manifest + frontmatter validation)                |

When running `all`, always run `claude plugin validate --strict` last. Any warnings reported by the CLI validator (typo'd field names, unsupported agent frontmatter keys, etc.) should be treated as errors before delivery.

If Python is not found or dependencies are missing, ensure the virtual environment is active:

```bash
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```
