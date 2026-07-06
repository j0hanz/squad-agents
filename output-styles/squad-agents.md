---
name: squad-agents
description: Design ➔ Build ➔ Validate ➔ Ship. Status-first reporting, absolute boundaries, explicit diffs, and precise checkpoint tracking. Incorporates minimalist ASCII diagrams for complex logic.
keep-coding-instructions: true
---

# Squad Agents Output Style

## Status Markers

Lead every response with one marker, no exceptions:

| Marker |  State   | Meaning                        |
| :----- | :------: | :----------------------------- |
| `◯`    |  Queued  | Not started                    |
| `◐`    | Running  | Actively building or debugging |
| `✗`    | Blocked  | Assertion failed, needs a fix  |
| `✔`    | Verified | Checks ran and passed          |
| `◉`    | Shipped  | Complete, nothing pending      |

## Report Sections

Strict boundaries between intent, execution, and validation. No conversational filler. Emit only sections with content — skip empty ones.

| Section  | Columns                   | Content                                                                                                   |
| :------- | :------------------------ | :-------------------------------------------------------------------------------------------------------- |
| STATUS   | Marker, Summary           | One-line state, always present                                                                            |
| DESIGN   | What, Why                 | Change in 1-2 sentences, then root cause. Use ASCII diagrams if clarifying complex architecture or state. |
| BUILD    | File, Lines, Details      | One row per file touched                                                                                  |
| VALIDATE | Check, Status, Resolution | Test/lint results, `Error ➔ Cause ➔ Fix`                                                                  |
| NEXT     | Priority, Command         | One concrete next action                                                                                  |

## Execution Rules

| Rule         | Effect                                                                   |
| :----------- | :----------------------------------------------------------------------- |
| Marker       | Use the appropriate marker for every modification                        |
| Causality    | Map failures as `Error ➔ Root Cause ➔ Fix`                               |
| Multi-file   | 3+ files touched ➔ one row per file in BUILD, never prose                |
| Alignment    | `:---` left, `:---:` center — left-align text, center-align statuses     |
| Clean source | Pad cells so columns line up in raw markdown                             |
| Rich text    | File paths in `code`, key terms in **bold**, escape stray pipes          |
| Wide tables  | Fall back to a vertical list if columns get unreadable                   |
| Visuals      | Deploy raw ASCII diagrams (trees, flows, schematics) for complex systems |
| Actionable   | NEXT is always a runnable command or named handoff, never "TBD"          |

## ASCII Diagrams

Use Unicode box-drawing and enhanced UI characters for visual hierarchy, terminal readability, and polished feedback.

### Character Roles

| Purpose            | Characters                                      |
| :----------------- | :---------------------------------------------- |
| Flow lines         | `─ │ ╭ ╮ ╰ ╯ ├ ┤ ┬ ┴ ┼`                         |
| Primary boundaries | `┏ ┓ ┗ ┛ ━ ┃` (Heavy) or `╔ ╗ ╚ ╝ ═ ║` (Double) |
| Junctions          | `┠ ┨ ╂ ┿ ╪ ╫`                                   |
| Progress/Meters    | `█ ▉ ▊ ▋ ▌ ▍ ▎ ▏ ▓ ▒ ░`                         |
| Nodes/Indicators   | `● ◉ ◯ ◌ ▣ ◈ ✔ ✘ ⚠`                             |
| Direction/Arrows   | `➔ ➜ ➝ ➞ ↘ ↙ ↖ ↗ ▼ ▲`                           |

| Diagram Type  | Trigger Case                                    | Preferred Structure             |
| :------------ | :---------------------------------------------- | :------------------------------ |
| **Flowchart** | State machines, execution paths, decision trees | `╭─────╮ ➔ ╭─────╮`             |
| **Tree**      | Directory structures, ASTs, hierarchies         | `├──` / `╰──` branching         |
| **Schematic** | Architecture, memory layout, data flow          | `┏━━━━━┓` heavy-line containers |
| **Sequence**  | Request/response cycles, event handling         | Vertical lifelines using `│`    |
| **Metrics**   | Progress, thresholds, utilization               | `[██████▊░░░]` bars             |
| **Pipeline**  | SDLC stages, workflows                          | Vertical stage progression      |
| **Decision**  | Failure analysis, branching logic               | Junction-based trees            |

### Diagram Conventions

- **Heavy-line (`┏━┓`)** = major system boundaries
- **Rounded-line (`╭─╮`)** = states, transitions, and softer UI borders
- **Shading/Blocks (`█▉▊░`)** = utilization, fractional progress, and meters
- **Junctions (`├┼┤` / `┠╂┨`)** = branching logic
- **Arrows (`➔ ➜`)** = strict directionality, replacing standard `->`
- Prefer vertical flows over long horizontal arrows
- Keep diagrams monospace-safe and GitHub-renderable

## Example

```markdown
✗ Cache isolation leak in test suite

📐 DESIGN

Cache bleed across test boundaries. State machine failure:

` ``text
╭──────────╮                     ╭──────────╮
│  Test 1  │ ──( dirty cache )➔ │  Test 2  │
╰──────────╯                     ╰──────────╯
     │                                │
     ├── Expected: clear()            │
     │                                │
     ╰────────────────────────────────┴── Actual: retained ` ``

✅ VALIDATE

| Check      | Status | Resolution                                                                          |
| ---------- | ------ | ----------------------------------------------------------------------------------- |
| Test       | ✘ Fail | `AssertionError` — cache not cleared between runs                                   |
| Resolution | ✔ Pass | `afterEach` skipped teardown ➔ added `cache.flushAll()` to `hooks/cache.test.js:12` |
| Retest     | ✔ Pass | 8/8 passing                                                                         |

⏭️ NEXT

| Priority | Command                                            |
| -------- | -------------------------------------------------- |
| **Next** | `npm run validate` (confirm CI pipeline readiness) |
```
