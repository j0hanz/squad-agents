# Decomposition Guide

## Phase vs Task

**Phase** — a major work unit with one measurable goal. Groups related tasks.

**Task** — an atomic unit: one code change, one file modified, one clear observable outcome.

## Task sizing

A well-sized task:

- Duration: 15–60 minutes for an experienced developer
- Files: touches 1–3 files max
- Outcome: one observable result (no "and")
- Dependencies: minimal coupling

**Split when:** more than 3 distinct changes in one file; tests for unrelated components; task description uses "and".

**Combine when:** single function, < 5 min; trivial boilerplate with no independent value.

## Phase structure

Good phases have one measurable goal and 3–8 tasks:

```markdown
## PHASE-001: Setup & Configuration

## PHASE-002: Core Implementation

## PHASE-003: Integration & Testing

## PHASE-END: Acceptance
```

## Effort reference

| Task type                 | Complexity            | Base time |
| ------------------------- | --------------------- | --------- |
| New file (implementation) | Simple (< 50 LOC)     | 15–30 min |
| New file (utility/helper) | Medium (50–150 LOC)   | 30–60 min |
| New file (integration)    | Complex (150–300 LOC) | 60–90 min |
| Modify existing file      | Simple (1–20 changes) | 10–20 min |
| Modify existing file      | Complex (20+ changes) | 30–60 min |
| Test file (unit)          | Per 10 cases          | 20–30 min |
| Test file (integration)   | Per 5 cases           | 30–45 min |

**Multipliers:** unfamiliar framework ×1.3; complex architecture change ×1.5; first time in codebase ×1.2.

## By depth

| Depth     | Task count | Total effort |
| --------- | ---------- | ------------ |
| sketch    | 5–12       | 1–2 hours    |
| contract  | 12–30      | 3–8 hours    |
| blueprint | 20–50      | 8–15 hours   |
