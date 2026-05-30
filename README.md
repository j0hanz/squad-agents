# Agent Dev Plugin

[![Node.js](https://img.shields.io/badge/node-%3E%3D22-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org) [![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org) [![JavaScript](https://img.shields.io/badge/JavaScript-ESM-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

A Claude Code plugin for authoring and maintaining agents, skills, and hooks.

## Overview

Agent Dev is a Claude Code plugin that provides process skills, managed agents, slash commands, and lifecycle hooks for building AI-assisted development workflows. It scaffolds components, validates output, and auto-formats code as you author Claude agents, skills, and hooks.

| Aspect       | Detail                     |
| :----------- | :------------------------- |
| **Runtime**  | Node.js ≥22 · Python ≥3.10 |
| **Language** | JavaScript (ESM) · Python  |
| **Package**  | npm                        |
| **Tests**    | `node --test` · `pytest`   |

## Highlights

| Component | Count | Purpose                                                                                                                 |
| :-------- | :---: | :---------------------------------------------------------------------------------------------------------------------- |
| Skills    |  19   | Process + domain skills (brainstorming, TDD, diagnose, refactor, …)                                                     |
| Agents    |   2   | `coder` (autonomous execution) · `explorer` (read-only research)                                                        |
| Commands  |  11   | `/plan`, `/new`, `/eval`, `/check`, `/deliver`, `/artifact-review`, `/debug`, `/test`, `/refactor`, `/docs`, `/welcome` |
| Hooks     |  15   | Lifecycle events covering format, nudge, session context, and debug scan                                                |
| MCP       |   1   | Context7 for live library documentation                                                                                 |

## Quick Start

> [!TIP]
> Requires Node.js ≥22 and Python ≥3.10.

```bash
npm install
pip install pytest pyyaml jsonschema
```

Then open Claude Code and run:

```text
/welcome
```

This confirms the plugin loaded and walks you through each component. Run `/check all` to validate plugin health at any time.

## Usage

All plugin capabilities are exposed as slash commands inside Claude Code.

| Command            | Purpose                                                       |
| :----------------- | :------------------------------------------------------------ |
| `/welcome`         | Plugin orientation and component overview                     |
| `/plan`            | Brainstorm → spec → implementation plan                       |
| `/new`             | Scaffold a skill, agent, or hook from a template              |
| `/eval`            | Create and run evaluation suites for agents                   |
| `/check`           | Validate plugin health (components, hooks, structure)         |
| `/deliver`         | Validate, commit with attribution, and open a PR              |
| `/artifact-review` | Audit or refine skills, agents, plans, and hooks              |
| `/debug`           | Debug a problem using the structured diagnose methodology     |
| `/test`            | Run the plugin test suite (node, python, integration, or all) |
| `/refactor`        | Clean up code without changing behavior                       |
| `/docs`            | Create or update AGENTS.md, CLAUDE.md, README, or skill docs  |

## Project Structure

```text
agents/             — Agent definitions (coder.md, explorer.md) + eval suites
bin/                — CLI utilities: simulate, telemetry, validate
commands/           — Slash command markdown definitions
hooks/
  handlers/         — Per-event handler modules (ES modules)
  config/           — Hook configuration files
  hooks.json        — Event-to-handler registration
  runner.mjs        — Central dispatcher: runner.mjs <domain> <action>
  utils.mjs         — Shared hook utilities
monitors/           — Monitor definitions
output-styles/      — Output formatting rules
skills/             — 19 skill definitions, each in skills/<name>/
tests/              — Integration tests (hooks fire, skills load)
AGENTS.md           — Layout, conventions, and debugging guide
```

| Path               | Purpose                                                        |
| :----------------- | :------------------------------------------------------------- |
| `agents/`          | Agent markdown definitions and evaluation case YAML files      |
| `commands/`        | Slash command markdown definitions loaded by Claude Code       |
| `hooks/runner.mjs` | Entry point — dispatches each event to `handlers/<domain>.mjs` |
| `skills/<name>/`   | Skill definition, reference docs, and helper scripts           |

## Hook Architecture

Hooks route through `hooks/runner.mjs` as `runner.mjs <domain> <action>`, which dynamically imports `hooks/handlers/<domain>.mjs` and calls the exported `<action>` function. Telemetry is written to `.claude/telemetry.log`.

| Event                 | Handler domain        | Purpose                                        |
| :-------------------- | :-------------------- | :--------------------------------------------- |
| `SessionStart`        | `session`, `explorer` | Load context; inject session variables         |
| `PreToolUse`          | `explorer`            | Pre-fetch URLs; enrich Glob/Grep context       |
| `PostToolUse`         | `format`              | Auto-format files on Write/Edit                |
| `UserPromptSubmit`    | `brainstorm-nudge`    | Nudge toward brainstorming on creative tasks   |
| `PostToolUseFailure`  | `diagnose-nudge`      | Surface the debugging skill on Bash failure    |
| `Stop` / `SessionEnd` | `debug`, `explorer`   | Scan for debug artifacts; flush explorer state |

See [AGENTS.md](AGENTS.md) for the full event list, hook debugging, and `CLAUDE_HOOKS_DEBUG=1` usage.

## Scripts

| Command                    | Description                                 |
| :------------------------- | :------------------------------------------ |
| `npm test`                 | Run Node.js and Python test suites          |
| `npm run test:node`        | Node.js unit tests (`node --test`)          |
| `npm run test:python`      | Python tests (`pytest`)                     |
| `npm run test:integration` | Integration tests (hooks fire, skills load) |
| `npm run lint`             | Lint with ESLint                            |
| `npm run lint:fix`         | Lint and auto-fix                           |
| `npm run format`           | Format with Prettier                        |
| `npm run format:check`     | Check formatting without writing            |

## Contributing

1. Clone the repo and install dependencies: `npm install && pip install pytest pyyaml jsonschema`
2. Open in Claude Code and run `/welcome` to confirm the plugin loads.
3. Create a feature branch: `git checkout -b feat/<name>`
4. Scaffold new components with `/new skill|agent|hook <name>` or edit directly.
5. Validate with `npm test` and `/check all`.
6. Commit with a `Co-Authored-By:` trailer (required — see [AGENTS.md](AGENTS.md)).
7. Open a pull request.

---

[Back to top](#agent-dev-plugin)
