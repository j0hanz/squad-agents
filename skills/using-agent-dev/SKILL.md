---
name: using-agent-dev
description: |
  Navigation guide for agent-dev plugin skills — establishes routing and priority order.
  Use when asking "which skill should I use for X?", when a task doesn't clearly map to
  an existing skill, or when working within the agent-dev plugin context.
disable-model-invocation: false
---

> **Invocation:** When installed as the `agent-dev` plugin, prefix skill names with `agent-dev:` — e.g., `/agent-dev:brainstorming`. In a standalone `.claude/skills/` installation, use bare names — e.g., `/brainstorming`.

# Agent-Dev Skill System

## Skill Map

### Process Skills — use these FIRST (they govern HOW to work)

| Skill                            | Invoke when...                                                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `brainstorming`                  | User asks to build, add, or change any feature or behavior; domain terminology is ambiguous; glossary or term alignment needed |
| `diagnose`                       | Any bug, test failure, unexpected behavior, or crash                                                                           |
| `test-driven-development`        | Implementing any feature or bugfix                                                                                             |
| `spec-driven-development`        | Full feature lifecycle (spec → plan → code → validate)                                                                         |
| `create-specs`                   | Formalizing requirements before planning                                                                                       |
| `create-plan`                    | Breaking work into tasks before coding                                                                                         |
| `verification-before-completion` | Before declaring any task or feature done                                                                                      |
| `code-review`                    | Before reporting implementation complete                                                                                       |
| `delivery-manager`               | Transitioning code to PR or delivery                                                                                           |

### Domain Skills — use AFTER choosing your process

| Skill               | Invoke when...                                                  |
| ------------------- | --------------------------------------------------------------- |
| `research`          | External APIs, libraries, or unfamiliar docs                    |
| `architecture`      | Designing new systems or improving structure of existing code   |
| `refactor`          | Restructuring without changing behavior                         |
| `diagrams`          | Creating architectural visualizations                           |
| `github-automation` | GitHub Actions workflows or gh CLI automation/scripting         |
| `hook-development`  | Designing or implementing Claude Code hooks                     |
| `agent-development` | Building Claude agents, skills, or sub-skill pipelines          |
| `skill-builder`     | Creating, updating, testing, or benchmarking skills             |
| `agents-maintainer` | Updating AGENTS.md, CLAUDE.md, or instruction files             |

### Unmapped Tasks

If a task does not fit any existing skill in the map, use `skill-builder` to create a new skill or update an existing one to capture the missing knowledge.

## Skill Priority

1. **Process skills first** — brainstorming, diagnose, and TDD determine HOW to approach the task
2. **Domain skills second** — guide implementation details within that approach

## Rigid vs Flexible

**Rigid** (follow exactly — do not adapt away from the discipline):

- `diagnose` — root cause documented before any fix
- `test-driven-development` — one test, run it, one impl, run it; no batching
- `spec-driven-development` — spec → plan → code order is mandatory

**Flexible** (adapt principles to context):

- All domain skills — `research`, `architecture`, `refactor`, `diagrams`, `github-automation`, `hook-development`, `agent-development`, `skill-builder`, `agents-maintainer` — unless the skill body itself says otherwise.
