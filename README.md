# Agent Dev Plugin

[![License](https://img.shields.io/github/license/j0hanz/claude-agent-dev-plugin?style=for-the-badge)](https://github.com/j0hanz/claude-agent-dev-plugin/blob/master/LICENSE) [![Latest release](https://img.shields.io/github/v/release/j0hanz/claude-agent-dev-plugin?style=for-the-badge&include_prereleases&sort=semver)](https://github.com/j0hanz/claude-agent-dev-plugin/releases) [![Node.js](https://img.shields.io/badge/node-%3E%3D22-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org) [![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org) [![GitHub stars](https://img.shields.io/github/stars/j0hanz/claude-agent-dev-plugin?style=for-the-badge&logo=github)](https://github.com/j0hanz/claude-agent-dev-plugin/stargazers)

A Claude Code plugin for authoring and maintaining agents, skills, and hooks — structured workflows, managed subagents, and lifecycle hooks that guide Claude through the full agent development lifecycle.

## Overview

Agent Dev Plugin extends Claude Code with 14 skills, 4 managed subagents, and 8 lifecycle hooks covering the complete agent development cycle. Skills activate automatically based on task context and can also be invoked manually; hooks fire on every session event to keep development disciplined; agents handle specialized tasks in scoped, isolated environments.

| Aspect              | Detail                       |
| :------------------ | :--------------------------- |
| **Status**          | Stable — v1.0.0              |
| **Language**        | JavaScript (ESM) · Python    |
| **Runtime**         | Node.js ≥ 22 · Python ≥ 3.10 |
| **Package manager** | npm                          |
| **License**         | MIT                          |

## Highlights

| Feature                  | Description                                                         |
| :----------------------- | :------------------------------------------------------------------ |
| 14 auto-triggered skills | Activate on task context; invoke manually with `/skill-name`        |
| 4 specialized subagents  | Scoped tool access — executor, debugger, documenter, researcher     |
| 8 lifecycle hooks        | Fire on session events to enforce workflow discipline automatically |
| Marketplace install      | One-command install from GitHub — no manual clone required          |

## Installation

### Via Marketplace

> [!TIP]
> Marketplace install is recommended — upgrades are handled automatically.

1. Add the marketplace to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-agent-dev": {
      "source": {
        "source": "github",
        "repo": "j0hanz/claude-agent-dev-plugin"
      }
    }
  }
}
```

1. Install the plugin:

```bash
claude plugin install claude-agent-dev@claude-agent-dev
```

### Manual

```bash
git clone https://github.com/j0hanz/claude-agent-dev-plugin.git
claude --plugin-dir ./claude-agent-dev-plugin
```

## Prerequisites

| Requirement     | Version / Notes                        |
| :-------------- | :------------------------------------- |
| Node.js         | ≥ 22                                   |
| Python          | ≥ 3.10                                 |
| Claude Code     | latest                                 |
| Python packages | `pip install pytest pyyaml jsonschema` |

## What's Included

### Skills (14)

Skills are invoked automatically by Claude based on task context, or manually with `/skill-name`.

| Skill                            | Trigger                                                    | Purpose                                                        |
| :------------------------------- | :--------------------------------------------------------- | :------------------------------------------------------------- |
| `brainstorming`                  | "let's build", "add a feature", "I want to implement"      | Requirements discovery before implementation — prevents rework |
| `planning`                       | "plan", "design", "how should we approach"                 | Implementation planning and design decisions                   |
| `create-agent`                   | "build agent", "create subagent", "agent prompt"           | Scaffold, write, and test agents                               |
| `create-hook`                    | "create hook", "add hook", "hook for X"                    | Design and test lifecycle hooks                                |
| `skill-builder`                  | "make skill", "build skill", "run evals"                   | Create, test, and optimize skills                              |
| `diagnose`                       | "debug", "fix crash", "not working", "why is this failing" | Root-cause debugging before any fix                            |
| `code-review`                    | "review", "check this", "is this correct"                  | Quality gate — correctness and simplification                  |
| `refactor`                       | "clean up", "refactor", "simplify", "messy"                | Structural improvements                                        |
| `test-driven-development`        | "TDD", "write tests", "implement this"                     | Red-green-refactor workflow                                    |
| `architecture`                   | "architecture", "structure", "how is this organized"       | Codebase structural analysis                                   |
| `github-automation`              | "GitHub Actions", "gh CLI", "automate workflow"            | Actions and `gh` CLI scripting                                 |
| `verification-before-completion` | (automatic before task completion)                         | Verify changes work before marking done                        |
| `using-agent-dev-skills`         | (meta-routing)                                             | Routes to the right skill based on context                     |
| `agents-maintainer`              | "update AGENTS.md", "update CLAUDE.md"                     | Authoring AGENTS.md and CLAUDE.md files                        |

### Agents (4)

Specialized subagents Claude can invoke automatically or you can request directly.

| Agent        | Role                                                                        | Tools                                                 |
| :----------- | :-------------------------------------------------------------------------- | :---------------------------------------------------- |
| `coder`      | Autonomous code executor — implements, refactors, runs tests                | Bash, Read, Write, Edit, Glob, Grep, Skill, TodoWrite |
| `detective`  | Debugging specialist — root-cause analysis, proposes fixes without applying | Read, Glob, Grep, Skill, TodoWrite                    |
| `documenter` | Documentation maintainer — audits, writes, syncs docs with code             | Read, Write, Edit, Glob, Grep, Skill                  |
| `explorer`   | Research agent — finds files, symbols, and external docs                    | Read, Glob, Grep, context7 docs                       |

> [!NOTE]
> `coder` runs in an isolated git worktree. `explorer` and `detective` are strictly read-only.

### Hooks

Lifecycle hooks fire automatically during every Claude Code session.

| Event                                            | Handler                   | What it does                                                   |
| :----------------------------------------------- | :------------------------ | :------------------------------------------------------------- |
| `SessionStart`                                   | session, explorer, skills | Injects session context, explorer history, and skill list      |
| `UserPromptSubmit`                               | brainstorm-nudge          | Encourages requirements discovery before implementation starts |
| `PreToolUse` (Grep/Glob/Read/WebFetch/WebSearch) | explorer                  | Logs search breadcrumbs for context replay                     |
| `PostToolUse` (Write/Edit/MultiEdit)             | format                    | Runs Prettier on every saved file                              |
| `PostToolUse` (Write/Edit/MultiEdit)             | debug                     | Scans for new issues after each change                         |
| `PostToolUseFailure` (Bash)                      | diagnose-nudge            | Prompts structured debugging when a command fails              |
| `Stop`                                           | debug                     | Final scan before Claude stops                                 |
| `SessionEnd`                                     | explorer                  | Flushes explorer history to disk                               |

### MCP Server

[context7](https://context7.com) is bundled and available to the `explorer` agent for live library documentation lookups.

## Project Structure

```text
.
├── agents/                 # Subagent definitions and eval suites
├── bin/                    # Validation scripts
├── hooks/                  # Hook runner and handlers
│   ├── handlers/
│   ├── hooks.json
│   ├── runner.mjs
│   └── utils.mjs
├── monitors/               # Live development watchers (experimental)
├── output-styles/          # Output style definitions
├── skills/                 # Skill SKILL.md files (14 skills)
└── tests/                  # Integration tests
```

| Directory   | Purpose                                                          |
| :---------- | :--------------------------------------------------------------- |
| `agents/`   | Markdown prompt files and eval suites for each subagent          |
| `hooks/`    | Hook runner, event handlers, and the hooks manifest              |
| `skills/`   | One directory per skill, each containing a `SKILL.md` definition |
| `monitors/` | Experimental live watchers for tests and telemetry               |
| `bin/`      | Plugin manifest validator and YAML schema checker                |
| `tests/`    | Integration tests verifying hooks fire and skills load correctly |

## Scripts

| Command                    | Description                                     |
| :------------------------- | :---------------------------------------------- |
| `npm run validate`         | Validate the plugin manifest                    |
| `npm test`                 | Validate, then run all Node.js and Python tests |
| `npm run test:node`        | Run Node.js unit tests only                     |
| `npm run test:python`      | Run Python unit tests only                      |
| `npm run test:integration` | Run integration tests                           |
| `npm run lint`             | Lint with ESLint                                |
| `npm run lint:fix`         | Lint and auto-fix with ESLint                   |
| `npm run format`           | Format all files with Prettier                  |
| `npm run format:check`     | Check formatting without writing changes        |

## Contributing

1. Fork the repository.
2. Create a feature branch — `git checkout -b feat/your-feature`.
3. Make your changes and run the full test suite: `npm test`.
4. Lint and format: `npm run lint && npm run format`.
5. Open a pull request against `master`.

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.

---

[Back to top](#agent-dev-plugin)
