# Agent SDLC Plugin

[![License](https://img.shields.io/github/license/j0hanz/agent-sdlc?style=for-the-badge)](https://github.com/j0hanz/agent-sdlc/blob/master/LICENSE) [![Latest release](https://img.shields.io/github/v/release/j0hanz/agent-sdlc?style=for-the-badge&include_prereleases&sort=semver)](https://github.com/j0hanz/agent-sdlc/releases) [![Node.js](https://img.shields.io/badge/node-%3E%3D22-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org) [![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org) [![GitHub stars](https://img.shields.io/github/stars/j0hanz/agent-sdlc?style=for-the-badge&logo=github)](https://github.com/j0hanz/agent-sdlc/stargazers)

A Claude Code plugin for authoring and maintaining skills and hooks — structured workflows and lifecycle hooks that guide Claude through the full agent development lifecycle.

## Overview

Agent SDLC Plugin extends Claude Code with 15 skills and 2 lifecycle hooks covering the complete agent development cycle. Skills activate automatically based on task context and can also be invoked manually; hooks fire on session events to guard against destructive commands and surface relevant skills. Multi-step or parallel work is delegated to specialized, safe-by-default subagents (`implementer`, `researcher`, `conflict-resolver`, etc.) orchestrated by the `multi-agent-dispatch` (parallel fan-out) and `multi-agent-development` (sequential, gate-checked) skills.

| Aspect              | Detail                       |
| :------------------ | :--------------------------- |
| **Status**          | Stable — v1.0.0              |
| **Language**        | JavaScript (ESM) · Python    |
| **Runtime**         | Node.js ≥ 22 · Python ≥ 3.10 |
| **Package manager** | npm                          |
| **License**         | MIT                          |

## Highlights

| Feature                  | Description                                                                                                                                                  |
| :----------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 15 auto-triggered skills | Activate on task context; invoke manually with `/skill-name`                                                                                                 |
| Subagent orchestration   | `multi-agent-dispatch` and `multi-agent-development` drive subagent dispatches using specialized, safe-by-default agents (`implementer`, `researcher`, etc.) |
| 2 lifecycle hooks        | Bash-only handlers: a shell-safety guard and a skill nudge                                                                                                   |
| Marketplace install      | One-command install from GitHub — no manual clone required                                                                                                   |

## Installation

### Via Marketplace

> [!TIP]
> Marketplace install is recommended — upgrades are handled automatically.

1. Add the marketplace to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-agent-sdlc": {
      "source": {
        "source": "github",
        "repo": "j0hanz/agent-sdlc"
      }
    }
  }
}
```

1. Install the plugin:

```bash
claude plugin install claude-agent-sdlc@claude-agent-sdlc
```

### Manual

```bash
git clone https://github.com/j0hanz/agent-sdlc.git
claude --plugin-dir ./agent-sdlc
```

## Prerequisites

| Requirement     | Version / Notes           |
| :-------------- | :------------------------ |
| Node.js         | ≥ 22                      |
| Python          | ≥ 3.10                    |
| Claude Code     | latest                    |
| Python packages | `pip install -e ".[dev]"` |

## What's Included

### Skills (16)

Skills are invoked automatically by Claude based on task context, or manually with `/skill-name`. 14 are listed below; `multi-agent-dispatch` and `multi-agent-development` are detailed in [Subagent Dispatch](#subagent-dispatch).

| Skill                            | Trigger                                                    | Purpose                                                        |
| :------------------------------- | :--------------------------------------------------------- | :------------------------------------------------------------- |
| `parallel-brainstorming`         | "brainstorm", "add a feature", "explore approaches"        | Parallel multi-agent ideation + critique before implementation |
| `request-plan`                   | "plan", "design", "draft a plan", "write a spec"           | Multi-agent ideate-and-synthesize: drafts plan/specs.md        |
| `receive-plan`                   | "check my plan", "is this plan ready", "verify this spec"  | Multi-agent critique panel + Traceability Auditor gate         |
| `diagnose`                       | "debug", "fix crash", "not working", "why is this failing" | Root-cause debugging before any fix                            |
| `request-code-review`            | "review", "check this", "is this correct"                  | Dispatches a fresh-context subagent to review the diff         |
| `receive-code-review`            | "reviewer said", "PR comments"                             | Verify, push back on, and implement review feedback            |
| `test-driven-development`        | "TDD", "write tests", "implement this"                     | Red-green-refactor workflow                                    |
| `architecting`                   | "architecture", "structure", "how is this organized"       | Codebase structural analysis                                   |
| `pr-workflow`                    | "commit this", "open a PR", "ship it", "push my work"      | Branch, commit, push & open a PR — multi-agent aware delivery  |
| `gh-actions`                     | "GitHub Actions", "gh CLI", "harden a workflow", "OIDC"    | Secure CI/CD authoring and `gh` CLI scripting                  |
| `context-optimizer`              | "optimize context", "compress context", "reduce tokens"    | Prunes conversation bloat before hitting context limits        |
| `verification-before-completion` | (automatic before task completion)                         | Verify changes work before marking done                        |
| `using-agent-sdlc-skills`        | (meta-routing)                                             | Routes to the right skill based on context                     |
| `project-init`                   | "init project", "generate AGENTS.md", "onboard repo"       | Parallel discovery fan-out → lean AGENTS.md + stubs            |

### Subagent Dispatch

This plugin defines custom agents in the `agents/` directory covering specialized roles: `implementer` (code writer), `researcher` (read-only investigator/explorer), `conflict-resolver` (merge conflict resolution), `spec-reviewer`, `quality-reviewer`, and `diff-reviewer`. Three skills orchestrate these:

| Skill                     | Pattern                                                                                       |
| :------------------------ | :-------------------------------------------------------------------------------------------- |
| `multi-agent-dispatch`    | Parallel fan-out — one `researcher` or `implementer` agent per independent domain, one batch  |
| `multi-agent-development` | Sequential — one `implementer` per plan task, gated by `spec-reviewer` and `quality-reviewer` |
| `request-code-review`     | Read-only — one fresh-context `diff-reviewer` per diff, no memory of the implementation       |

> [!NOTE]
> Read-only roles (researcher, reviewers) utilize the specialized `researcher` and `*-reviewer` agents which enforce hard tool restrictions (Write/Edit tools are disabled) at the harness level. Implementer and conflict-resolver roles run in an isolated git worktree (`isolation: "worktree"`).

### Hooks

Bash-only handlers (`hooks/*.sh`), wired in `hooks/hooks.json`. `shell-safety` is the only blocking hook — everything else is additive (warns or injects context, never blocks).

| Event                 | Handler        | What it does                                                                                                                                                           | Blocking? |
| :-------------------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------- |
| `PreToolUse` (`Bash`) | `shell-safety` | Rejects a small, explicit denylist of catastrophic commands (`rm -rf /`, force-push to main/master, `git clean -fdx`). Override with `AGENT_SDLC_SKIP_SHELL_SAFETY=1`. | Yes       |
| `SessionStart` (`*`)  | `skill-nudge`  | Points toward this plugin's bundled skills, at most once per 24h. Opt out with `AGENT_SDLC_SKILL_NUDGE=0`.                                                             | No        |

`shell-safety.sh` is self-contained (no shared-library dependency) so a bug in `hooks/lib.sh` can never silently disable the one blocking guard. The denylist is intentionally narrow and documented as best-effort, not comprehensive protection.

### Configuration

You can configure project-local behaviors for the `claude-agent-sdlc` plugin by creating a settings file at `.claude/claude-agent-sdlc.local.md` in the root of your project:

```markdown
---
# Set to true to disable the shell safety check (use with caution)
skip_shell_safety: false

# Set to false to disable the periodic skill nudge on session start
skill_nudge: true
---

# claude-agent-sdlc Configuration

This file configures local settings for the `claude-agent-sdlc` plugin.
```

> [!IMPORTANT]
> Since hooks are loaded at session startup, any changes to this file will take effect on the next Claude Code session (requires restart). Remember to add `.claude/*.local.md` to your `.gitignore`.

## Project Structure

```text
.
├── bin/                    # Validation and release scripts
├── hooks/                  # Hook manifest and bash handlers
│   ├── lib.sh
│   ├── shell-safety.sh
│   ├── skill-nudge.sh
│   └── hooks.json
├── output-styles/          # Output style definitions
├── skills/                 # Skill SKILL.md files (15 skills)
└── tests/                  # Integration tests
```

| Directory        | Purpose                                                          |
| :--------------- | :--------------------------------------------------------------- |
| `hooks/`         | Bash hook handlers and the hooks manifest                        |
| `skills/`        | One directory per skill, each containing a `SKILL.md` definition |
| `output-styles/` | Output style definitions                                         |
| `bin/`           | Manifest validator and release scripts                           |
| `tests/`         | Integration tests verifying hooks fire and skills load correctly |

## Scripts

| Command                    | Description                                     |
| :------------------------- | :---------------------------------------------- |
| `npm run validate`         | Validate the plugin manifest                    |
| `npm test`                 | Validate, then run all Node.js and Python tests |
| `npm run test:node`        | Run Node.js unit tests only                     |
| `npm run test:python`      | Run Python unit tests only                      |
| `npm run test:integration` | Run integration tests                           |
| `npm run test:eval`        | Run skill-triggering evals for selected skills  |
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

[Back to top](#agent-sdlc-plugin)
