# Plan Validation Guide

## Overview

After authoring a plan, validate it using `validate_plan.py` to check structural integrity, canonical task blocks, and markdown links.

```bash
python scripts/validate_plan.py path/to/plan.md
```

## What Validation Checks

✅ **Structural integrity**: All required sections present (Goal, Requirements, Current Context, Phases, Tasks)

✅ **Canonical task blocks**: Every task has required fields (Depends on, Files, Symbols, Action, Validate, Expected result)

✅ **Markdown links**: All file paths and symbols are markdown links (not bare paths or backticks)

✅ **Circular dependencies**: No task depends on another that depends on it

✅ **Broken links**: All TASK-001, PHASE-001 references resolve to actual headings

✅ **UNVERIFIED markers**: All unverified paths are listed; resolution plan documented

## Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Task TASK-001 missing "Depends on"` | Task block incomplete | Add "Depends on: none" or "Depends on: [TASK-001](#...)" |
| `Path src/auth.ts is bare path, not markdown` | Used `src/auth.ts` instead of `[src/auth.ts](src/auth.ts)` | Wrap all paths in markdown links |
| `Line 42: Link [foo](#L42) but section is #task-001` | Broken cross-reference | Check heading format; use `#task-001-title` |
| `Symbol validateToken not found in discovery` | Fabricated path or symbol | Re-run discovery; remove if not real |
| `UNVERIFIED marker without resolution plan` | Missing context | Add "Expected to exist after [TASK-002]" or manual note |

## Resolving UNVERIFIED Markers

If your plan has UNVERIFIED paths (e.g., for new files or cross-repo):

1. **Document why**: "New file created by TASK-001" or "External service config from deployment docs"
2. **Document how to resolve**: "Re-run discovery after TASK-001 completes" or "Manual verification required"
3. **Plan can proceed** once all markers have resolution plans (they don't need to be resolved before execution)

## Markdown Link Rules (Required)

**Valid**:
- `[path/to/file.ts](path/to/file.ts)`
- `[functionName](path/to/file.ts#L42)`
- `[functionName](path/to/file.ts#L42-L58)`

**Invalid**:
- Bare path: `src/auth.ts` ❌
- Backtick: `` `src/auth.ts` `` ❌
- Fabricated line: `[name](path#L999)` when L999 doesn't exist ❌

## Validation Output

Successful validation:

```
Plan: plan-auth-jwt-1.md
Status: VALID
Tasks: 12
Phases: 4
Errors: 0
Warnings: 0
```

If errors exist, fix them and re-validate before execution.

## Quality Gate Checklist

Before marking plan ready:

- ✅ Plan saved with correct naming (`[purpose]-[component]-[version].md`)
- ✅ No placeholder text ("TODO", "FIXME", "[add description]")
- ✅ Every file path is markdown link verified by discovery
- ✅ Every symbol has link + line anchor from discovery
- ✅ Every task has all 6 fields (Depends on, Files, Symbols, Action, Validate, Expected result)
- ✅ Every Validate field is executable command (not prose)
- ✅ Every Expected result is observable (e.g., "exit code 0", not "looks good")
- ✅ All TASK-001, PHASE-001 cross-references link correctly
- ✅ UNVERIFIED markers have resolution plans
- ✅ Validation script returns 0 errors
