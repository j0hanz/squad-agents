---
description: Refactor code for clarity, maintainability, or testability without changing behavior.
argument-hint: [file path or description of what to refactor]
---

# Refactor: $ARGUMENTS

Invoke the `refactor` skill on: `$ARGUMENTS`

If no target is provided, ask:

> "What do you want to refactor? Provide a file path or describe the code area (e.g. `hooks/handlers/explorer.mjs`, 'the session context logic')."

## Decision Check

Before refactoring, confirm the right skill is being used:

- **Is the fundamental structure or design wrong?** → Use `architecture` instead (redesign the blueprint)
- **Is the code messy but structure is sound?** → Proceed with `refactor` (clean up the existing code)

Examples:
- "This function has 8 nested loops" → `refactor`
- "Microservices are too tightly coupled" → `architecture`

## Constraints

The `refactor` skill preserves behavior — do not change public APIs, alter observable behavior, or introduce new features during a refactor pass. Run tests before and after to confirm nothing regressed.

---

<!-- Usage: /refactor hooks/handlers/explorer.mjs -->
<!-- Usage: /refactor the session context loading logic -->
