---
name: using-agent-dev-skills
description: "Entry-point meta-skill for the agent-dev plugin. Check at session start or when uncertain which skill to use. Routes tasks to the correct agent-dev skill: brainstorming, planning, test-driven-development, diagnose, code-review, refactor, architecture, create-agent, create-hook, skill-builder, github-automation, verification-before-completion, agents-maintainer. Trigger on 'where do I start', 'which skill', 'how does this work', 'let me build a new agent', 'about to open a PR', 'ready to merge', or at the beginning of any new task in this repo."
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

# Using Agent Dev Skills

## How to Use This Skill

- Read this skill at the start of every session in this repo.
- Check the routing table before beginning any task.
- When a row matches — even partially — invoke that skill.
- When in doubt, invoke. Do not skip.
- Before invoking a routed skill, output one line: `Routing to \`<skill-name>\`: <one-sentence reason>.`

## Priority Order

1. **User's explicit instruction** — overrides everything
2. **Agent-dev skill** — overrides default model behavior
3. **Default model response** — only when no skill applies

<EXTREMELY-IMPORTANT>

## Do Not Rationalize Skipping

These thoughts mean you are about to make a mistake. Check the routing table first — without exception.

| Rationalization                         | Reality                                                                   |
| :-------------------------------------- | :------------------------------------------------------------------------ |
| "This is simple, skills are overkill."  | Simple things become complex. The skill takes 2 seconds to check.         |
| "I'll check skills once I get started." | Skill check comes before any action, including the first one.             |
| "I already know how to do this."        | Knowing the concept is not the same as invoking the skill.                |
| "The skill is for more complex cases."  | If a skill exists for this task, use it. Complexity is not the threshold. |
| "This is just a quick question."        | Questions are tasks. Check for skills before answering.                   |
| "I need more context first."            | Skills tell you how to gather context. Check first.                       |
| "I remember this skill from training."  | Skills evolve. Read the current version every time.                       |

</EXTREMELY-IMPORTANT>

---

## Routing Table

| Task signal                                                                                  | Skill to invoke                  |
| :------------------------------------------------------------------------------------------- | :------------------------------- |
| "let's build X", "add a feature", "we need a new Y", ambiguous design, unclear terminology   | `brainstorming`                  |
| "write a spec", "create a plan", "define requirements", "implementation plan"                | `planning`                       |
| Implementing code, writing functions, any non-trivial implementation                         | `test-driven-development`        |
| "something is broken", "debug this", "why is X failing", unexpected output, production error | `diagnose`                       |
| "review this", "any issues?", "check for bugs", before opening a PR                          | `code-review`                    |
| "clean up", "refactor", "simplify", "improve this code", "hard to read"                      | `refactor`                       |
| "architecture review", "too coupled", "where should this code live", "God class"             | `architecture`                   |
| "add hook", "block a tool", "auto-format", "run tests on save", lifecycle guarantees         | `create-hook`                    |
| "build an agent", "create subagent", "agent prompt", "agent not working"                     | `create-agent`                   |
| "make a skill", "build skill", "skill not working", "turn this workflow into a skill"        | `skill-builder`                  |
| "add CI", "set up release", GitHub Actions workflows, `gh` CLI scripting                     | `github-automation`              |
| About to say "done", "ready to review", "looks good", or "ready to merge"                    | `verification-before-completion` |
| "update AGENTS.md", "improve agent instructions", "onboard me", trimming CLAUDE.md           | `agents-maintainer`              |

---

## Lifecycle Chain

For a complete feature, skills connect in order:

```
brainstorming
     │
     ▼
  planning
     │
     ▼
test-driven-development  ◄── (loop: RED → GREEN → REFACTOR)
     │
     ▼
verification-before-completion
     │
     ▼
  code-review
     │
     ▼
github-automation
```

Side paths — invoke at any stage when the signal matches:

| Signal                                 | Skill                        |
| :------------------------------------- | :--------------------------- |
| Code breaks mid-build                  | `diagnose`                   |
| Code is hard to follow or change       | `architecture` or `refactor` |
| Building a new skill                   | `skill-builder`              |
| Building a new agent or subagent       | `create-agent`               |
| Adding a lifecycle hook                | `create-hook`                |
| Updating project or agent instructions | `agents-maintainer`          |

---

## Skill Types

| Type                                           | Skills                                                     | How to follow                                                   |
| :--------------------------------------------- | :--------------------------------------------------------- | :-------------------------------------------------------------- |
| **Rigid** — mandatory phase gates, no skipping | `test-driven-development`, `diagnose`, `planning`          | Follow every phase in order. Gates are blocking. Never skip.    |
| **Flexible** — adapt to context                | `brainstorming`, `refactor`, `code-review`, `architecture` | Apply judgment within the defined phases. Complete all of them. |

---

## Quick-Start Decision

Answer in order — stop at the first match:

1. No spec or approved design exists → invoke `brainstorming`, then `planning`
2. Failing test, crash, or unexpected behavior → invoke `diagnose`
3. Implementation complete, needs verification → invoke `verification-before-completion`, then `code-review`
4. Building a skill, agent, or hook → invoke `skill-builder` / `create-agent` / `create-hook`
5. Code is written but hard to understand or change → invoke `architecture` or `refactor`
