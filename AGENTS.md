# Agent Instructions

Claude Code plugin workspace for authoring and maintaining skills, hooks, and agents.

## Layout

| Path                         | Purpose                                                     |
| ---------------------------- | ----------------------------------------------------------- |
| `skills/<name>/SKILL.md`     | Skill definition (frontmatter + body)                       |
| `skills/<name>/references/`  | Reference docs loaded on demand by the skill                |
| `skills/<name>/scripts/`     | Helper scripts used by the skill                            |
| `hooks/hooks.json`           | Hook configuration for this plugin                          |
| `hooks/runner.mjs`           | Entry point that dispatches to handlers                     |
| `hooks/utils.mjs`            | Shared utilities for hook handlers                          |
| `hooks/handlers/`            | Per-event handler modules (format, session, diagnose, etc.) |
| `.claude-plugin/plugin.json` | Plugin manifest (name, version, hooks path)                 |
| `.simulate/`                 | Local hook simulation harness for testing                   |
| `agents/`                    | Managed Agent definitions (coder.md, explorer.md)           |

## Skill Conventions

- Every skill starts with YAML frontmatter: `name`, `description` (required); `disable-model-invocation` is optional
- `description` is what triggers the skill — write it as a precise trigger list, not marketing copy
- Heavy reference content goes in `references/` and loads only when needed (progressive disclosure)
- Scripts in `scripts/` are invoked by the skill body — verify they exist before referencing them

## Hook Conventions

- Hooks are registered in `hooks/hooks.json` under event names (`SessionStart`, `PreToolUse`, etc.)
- Each hook entry: `type` (`command` or `prompt`), `command`, optional `timeout`
- Hook logic lives in `hooks/handlers/` as ES modules; each module exports named action functions
- All handlers are dispatched via `hooks/runner.mjs`; shared helpers go in `hooks/utils.mjs`
- Prefer `command` hooks for deterministic checks; use `prompt` hooks only when reasoning is needed
- Session-start hooks run on every conversation — keep them fast (< 10s)

## File-Scoped Checks

No build toolchain. Validate skills manually:

| Task           | Command                                                                         |
| -------------- | ------------------------------------------------------------------------------- |
| Lint AGENTS.md | `python skills/agents-maintainer/scripts/run.py lint-agents-md AGENTS.md`       |
| Scan structure | `python skills/agents-maintainer/scripts/run.py scan-structure . --max-depth 2` |

## Hook Debugging

Set `CLAUDE_HOOKS_DEBUG=1` in the environment to surface hook errors to stderr during development:

```bash
CLAUDE_HOOKS_DEBUG=1 node hooks/runner.mjs session context
```

The `Stop` hook scans `git diff HEAD` for debug artifacts. To intentionally keep a debug statement, append `// debug-keep` (JS) or `# debug-keep` (Python/Ruby) to the line:

```js
console.log('auth flow trace', user.id); // debug-keep
```

## Local Hook Testing

The `.simulate/` directory contains a harness for recording real hook inputs during a test session.

| Task                    | Command                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------ |
| Run simulation          | `python skills/agent-development/scripts/simulate.py --config .simulate/hooks-config.json` |
| Inspect recorded events | Open `.simulate/<run-id>/tool-calls.jsonl` — one JSON object per hook call                 |

Use this to capture realistic inputs before writing unit tests for a new handler.

## Commit Attribution

AI commits MUST include a `Co-Authored-By:` trailer.
Example: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
