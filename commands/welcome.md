---
description: Get a guided tour of the agent-dev plugin.
---

# Welcome — Plugin Walkthrough

Welcome to the **agent-dev** plugin. This plugin provides skills, agents, hooks, and slash commands for building and maintaining Claude Code agents and skills.

## Slash Commands

| Command             | Purpose                                                                 |
| ------------------- | ----------------------------------------------------------------------- |
| `/plan`             | Brainstorm → spec → implementation plan                                 |
| `/new`              | Scaffold a skill, agent, or hook from a template                        |
| `/eval`             | Create, audit, run, or lint evaluation suites                           |
| `/check`            | Validate plugin health (structure, skills, agents, hooks, manifest)     |
| `/artifact-review`  | Audit existing skills, agents, plans, or hooks for quality and design   |
| `/deliver`          | Validate, commit with attribution, and open a PR                        |
| `/debug`            | Debug a problem using the structured `diagnose` methodology             |
| `/test`             | Run the plugin test suite (node, python, integration, or all)           |
| `/refactor`         | Clean up code using the `refactor` skill without changing behavior      |
| `/docs`             | Create or update AGENTS.md, CLAUDE.md, README, or skill documentation   |

## Agents

| Agent        | Purpose                                                    |
| ------------ | ---------------------------------------------------------- |
| `coder`      | Autonomous code execution and refactoring                  |
| `explorer`   | Read-only research and codebase navigation                 |
| `documenter` | Documentation generation (invoked by `/docs readme`)       |

## Skill Routing

Not sure which skill to use? Run the `using-agent-dev` skill for a full routing map and decision tree. Quick guide:

- Something broken → `/debug` (diagnose skill)
- Building something new → `/plan` (brainstorm → spec → plan)
- Requirements unclear → brainstorming skill
- Code messy → `/refactor` (refactor skill)
- Structure wrong → architecture skill
- Need API docs → research skill (Context7)

## Monitors

| Monitor | Purpose |
| --- | --- |
| `telemetry-watcher` | Live hook execution telemetry and error surfacing |
| `node-test-watcher` | Hook handler tests — live feedback during hook dev |
| `python-test-watcher` | Skill script tests — live feedback during skill dev |

## Getting Started

Run `/check all` to confirm the plugin is healthy, then `/plan` to start building.
