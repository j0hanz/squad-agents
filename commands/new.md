---
description: Scaffold a new skill, agent, or hook in this plugin.
argument-hint: [skill|agent|hook] [name]
---

# New — Scaffold Plugin Component

Create a new plugin component from: `$ARGUMENTS`

## Parse Arguments

Format: `[type] [name]`

- **type**: `skill`, `agent`, or `hook`
- **name**: kebab-case component name (e.g. `my-feature`)

If arguments are missing or the type is not one of the three, ask:

> "What do you want to create? `skill`, `agent`, or `hook`? And what should it be named?"

## Route

| type    | Action                                                                            |
| ------- | --------------------------------------------------------------------------------- |
| `skill` | Invoke the `skill-builder` skill with the name as context                         |
| `agent` | Invoke the `skill-builder` skill with the name as context (it handles agents too) |
| `hook`  | Invoke the `hook-development` skill with the name as context                      |
