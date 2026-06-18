---
name: multi-agent-development
description: "For tasks with dependencies between them: execute a multi-task plan one task at a time, delegating each to a focused general-purpose implementer subagent and running two review gates (spec compliance, then code quality) before advancing. Trigger on 'implement the plan', 'execute spec', 'agentic development'."
disable-model-invocation: false
argument-hint: '[path to plan file]'
---

# multi-agent-development

Orchestrate sequential task execution with zero context pollution and high quality-assurance.

## When to Use

```dot
digraph when_to_use {
    rankdir=TB;
    node [shape=box, style=rounded, fontname="Helvetica"];
    edge [fontname="Helvetica", fontsize=10];

    TaskType [label="Task Relationship", shape=diamond];

    TaskType -> "Sequential (this skill)" [label="Dependencies or\nshared state"];
    TaskType -> "Parallel (multi-agent-dispatch)" [label="Independent\ntasks"];

    "Sequential (this skill)" [shape=box];
    "Parallel (multi-agent-dispatch)" [shape=box];
}
```

## Process Flow

```dot
digraph multi_agent_dev {
  rankdir=TB;
  node [shape=box, style=rounded, fontname="Helvetica"];
  edge [fontname="Helvetica", fontsize=10];

  Start [label="Start Loop (Per Task)"];
  Phase1 [label="Phase 1: Implement\n(General-purpose subagent)"];
  Phase2 [label="Phase 2: Spec Compliance\n(Read-only reviewer)"];
  Phase3 [label="Phase 3: Code Quality\n(Read-only auditor)"];
  Next [label="Next Task?", shape=diamond];
  Final [label="Final Validation\n(Test & Verify)"];

  Start -> Phase1 -> Phase2;
  Phase2 -> Phase3 [label="SPEC_PASS"];
  Phase2 -> Phase1 [label="SPEC_FAIL", style=dashed];

  Phase3 -> Next [label="QUALITY_PASS"];
  Phase3 -> Phase1 [label="CRITICAL / IMPORTANT", style=dashed];

  Next -> Start [label="yes"];
  Next -> Final [label="no"];
}
```

## NEVER Do This

- **NEVER** skip Phase 2 or 3 to save time. **WHY:** Bypassing gates leads to regression and spec drift.
- **NEVER** trust a summary. Verify actual code changes yourself.
- **NEVER** reuse subagents across tasks. **WHY:** Context pollution from previous tasks will cause hallucinations.
- **NEVER** dispatch a reviewer without reading the prompt file first. **WHY:** Reference paths are NOT automatically resolved by subagents; you must load the text.
- **NEVER** start implementation without verifying **disjoint file sets**. **WHY:** Parallel or sequential tasks must not overlap on the same files unless dependencies are explicitly managed.

## Decision Gate

- **Dependencies or shared state?** → **Sequential** (This skill).
- **Independent tasks?** → **Parallel** (`multi-agent-dispatch`).

## Partitioning & Scope

Before starting Phase 1, you MUST:

1. Identify all files each task in the plan will touch.
2. Verify no two tasks touch the same file unless they are strictly ordered.
3. If overlap is found, you MUST consolidate those tasks or ensure the downstream task receives the upstream task's commits as context.

## The Core Loop (Per Task)

Execute Phases 1 → 2 → 3 in strict order.

### Phase 1: Implement

- Dispatch a `general-purpose` subagent with `isolation: \"worktree\"`.
- **Prompt Contract:** Carry `SCOPE`, `OBJECTIVE`, `CONTEXT`, `CONSTRAINTS`.
- **Outcome:** `DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`.

### Phase 2: Spec Compliance Gate

- **MANDATORY**: Read `references/spec-reviewer-prompt.md` and use its content as the prompt for the Reviewer.
- Dispatch a read-only `general-purpose` agent as Reviewer.
- **Contract:** Expect `VERDICT: [SPEC_PASS | SPEC_FAIL]`, `MISSING_REQUIREMENTS`, `EXTRA_WORK`.
- **Check:** Did implementer build everything? Anything extra?
- **Failure:** Dispatch implementer to fix. Max 2 attempts before escalating as BLOCKED.

### Phase 3: Code Quality Gate

- **MANDATORY**: Read `references/quality-reviewer-prompt.md` and use its content as the prompt for the Quality Auditor.
- Dispatch a read-only `general-purpose` agent as Quality Auditor.
- **Contract:** Expect `VERDICT: [QUALITY_PASS | CRITICAL | IMPORTANT | MINOR]`, `CRITICAL_ISSUES`, `IMPORTANT_ISSUES`.
- **Check:** Responsibility, decomposition, error handling, test coverage.
- **Severity:** `CRITICAL` (Block), `IMPORTANT` (Block), `MINOR` (Log).

## Final Validation

Advance only after Phase 3 passes. After ALL tasks pass:

1. `npm test && npm run validate`
2. Invoke `verification-before-completion`

## Operational Rules

- **Fresh agent per task.**
- **Prompt Discipline:** Subagents start cold. Embed every fact.
- **Commit Baseline:** Always provide `Baseline commit` and `Implementation commit` to reviewers for precise diffing.
