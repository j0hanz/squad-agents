# Skill Routing Map

## Quick Lookup by Task Type

| I want to…                          | Invoke this skill                |
| ----------------------------------- | -------------------------------- |
| Start a new feature, skill, or hook | `brainstorming`                  |
| Fix a bug or trace a failure        | `diagnose`                       |
| Clean up messy or hard-to-read code | `refactor`                       |
| Review a diff or PR                 | `code-review`                    |
| Write a spec and plan               | `planning`                       |
| Create or improve a skill           | `skill-builder`                  |
| Design a new managed agent          | `create-agent`                   |
| Implement a lifecycle hook          | `create-hook`                    |
| Final check before marking complete | `verification-before-completion` |
| Draw architecture or data flow      | `diagrams`                       |
| Research a library or API           | `research`                       |

---

## Process / Methodology Skills

| Skill                            | Invoke when…                                                                                                                                                                                    |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `brainstorming`                  | Starting any new feature, component, agent, skill, or hook. **Required before design approval.**                                                                                                |
| `planning`                       | Writing formal specs AND an atomic implementation plan together. Produces paired `<name>.specs.md` + `<name>.plan.md` with enforced traceability.                                               |
| `spec-driven-development`        | Full spec-first development lifecycle with validation gates.                                                                                                                                    |
| `test-driven-development`        | Any non-trivial logic that needs red-green-refactor discipline.                                                                                                                                 |
| `skill-builder`                  | Creating, testing, improving, or evaluating a skill.                                                                                                                                            |
| `create-agent`                   | Designing a new managed agent (system prompt, tools, model, context).                                                                                                                           |
| `create-hook`                    | Designing or implementing a lifecycle hook handler.                                                                                                                                             |
| `verification-before-completion` | **MANDATORY** before any `/deliver` or "done" claim. Runs structured checklist: tests pass, no debug artifacts, no TODOs, docs in sync, output style followed. Invoke it — do not self-certify. |
| `architecture`                   | Checking code locality, coupling, or module boundary decisions.                                                                                                                                 |

## Domain / Execution Skills

| Skill         | Invoke when…                                                                                                                           |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `code-review` | Reviewing a diff or PR (accepts `--low`, `--medium`, `--high`, `--ultra` effort flags; `--fix` to apply).                              |
| `refactor`    | Cleaning up code without behavior change. Trigger on "refactor", "clean up", "messy", "hard to follow", "simplify", or "hard to test". |
| `diagnose`    | Debugging a failure, tracing a runtime error, or investigating unexpected behavior.                                                    |
| `diagrams`    | Visualizing architecture, workflows, hook flow, or data models.                                                                        |
| `research`    | Scoped web research on libraries, APIs, or external services.                                                                          |

## Lifecycle / Ops Skills

| Skill               | Invoke when…                                                      |
| ------------------- | ----------------------------------------------------------------- |
| `agents-maintainer` | Keeping AGENTS.md and CLAUDE.md in sync after structural changes. |
| `delivery-manager`  | Validating, committing, and opening a PR (invoke via `/deliver`). |
