# Squad Agents Plugin

[![License](https://img.shields.io/github/license/j0hanz/squad-agents?style=for-the-badge)](https://github.com/j0hanz/squad-agents/blob/master/LICENSE) [![Latest release](https://img.shields.io/github/v/release/j0hanz/squad-agents?style=for-the-badge&include_prereleases&sort=semver)](https://github.com/j0hanz/squad-agents/releases) [![Node.js](https://img.shields.io/badge/node-%3E%3D22-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org) [![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org) [![GitHub stars](https://img.shields.io/github/stars/j0hanz/squad-agents?style=for-the-badge&logo=github)](https://github.com/j0hanz/squad-agents/stargazers)

A Claude Code plugin for authoring and maintaining skills and hooks — structured workflows and lifecycle hooks that guide Claude through the full agent development lifecycle.

## Overview

Squad Agents Plugin extends Claude Code with 15 skills and 2 lifecycle hooks covering the complete agent development cycle. Skills activate automatically based on task context and can also be invoked manually; hooks fire on session events to guard against destructive commands and surface relevant skills. Multi-step or parallel work is delegated to subagents dispatched in specialized roles (`implementer`, `researcher`, `conflict-resolver`, etc.) by the `dispatch-agents` skill.

| Aspect              | Detail                       |
| :------------------ | :--------------------------- |
| **Status**          | Stable                       |
| **Language**        | JavaScript (ESM) · Python    |
| **Runtime**         | Node.js ≥ 22 · Python ≥ 3.10 |
| **Package manager** | npm                          |
| **License**         | MIT                          |

## Highlights

| Feature                  | Description                                                                                                                |
| :----------------------- | :------------------------------------------------------------------------------------------------------------------------- |
| 15 auto-triggered skills | Activate on task context; invoke manually with `/skill-name`                                                               |
| Subagent orchestration   | `dispatch-agents` drives subagent dispatches using specialized, safe-by-default agents (`implementer`, `researcher`, etc.) |
| 2 lifecycle hooks        | Bash-only handlers: a shell-safety guard and a skill nudge                                                                 |
| Marketplace install      | One-command install from GitHub — no manual clone required                                                                 |

## Installation

### Via Marketplace

> [!TIP]
> Marketplace install is recommended — upgrades are handled automatically.

1. Add the marketplace to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "squad-agents": {
      "source": {
        "source": "github",
        "repo": "j0hanz/squad-agents"
      }
    }
  }
}
```

1. Install the plugin:

```bash
claude plugin install squad-agents@squad-agents
```

### Manual

```bash
git clone https://github.com/j0hanz/squad-agents.git
claude --plugin-dir ./squad-agents
```

## Prerequisites

| Requirement     | Version / Notes           |
| :-------------- | :------------------------ |
| Node.js         | ≥ 22                      |
| Python          | ≥ 3.10                    |
| Claude Code     | latest                    |
| Python packages | `pip install -e ".[dev]"` |

## What's Included

### Skills (15)

Skills are invoked automatically by Claude based on task context, or manually with `/skill-name`. 15 are listed below; `dispatch-agents` is detailed in [Subagent Dispatch](#subagent-dispatch).

| Skill                            | Trigger                                                                  | Purpose                                                                                                                    |
| :------------------------------- | :----------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------- |
| `parallel-brainstorming`         | "brainstorm", "add a feature", "explore approaches"                      | Parallel multi-agent ideation + critique before implementation                                                             |
| `request-plan`                   | "plan", "design", "draft a plan", "write a spec"                         | Multi-agent ideate-and-synthesize: drafts plan/specs.md                                                                    |
| `receive-plan`                   | "check my plan", "is this plan ready", "verify this spec"                | Multi-agent critique panel + Traceability Auditor gate                                                                     |
| `request-code-review`            | "review", "check this", "is this correct"                                | Dispatches a fresh-context subagent to review the diff                                                                     |
| `receive-code-review`            | "reviewer said", "PR comments"                                           | Verify, push back on, and implement review feedback                                                                        |
| `test-driven-development`        | "TDD", "write tests", "implement this"                                   | Red-green-refactor workflow                                                                                                |
| `verification-before-completion` | (automatic before task completion)                                       | Verify changes work before marking done                                                                                    |
| `using-squad-agents-skills`      | (meta-routing)                                                           | Routes to the right skill based on context                                                                                 |

### Subagent Dispatch

These skills dispatch subagents in specialized roles: `implementer` (code writer), `researcher` (read-only investigator/explorer), `conflict-resolver` (merge conflict resolution), `reviewer`, and `diff-reviewer`. Two skills orchestrate them:

| Skill                 | Pattern                                                                                          |
| :-------------------- | :----------------------------------------------------------------------------------------------- |
| `dispatch-agents`     | Parallel fan-out or sequential dispatch — one subagent per task, gated by a `reviewer` pass      |
| `request-code-review` | One fresh-context subagent per diff, run read-only, with no memory of the implementation         |

> [!NOTE]
> Read-only roles (researcher, reviewers) are dispatched with write/edit tools denied in the invocation config; writer roles (implementer, conflict-resolver) can be dispatched in an isolated git worktree (`isolation: "worktree"`). These are applied per dispatch rather than enforced by a dedicated agent type.

### Hooks

Bash-only handlers (`hooks/*.sh`), wired in `hooks/hooks.json`. `shell-safety` is the only blocking hook — everything else is additive (warns or injects context, never blocks).

| Event                 | Handler        | What it does                                                                                                                                                             | Blocking? |
| :-------------------- | :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------- |
| `PreToolUse` (`Bash`) | `shell-safety` | Rejects a small, explicit denylist of catastrophic commands (`rm -rf /`, force-push to main/master, `git clean -fdx`). Override with `SQUAD_AGENTS_SKIP_SHELL_SAFETY=1`. | Yes       |
| `SessionStart` (`*`)  | `skill-nudge`  | Points toward this plugin's bundled skills, at most once per 24h. Opt out with `SQUAD_AGENTS_SKILL_NUDGE=0`.                                                             | No        |

`shell-safety.sh` is self-contained with no shared-library dependency, so a bug in any other hook file can never silently disable the one blocking guard. The denylist is intentionally narrow and documented as best-effort, not comprehensive protection.

### Configuration

You can configure project-local behaviors for the `squad-agents` plugin by creating a settings file at `.claude/squad-agents.local.md` in the root of your project:

```markdown
---
# Set to true to disable the shell safety check (use with caution)
skip_shell_safety: false

# Set to false to disable the periodic skill nudge on session start
skill_nudge: true
---

# squad-agents Configuration

This file configures local settings for the `squad-agents` plugin.
```

> [!IMPORTANT]
> Since hooks are loaded at session startup, any changes to this file will take effect on the next Claude Code session (requires restart). Remember to add `.claude/*.local.md` to your `.gitignore`.

## Project Structure

```text
.
├── bin/                    # Validation and release scripts
├── hooks/                  # Hook manifest and bash handlers
│   ├── shell-safety.sh
│   ├── skill-nudge.sh
│   └── hooks.json
├── output-styles/          # Output style definitions
└── skills/                 # Skill SKILL.md files (15 skills)
```

| Directory        | Purpose                                                          |
| :--------------- | :--------------------------------------------------------------- |
| `hooks/`         | Bash hook handlers and the hooks manifest                        |
| `skills/`        | One directory per skill, each containing a `SKILL.md` definition |
| `output-styles/` | Output style definitions                                         |
| `bin/`           | Manifest validator and release scripts                           |

## Scripts

| Command                           | Description                                                          |
| :-------------------------------- | :------------------------------------------------------------------- |
| `npm run validate`                | Validate the plugin manifest                                         |
| `npm test`                        | Validate, then run all Node.js and Python tests                      |
| `npm run test:node`               | Run Node.js unit tests only                                          |
| `npm run test:python`             | Run Python unit tests only                                           |
| `npm run test:integration`        | Run integration tests                                                |
| `npm run test:eval`               | Run skill-triggering evals for selected skills                       |
| `npm run lint`                    | Lint with ESLint                                                     |
| `npm run lint:fix`                | Lint and auto-fix with ESLint                                        |
| `npm run format`                  | Format all files with Prettier                                       |
| `npm run format:check`            | Check formatting without writing changes                             |
| `npm version patch\|minor\|major` | Bump version, sync manifests, tag, and push — triggers `release.yml` |

## Contributing

1. Fork the repository.
2. Create a feature branch — `git checkout -b feat/your-feature`.
3. Make your changes and run the full test suite: `npm test`.
4. Lint and format: `npm run lint && npm run format`.
5. Open a pull request against `master`.

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.

---

[Back to top](#squad-agents-plugin)
