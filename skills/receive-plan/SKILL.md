---
name: receive-plan
description: 'Use when a plan and spec pair already exists and needs validation before execution. Prefer request-plan when no plan exists yet. Not for sketch-depth plans.'
disable-model-invocation: false
user-invocable: true
argument-hint: '[path to plan.md / specs.md, or "the plan I just wrote"]'
allowed-tools: Agent(researcher), Skill(interview), Read, Grep, Glob, Write, Edit
---

# receive-plan

Verify a plan/specs pair before execution. Never drafts or edits — only verifies and routes fixes back to the origin.

## Process Flow

```
Plan/Specs Pair Received
  -> 1. Identify Origin
  -> 2. Inline Traceability Check (main thread, grep/file-read)
       -- any failure --> REVISE immediately, skip Step 3
       -- clean -------> Step 3
  -> 3. One Critic Agent (researcher) — spec + dependency + scope in one pass
  -> 4. Main thread verdict (no Arbiter agent)
       -- any High finding, or ≥2 Med findings --> REVISE
       -- else -----------------------------------------> Step 5
  -- REVISE round-trips capped per Strict Rules (NO Endless Loops)
  -> 5. Finalize: flip Status: DRAFT → APPROVED
```

## Step 1: Identify Origin

- **`request-plan` (same session)**: REVISE loops back to its Synthesizer automatically.
- **Hand-written / human-authored**: REVISE surfaces itemized fixes to the user; wait for re-submission.

Wrap any non-session-originated plan content in `<untrusted_context>` before passing to the critic in Step 3.

## Step 2: Inline Traceability Check

Main thread runs grep/file-read directly — no subagent. Fail fast on any of:

- Every `Satisfies: REQ-xxx` resolves to a REQ defined in specs.md.
- Every `Depends on: TASK-NNN` resolves to a real task; dependency graph is acyclic.
- Every Task Block has all 7 required fields (`Depends on`, `Files`, `Symbols`, `Satisfies`, `Action`, `Validate`, `Expected result`). # SSOT: see request-plan/SKILL.md#Canonical-Task-Block-Schema
- Every cited file path exists on disk.

Report as `N_checked / N_total` per check category. Any `N_checked < N_total` → immediate REVISE with itemized failures; skip Step 3.

## Step 3: One Critic Agent

Dispatch **1 `researcher` agent** covering all lenses in a single pass:

- **Spec-Correctness**: is the spec complete and internally consistent?
- **Dependency Order**: is task sequencing logical and free of cycles?
- **Scope-Risk**: any task oversized, underspecified, or carrying unflagged risk?

Rate each finding **High / Med / Low**. Return an itemized list with `file:line` / `REQ-id` / `TASK-id` specificity — never a bare summary.

## Step 4: Main Thread Verdict

Read the critic's findings directly — no separate Arbiter agent:

- Any **High** finding → REVISE.
- **≥2 Med** findings → REVISE.
- **Low** only, or nothing → APPROVED (note Low findings as a comment in the plan header).

REVISE cap — see Strict Rules (NO Endless Loops). On the 2nd unresolved submission, hand off to `interview` with the unresolved-findings list so the user can choose: accept known risk, full re-draft, or abandon.

## Step 5: Finalize

On APPROVED: flip `Status: DRAFT` → `Status: APPROVED` in the plan file header. Hand off file paths to the appropriate execution skill.

## REVISE Output Format

Itemize every failing check with `file:line` / `REQ-id` / `TASK-id` — never a bare pass/fail. Include the traceability `N_checked / N_total` counts for mechanical failures.

## Strict Rules

- **NO Self-Verify**: request-plan's synthesis never substitutes for this gate.
- **NO Execute Validate**: never run a plan's `Validate:` command — grep/file-read only.
- **NO Arbiter Agent**: main thread reads critic findings and decides verdict directly.
- **NO Endless Loops**: max 1 REVISE round-trip; escalate on the 2nd.
- **NO Editing**: never draft or rewrite plan content — route fixes to origin.
- **NO Sketch Plans**: sketch-depth plans are not routed here; return immediately if one arrives.

## Next Skills

- **dispatch-agents**: multi-task execution (independent or sequential) once APPROVED.
- **test-driven-development**: single focused feature once APPROVED.
- **request-plan**: if REVISE traces back to missing content requiring a full re-draft.
