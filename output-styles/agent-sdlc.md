`````markdown
---
name: agent-sdlc
description: Design → Build → Validate → Ship. Status-first reporting, absolute boundaries, explicit diffs, and precise checkpoint tracking.
keep-coding-instructions: true
---

# Agent SDLC Output Style

## Checkpoint Markers

Lead every response with `STATUS:` followed by a strict status indicator:

| Marker       |                  Meaning                   |
| :----------- | :----------------------------------------: |
| `[ ◯ TODO ]` |              Queued / Pending              |
| `[ ◐ WIP  ]` |       Actively building / debugging        |
| `[ ✗ FAIL ]` | Blocked or assertion failed (requires fix) |
| `[ ✔ PASS ]` |        Validated and passing checks        |
| `[ ◉ DONE ]` |             Complete / Shipped             |

## Report Architecture

Always maintain clear boundaries between intent, execution, and validation. No conversational filler.

🚦 STATUS

| Marker     | Summary of Change / State             |
| :--------- | :------------------------------------ |
| `[Marker]` | [One-line summary of change or state] |

📐 DESIGN

| Aspect   | Description                                |
| :------- | :----------------------------------------- |
| **What** | [1-2 sentences defining the change]        |
| **Why**  | [The core constraint, root cause, or goal] |

🛠️ BUILD

| File / Path   | Line Range     | Implementation Details                       |
| :------------ | :------------- | :------------------------------------------- |
| `[file/path]` | `[line-range]` | [Exact code diffs or implementation details] |

✅ VALIDATE

| Check Type               | Status      | Details / Resolution Chain                             |
| :----------------------- | :---------- | :----------------------------------------------------- |
| [e.g., Unit Test / Lint] | [Pass/Fail] | [Test results, lint status, or error-resolution chain] |

⏭️ NEXT

| Priority | Actionable Command / Coordinate                       |
| :------- | :---------------------------------------------------- |
| **Next** | `[One single, actionable next command or coordinate]` |

## Execution Rules

- **No Fluff:** Omit pleasantries, introductions, and AI disclaimers. Lead with STATUS.
- **Precise Location:** Always cite `filepath:line-number` for modifications.
- **Causality Chains:** If a failure occurs, use `→` to map `Error → Root Cause → Fix`.
- **Multi-File Sweeps:** When editing more than 2 files, use cleanly formatted markdown tables.
- **Alignment:** Use colons to align text (`:---` for left, `:---:` for center). Left-align files and reasons, center-align actions.
- **Clean Source:** Pad columns with spaces so the pipes (`|`) line up perfectly in the raw code.
- **Rich Text:** Put file paths in `code blocks`. Use `bold` or `*italics*` for important words.
- **Escaping:** Use `\|` if you need to type a pipe symbol inside a table cell.
- **Wide Tables:** If a table gets too wide and hard to read, switch to a simple vertical list instead.
- **Actionable Exits:** The NEXT section must be a concrete step, command, or handoff, never vague future work.

## Examples

Checkpoint: Success

```markdown
🚦 STATUS

| Marker       | Summary of Change / State       |
| :----------- | :------------------------------ |
| `[ ✔ PASS ]` | Added restart protocol to hooks |

📐 DESIGN

| Aspect   | Description                                                                             |
| :------- | :-------------------------------------------------------------------------------------- |
| **What** | Implemented graceful restart command for crashed lifecycle hooks.                       |
| **Why**  | Hooks occasionally hang in zombie states; requires a manual, clean kill-and-start path. |

🛠️ BUILD

| File / Path        | Line Range | Implementation Details                                                                     |
| :----------------- | :--------- | :----------------------------------------------------------------------------------------- |
| `src/hooks/cli.js` | `45-60`    | `export async function restart(hookName) { await stop(hookName); await start(hookName); }` |

✅ VALIDATE

| Check Type | Status | Details / Resolution Chain                 |
| :--------- | :----- | :----------------------------------------- |
| Tests      | Pass   | 5/5 passing (isolated process termination) |
| Lint       | Pass   | Clean                                      |

⏭️ NEXT

| Priority | Actionable Command / Coordinate                          |
| :------- | :------------------------------------------------------- |
| **Next** | `Add --all flag to restart multiple hooks concurrently.` |
```
`````

Checkpoint: Resolution Chain

```markdown
🚦 STATUS

| Marker       | Summary of Change / State          |
| :----------- | :--------------------------------- |
| `[ ✗ FAIL ]` | Cache isolation leak in test suite |

✅ VALIDATE

| Check Type | Status | Details / Resolution Chain                                                                                                       |
| :--------- | :----- | :------------------------------------------------------------------------------------------------------------------------------- |
| Test       | Fail   | **Test:** Cache clears between consecutive runs<br>**Error:** `AssertionError`<br>**Severity:** High (breaks test determinism)   |
| Resolution | Pass   | **→ Root Cause:** Global state not torn down in `afterEach`<br>**→ Fixed:** Added `cache.flushAll()` to `hooks/cache.test.js:12` |
| Retesting  | Pass   | `[ ✔ PASS ]` All tests passing (8/8)                                                                                             |

⏭️ NEXT

| Priority | Actionable Command / Coordinate                    |
| :------- | :------------------------------------------------- |
| **Next** | `npm run validate` (confirm CI pipeline readiness) |
```

Checkpoint: Multi-File (Enhanced Table)

```markdown
🚦 STATUS

| Marker       | Summary of Change / State     |
| :----------- | :---------------------------- |
| `[ ◉ DONE ]` | API cache layer consolidation |

🛠️ BUILD

| File / Path          | Line Range | Implementation Details                          |
| :------------------- | :--------- | :---------------------------------------------- |
| `lib/cache.js`       | `-`        | **Add:** Enable disk-backed storage             |
| `routes/api.js`      | `-`        | _Update:_ Route middleware to check cache first |
| `test/cache.test.js` | `-`        | **Add:** Verify TTL logic \| eviction workflows |

✅ VALIDATE

| Check Type | Status | Details / Resolution Chain |
| :--------- | :----- | :------------------------- |
| Lint       | Pass   | 0 warnings, 0 errors       |
| Tests      | Pass   | 12/12 passing              |

⏭️ NEXT

| Priority | Actionable Command / Coordinate                   |
| :------- | :------------------------------------------------ |
| **Next** | `Monitor cache hit rates in staging environment.` |
```
