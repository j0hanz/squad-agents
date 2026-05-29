---
description: Run the full planning pipeline for a new feature or task.
argument-hint: [task description]
---

# Plan — Feature Planning Pipeline

Plan the following task: `$ARGUMENTS`

If no task description is provided, ask:

> "What do you want to plan? Describe the feature or task in one sentence."

## Pipeline

Run these skills in sequence — complete each fully before starting the next:

1. **Invoke `brainstorming`** with the task description as the seed input — explore intent, constraints, domain terminology, and design options
2. **Invoke `create-specs`** using the brainstorm output — produce a structured technical specification
3. **Invoke `create-plan`** using the spec — produce a step-by-step implementation plan

Do not skip steps. Do not jump to `create-plan` without a spec.
