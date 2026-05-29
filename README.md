# Agent Dev Plugin

A Claude Code plugin for authoring and maintaining agents, skills, and hooks.

## What's included

| Component | Count    | Purpose                                                                           |
| --------- | -------- | --------------------------------------------------------------------------------- |
| Skills    | 20       | Process + domain skills (brainstorming, TDD, diagnose, refactor, …)               |
| Agents    | 2        | `coder` (autonomous execution), `explorer` (read-only research)                   |
| Commands  | 7        | `/plan`, `/new`, `/eval`, `/check`, `/deliver`, `/code-review`, `/welcome`        |
| Hooks     | 6 events | Auto-format, syntax check, debug artifact scan, brainstorm nudge, session context |
| MCP       | 1 server | Context7 for live library documentation                                           |

## Quick start

```text
/welcome
```

Run `/check all` to verify plugin health, then `/plan [description]` to start building.

## Key workflows

- **Planning**: `/plan` → brainstorm → spec → implementation plan
- **Building**: `/new skill|agent|hook [name]` to scaffold components
- **Evaluating**: `/eval create [name]` → `/eval run [name]`
- **Delivering**: `/deliver` to validate and commit

## Hook architecture

All hooks route through `hooks/runner.mjs` as `runner.mjs <domain> <action>`, which dynamically imports `hooks/handlers/<domain>.mjs` and calls the exported `<action>` function. Telemetry is written to `.claude/telemetry.log`.

See [AGENTS.md](AGENTS.md) for layout, conventions, and debugging.
