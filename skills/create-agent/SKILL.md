---
name: create-agent
description: "Design, write, test agents and subagents. Trigger on 'build agent', 'create subagent', 'agent prompt', 'multi-agent system design', 'managed agent', 'agent not working', 'agent keeps triggering wrong thing'. Also: agent role selection, permission scoping, tool surface design, choosing between subagent/team/workflow/managed agent."
disable-model-invocation: false
argument-hint: '[what the agent should do]'
allowed-tools: Bash(python *) Bash(python3 *)
---

# create-agent

Agents are high-cost primitives. Use only for isolation, parallelism, or reusable roles. Use **skills** for inline instructions and **hooks** for fixed lifecycle actions.

## When to Use

```dot
digraph when_to_use {
    rankdir=TB;
    node [shape=box, style=rounded, fontname="Helvetica"];
    edge [fontname="Helvetica", fontsize=10];

    Need [label="What do you need?", shape=diamond];

    Need -> "Skill" [label="inline instructions"];
    Need -> "Hook" [label="fixed lifecycle action"];
    Need -> "Agent Primitive" [label="isolation, parallelism,\nor reusable role"];

    "Agent Primitive" -> "Subagent" [label="context isolation"];
    "Agent Primitive" -> "Agent Team" [label="parallel tasks"];
    "Agent Primitive" -> "Workflow" [label="orchestration"];
    "Agent Primitive" -> "Managed Agent" [label="external API"];
}
```

## Process Flow

```dot
digraph create_agent {
  rankdir=TB;
  node [shape=box, style=rounded, fontname="Helvetica"];
  edge [fontname="Helvetica", fontsize=10];

  Step0 [label="0. Decision Tree\n(Select Primitive)"];
  Step1 [label="1. Job Definition"];
  Step2 [label="2. System Prompt\n(markdown-kv)"];
  Step3 [label="3. Tools & Permissions"];
  Step4 [label="4. Model & Effort"];
  Step5 [label="5. Composition\n(Isolation/Memory)"];
  Step6 [label="6. Validation\n(validate_agent.py)"];

  Step0 -> Step1 -> Step2 -> Step3 -> Step4 -> Step5 -> Step6;
}
```

## 0. Decision Tree

- **Context Flooding / Isolation:** Subagent
- **Reusable Role:** Subagent
- **Parallel Tasks:** Agent Team
- **Orchestration/State Machine:** Workflow (Saga, Scatter-Gather)
- **External API:** Managed Agent
- **Inline Logic:** Skill

## 1. Procedure: 7 Strict Decisions

1. **Job Definition:** "This agent <verb + object> so that <main-thread benefit>." (One sentence).
2. **Primitive Selection:** Subagent | Agent Team | Workflow | Managed Agent.
3. **System Prompt (markdown-kv):**
   - Read `references/system-prompt-craft.md` for instructions on writing effective agent prompts.
   - **Role:** Specific persona and single job.
   - **Objective:** Concrete measurable goal.
   - **Procedure:** Ordered imperative steps.
   - **Fallback:** Timeout/Dead-letter handling.
   - **Boundaries:** Explicit "Do Not" rules.
   - **Output:** Exact final message schema.
4. **Tools & Permissions:** Default to Read-only. Escalate to `Edit, Write, Bash` only if justified. Select permission mode: `default | plan | acceptEdits | bypassPermissions`.
5. **Model & Effort:**
   - Haiku (Classification/Dispatch)
   - Sonnet (Implementation/Orchestration)
   - Opus (Security/Deep Root-Cause)
6. **Composition:** Define `worktree` isolation, `skills: []` to preload, and `memory` scope.
7. **Validation:**
   - Run `validate_agent.py`.
   - Run `verification-before-completion`.
   - Ensure `description` has zero overlap with sibling skills.

## Expert Patterns

- **Recursive Decomposition:** If prompt > 100 lines or >3 branches, split into a team/workflow.
- **Taint-Awareness:** Explicitly define "Untrusted Sources" and "Trusted Sinks".
- **Circuit Breakers:** Mandatory "Stop and Report" conditions for timeouts or tool failures.
- **State Handoff:** Define the "Context Payload" for workflows.

## Common Failure Modes

- **Context Bleed:** Too much irrelevant parent history. Use `worktree` and allowlists.
- **Tool Blindness:** Focus on "what" without tool "how". Add tool-specific steps to Procedure.
- **Infinite Loops:** Missing termination counters in multi-agent flows.
- **Permission Bloat:** Using `bypassPermissions` by default.
  s:\*\* Missing termination counters in multi-agent flows.
- **Permission Bloat:** Using `bypassPermissions` by default.
