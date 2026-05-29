---
description: Review agent-dev artifacts (skills, agents, plans, hooks) for quality, design, and alignment.
argument-hint: [create|audit|update|lint] [type|name]
---

# Artifact Review

Review agent-dev plugin components for quality and design.

**Mode format:** `$ARGUMENTS` = `[mode] [type|name]`

## Modes

| Mode            | Usage                                           | Purpose                                                                     |
| --------------- | ----------------------------------------------- | --------------------------------------------------------------------------- |
| `create [type]` | `create skill`, `create agent`, `create plan`   | Review design before writing (architectural vetting)                        |
| `audit [name]`  | `audit brainstorming`, `audit delivery-manager` | Audit existing skill quality (trigger phrases, frontmatter, body structure) |
| `update [name]` | `update new`, `update plan`                     | Refine a skill based on audit findings (improve trigger phrases, body)      |
| `lint [type]`   | `lint hooks`, `lint agents`                     | Structural lint pass (naming, SKILL.md presence, syntax)                    |

If mode is missing, ask:

> "Do you want to **create**, **audit**, **update**, or **lint** a review? And what's the target?"

## Mode: Create [type]

Architectural review of a proposed component BEFORE implementation.

**For skill/agent:** Review trigger phrase clarity, frontmatter scope, tool needs, potential conflicts with existing skills.
**For plan:** Review task granularity, file paths, completeness, test coverage.

Invoke the `skill-builder` or `create-plan` skill with the proposed design.

## Mode: Audit [name]

Quality audit of an existing skill or agent.

1. **Load the artifact:** `skills/[name]/SKILL.md` or `agents/[name].md`
2. **Check frontmatter:** description clarity, `disable-model-invocation` appropriateness, trigger phrase specificity
3. **Check body:** length vs. scope, reference files usage, no generic hedging ("handle errors appropriately")
4. **Cross-check:** does the description match what the skill actually does?

Report findings grouped by: frontmatter issues → body issues → trigger phrase precision.

## Mode: Update [name]

Refine and improve an existing skill or agent based on audit findings.

1. **Load the artifact:** `skills/[name]/SKILL.md` or `agents/[name].md`
2. **Identify issues:** Unclear trigger phrases, overly broad scope, generic body text, missing frontmatter fields
3. **Propose improvements:** Tighten trigger phrases, clarify description, improve frontmatter, clean up body
4. **Apply changes:** Edit the file with refined content

Invoke the `skill-builder` skill to apply the refinements.

## Mode: Lint [type]

Structural check for naming, file presence, and syntax validity.

- `lint skills` — all SKILL.md files exist, valid YAML frontmatter, kebab-case directory names
- `lint agents` — all agents `.md` files valid, proper frontmatter, no naming conflicts
- `lint hooks` — hooks.json valid JSON, all referenced script paths exist

Invoke `agents-maintainer` scan tools.
