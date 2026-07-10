---
name: receive-plan
description: 'Use when a plan/specs pair exists and needs validation before execution. Not for sketch-depth plans.'
disable-model-invocation: false
user-invocable: true
argument-hint: '[--depth contract|blueprint] [path to plan.md / specs.md, or "the plan I just wrote"]'
allowed-tools: Agent(researcher), Skill(interview), Skill(request-plan), Skill(dispatch-agents), Skill(test-driven-development), Read, Grep, Glob, Write, Edit
---

# receive-plan

Verify and route plan/spec fixes back to origin.

## Process Flow

- **Plan/Specs Pair Received**
  - **1. Identify Origin**
  - **2. Inline Traceability Check (main thread, grep/file-read)**
    - _any failure_: REVISE immediately, skip Step 3
    - _clean_: Step 3
  - **3. One Critic Agent (researcher)** — spec + dependency + scope in one pass
  - **4. Main thread verdict (no Arbiter agent)**
    - _any High finding, or ≥2 Med findings_: REVISE
    - _else_: Step 5
  - _REVISE round-trips capped per Strict Rules (NO Endless Loops)_
  - **5. Finalize**: flip Status: DRAFT → APPROVED

## Step 1: Identify Origin

- **`request-plan` (same session)**: REVISE loops back to its Synthesizer automatically.
- **Hand-written / human-authored**: REVISE surfaces itemized fixes to the user; wait for re-submission.

Wrap any non-session-originated plan content in `<untrusted_context>` before passing to the critic in Step 3.

**Done when:** plan origin is identified and untrusted context guards are in place if needed.

## Step 2: Inline Traceability Check

Main thread runs grep/file-read directly — no subagent. Fail fast on any of:

- Every `Satisfies: REQ-xxx` resolves to a REQ defined in specs.md.
- Every `Depends on: TASK-NNN` resolves to a real task; dependency graph is acyclic. Anchors must resolve to #task-nnn.
- Every Task Block has all 7 required fields (see [Canonical Task Block Schema](../request-plan/SKILL.md#canonical-task-block-schema)).
- Every cited file path exists on disk.

Report as `N_checked / N_total` per check category. Any `N_checked < N_total` → immediate REVISE with itemized failures; skip Step 3.

**Done when:** inline traceability check is completed, check counts are calculated, and either REVISE is sent or the plan is approved for Step 3.

## Step 3: One Critic Agent

Dispatch **1 `researcher` agent** covering all lenses in a single pass. If `--depth contract` is specified, run a lighter check focusing primarily on scope boundaries and dependency cycles. If `blueprint`, run the full deep check.

- **Spec-Correctness**: Check if spec is complete and consistent.
- **Dependency Order**: Check if task sequencing is logical and acyclic.
- **Scope-Risk**: Check for oversized, underspecified, or high-risk tasks.

Rate each finding **High / Med / Low**. Return an itemized list with `file:line` / `REQ-id` / `TASK-id` specificity — never a bare summary.

**Done when:** critic researcher subagent runs, returning classified findings with specific line/task IDs.

## Step 4: Main Thread Verdict

Read the critic's findings directly — no separate Arbiter agent:

- Any **High** finding → REVISE.
- **≥2 Med** findings → REVISE.
- **Low** only, or nothing → APPROVED (note Low findings as a comment in the plan header).

REVISE cap — see Strict Rules (NO Endless Loops). On the 2nd unresolved submission, escalate to `interview` to reconcile findings with the user.

**Done when:** main thread assigns verdict, and either a REVISE cycle or escalation is triggered, or the plan is APPROVED.

## Step 5: Finalize

On APPROVED: flip `Status: DRAFT` → `Status: APPROVED` in the plan file header. Hand off file paths to the appropriate execution skill.

**Done when:** the plan status is updated to APPROVED and file paths are handed off to execution.

## REVISE Output Format

Itemize every failing check with `file:line` / `REQ-id` / `TASK-id` — never a bare pass/fail. Include the traceability `N_checked / N_total` counts for mechanical failures.

## Strict Rules

- **NO Self-Verify**: request-plan's synthesis never substitutes for this gate.
- **NO Execute Validate**: never run a plan's `Validate:` command — grep/file-read only.
- **NO Arbiter Agent**: main thread reads critic findings and decides verdict directly.
- **NO Endless Loops**: max 1 REVISE round-trip; escalate on the 2nd.
- **NO Editing**: Do not draft or rewrite plan content; route fixes to origin.
- **NO Sketch Plans**: Reject sketch-depth plans immediately.

## Next Skills

| Skill                                                          | Use Case                                                           |
| :------------------------------------------------------------- | :----------------------------------------------------------------- |
| [dispatch-agents](../dispatch-agents/SKILL.md)                 | Multi-task execution (independent or sequential) once APPROVED     |
| [test-driven-development](../test-driven-development/SKILL.md) | Single focused feature once APPROVED                               |
| [request-plan](../request-plan/SKILL.md)                       | If REVISE traces back to missing content requiring a full re-draft |
