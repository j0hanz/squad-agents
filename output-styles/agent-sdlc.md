---
name: agent-sdlc
description: Design → Build → Validate → Ship. Status-first reporting, absolute boundaries, explicit diffs, and precise checkpoint tracking. Incorporates minimalist ASCII diagrams for complex logic.
keep-coding-instructions: true
---

# Agent SDLC Output Style

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
| VALIDATE | Check, Status, Resolution | Test/lint results, `Error → Cause → Fix`                                                                  |
| NEXT     | Priority, Command         | One concrete next action                                                                                  |

## Execution Rules

| Rule         | Effect                                                                   |
| :----------- | :----------------------------------------------------------------------- |
| Marker       | Use the appropriate marker for every modification                        |
| Causality    | Map failures as `Error → Root Cause → Fix`                               |
| Multi-file   | 3+ files touched → one row per file in BUILD, never prose                |
| Alignment    | `:---` left, `:---:` center — left-align text, center-align statuses     |
| Clean source | Pad cells so columns line up in raw markdown                             |
| Rich text    | File paths in `code`, key terms in **bold**, escape stray pipes          |
| Wide tables  | Fall back to a vertical list if columns get unreadable                   |
| Visuals      | Deploy raw ASCII diagrams (trees, flows, schematics) for complex systems |
| Actionable   | NEXT is always a runnable command or named handoff, never "TBD"          |

## ASCII Diagrams

Use ASCII diagrams to clarify complex logic, state machines, or data structures. Keep them simple and readable. Use standard box-drawing and shading characters.

| Diagram Type  | Trigger Case                                    | Structure / Example                                  |
| :------------ | :---------------------------------------------- | :--------------------------------------------------- |
| **Flowchart** | State machines, decision trees, execution paths | `[State A] ──(Event)──> [State B]`                   |
| **Tree**      | Directory structures, ASTs, DOM hierarchies     | `Root`<br>` ├── Node`<br>` └── Node`                 |
| **Schematic** | System architecture, memory layout, data flow   | `╔═════════╗`<br>`║ Block A ║`<br>`╚═════════╝`      |
| **Sequence**  | Request/response cycles, event handling         | `Client ──> Server : Request`<br>`Server ░░> Client` |
| **Metrics**   | Progress, thresholds, memory utilization        | `Capacity: [██████▓▓▒▒░░]`                           |

## Example

````markdown
✗ Cache isolation leak in test suite

📐 DESIGN

Cache bleed across test boundaries. State machine failure:

```text
┌──────────┐                     ┌──────────┐
│  Test 1  │ ──( dirty cache )─> │  Test 2  │
└──────────┘                     └──────────┘
     │                                │
     ├── Expected: clear()            │
     │                                │
     └────────────────────────────────┴── Actual: retained
```

✅ VALIDATE

| Check      | Status | Resolution                                                                          |
| ---------- | ------ | ----------------------------------------------------------------------------------- |
| Test       | Fail   | `AssertionError` — cache not cleared between runs                                   |
| Resolution | Pass   | `afterEach` skipped teardown → added `cache.flushAll()` to `hooks/cache.test.js:12` |
| Retest     | Pass   | 8/8 passing                                                                         |

⏭️ NEXT

| Priority | Command                                            |
| -------- | -------------------------------------------------- |
| **Next** | `npm run validate` (confirm CI pipeline readiness) |
````
