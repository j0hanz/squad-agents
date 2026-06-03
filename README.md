# Agent Dev Plugin

[![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge)](CHANGELOG.md)
[![Node.js](https://img.shields.io/badge/node-%3E%3D22-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

A Claude Code plugin for authoring and maintaining agents, skills, and hooks. Provides structured workflows, managed subagents, and lifecycle hooks that guide Claude through the full agent development cycle — from requirements discovery to testing and validation.

---

## Installation

### Via marketplace (recommended)

**Step 1:** Add the marketplace to your Claude Code project settings (`.claude/settings.json`):

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

**Step 2:** Install the plugin:

```bash
claude plugin install claude-agent-dev@claude-agent-dev
```

### Manual (load for one session)

```bash
git clone https://github.com/j0hanz/claude-agent-dev-plugin.git
claude --plugin-dir ./claude-agent-dev-plugin
```

### Prerequisites

- Node.js ≥ 22
- Python ≥ 3.10
- `pip install pytest pyyaml jsonschema`

---

## What's included

### Skills (14)

Skills are invoked automatically by Claude based on task context, or manually with `/skill-name`.

| Skill | Trigger | Purpose |
| --- | --- | --- |
| `brainstorming` | "let's build", "add a feature", "I want to implement" | Requirements discovery before implementation — prevents rework |
| `planning` | "plan", "design", "how should we approach" | Implementation planning and design decisions |
| `create-agent` | "build agent", "create subagent", "agent prompt" | Scaffold, write, and test agents |
| `create-hook` | "create hook", "add hook", "hook for X" | Design and test lifecycle hooks |
| `skill-builder` | "make skill", "build skill", "run evals" | Create, test, and optimize skills |
| `diagnose` | "debug", "fix crash", "not working", "why is this failing" | Root-cause debugging before any fix |
| `code-review` | "review", "check this", "is this correct" | Quality gate — correctness and simplification |
| `refactor` | "clean up", "refactor", "simplify", "messy" | Structural improvements |
| `test-driven-development` | "TDD", "write tests", "implement this" | Red-green-refactor workflow |
| `architecture` | "architecture", "structure", "how is this organized" | Codebase structural analysis |
| `github-automation` | "GitHub Actions", "gh CLI", "automate workflow" | Actions and `gh` CLI scripting |
| `verification-before-completion` | (automatic before task completion) | Verify changes work before marking done |
| `using-agent-dev-skills` | (meta-routing) | Routes to the right skill based on context |
| `agents-maintainer` | "update AGENTS.md", "update CLAUDE.md" | Authoring AGENTS.md and CLAUDE.md files |

### Agents (4)

Specialized subagents Claude can invoke automatically or you can request directly.

| Agent | Role | Tools |
| --- | --- | --- |
| `coder` | Autonomous code executor — implements, refactors, runs tests | Bash, Read, Write, Edit, Glob, Grep, Skill, TodoWrite |
| `detective` | Debugging specialist — root-cause analysis, proposes fixes without applying | Read, Glob, Grep, Skill, TodoWrite (read-only) |
| `documenter` | Documentation maintainer — audits, writes, syncs docs with code | Read, Write, Edit, Glob, Grep, Skill |
| `explorer` | Research agent — finds files, symbols, and external docs | Read, Glob, Grep, context7 docs (read-only) |

> `coder` runs in an isolated git worktree. `explorer` and `detective` are strictly read-only.

### Hooks

Lifecycle hooks fire automatically during every Claude Code session.

| Event | Handler | What it does |
| --- | --- | --- |
| `SessionStart` | session, explorer, skills | Injects session context, explorer history, and skill list |
| `UserPromptSubmit` | brainstorm-nudge | Encourages requirements discovery before implementation starts |
| `PreToolUse` (Grep/Glob/Read) | explorer | Logs search breadcrumbs for context replay |
| `PostToolUse` (Write/Edit) | format | Runs Prettier on every saved file |
| `PostToolUse` (Write/Edit/Bash) | debug | Scans for new issues after each change |
| `PostToolUseFailure` (Bash) | diagnose-nudge | Prompts structured debugging when a command fails |
| `Stop` | debug | Final scan before Claude stops |
| `SessionEnd` | explorer | Flushes explorer history to disk |

### MCP server

[context7](https://context7.com) is bundled and available to the `explorer` agent for live library documentation lookups.

---

## Development

```bash
# Install dev dependencies
npm install
pip install pytest pyyaml jsonschema

# Validate plugin manifest
npm run validate

# Run all tests
npm test

# Run only Node.js tests
npm run test:node

# Run only Python tests
npm run test:python

# Run integration tests
npm run test:integration

# Lint and format
npm run lint
npm run format
```

### Project structure

```text
.
├── .claude-plugin/         # Plugin manifest
│   ├── plugin.json
│   └── marketplace.json
├── agents/                 # Subagent definitions
├── skills/                 # Skill SKILL.md files
├── hooks/                  # Hook runner and handlers
│   ├── hooks.json
│   ├── runner.mjs
│   ├── utils.mjs
│   └── handlers/
├── monitors/               # Live development watchers (experimental)
├── bin/                    # Validation scripts
└── tests/                  # Integration tests
```

---

## Requirements

| Runtime | Version |
| --- | --- |
| Node.js | ≥ 22 |
| Python | ≥ 3.10 |
| Claude Code | latest |

---

## License

MIT — see [LICENSE](LICENSE).
