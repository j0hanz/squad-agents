---
name: create-agent
description: "Design, write, test agents and subagents. Trigger on 'build agent', 'create subagent', 'agent prompt', 'multi-agent', 'managed agent', 'agent not working', 'agent keeps triggering wrong thing'. Also: agent role selection, permission scoping, tool surface design, choosing between subagent/team/workflow/managed agent."
disable-model-invocation: false
argument-hint: '[what the agent should do]'
allowed-tools: Bash(python *) Bash(python3 *)
---

# Create Agent

**Mindset:** Agents are expensive primitives. Use only for isolation, parallelism, or reusable narrow roles. For inline instructions, use a **skill**. For fixed lifecycle actions, use a **hook**.

Design every agent through seven strict decisions. Output must be in `markdown-kv` format to minimize noise.

## 0. Prerequisite Check

- **Context Flooding:** Subagent
- **Reusable Role:** Subagent
- **Independent Parallel Tasks:** Agent team / view
- **Complex Orchestration / Multi-Agent:** Workflow (scatter-gather, saga, state machines)
- **External API Call:** Managed Agent
- **Inline Instructions:** Skill
- **One-off Task:** No agent

## 1. Job Definition

- **Format:** `This agent <verb + object> so that <main-thread benefit>.`
- **Constraint:** One sentence. Narrow scope.
- **Split Rule:** If the job contains `AND` connecting unrelated tasks, split into two agents.

## 2. Primitive Selection

- **Subagent:** Delegated side tasks; isolated context. Returns a single final message.
- **Agent Team:** Independent tasks running concurrently.
- **Workflow:** Large-scale orchestration, transaction management, scatter-gather, saga patterns, compensation logic, circuit breakers.
- **Managed Agent:** API-callable service outside any session.

## 3. System Prompt (`markdown-kv` format)

Agent instructions MUST be generated in strict `markdown-kv` format.

- **Role:** Who the agent is and its single job.
- **Objective:** The concrete goal.
- **Procedure:** Ordered imperative steps.
- **Fallback:** Dead-letter/timeout handling (crucial for multi-agent workflows).
- **Boundaries:** Explicit "Do not" boundaries.
- **Output:** Exact final message schema.

## 4. Tools & Permissions

- **Default:** Least privilege. Read-only (`Read, Grep, Glob`).
- **Escalation:** Justify `Edit, Write, Bash`.
- **Spawn Rights:** Allowlist via `Agent(worker, ...)` or omit to forbid spawning.
- **Permission Mode:** `default` (prompts), `plan` (read-only), `acceptEdits` (auto-accept files), `bypassPermissions` (dangerous).

## 5. Model & Effort

- **Haiku:** Classification, simple search/dispatch.
- **Sonnet:** Implementation, tool orchestration.
- **Opus:** Adversarial reasoning, security bounds, deep root-cause analysis.
- **Effort:** Scale to match complexity.

## 6. Composition & State

- **Isolation:** `worktree` for writes that shouldn't touch parent checkout.
- **Skills:** `skills: [name]` to preload behaviors natively.
- **Hooks:** Lifecycle guards (`SubagentStop`).
- **Memory:** Scoped persistence (`user|project|local`).

## 7. Delivery & Testing

**Note on resolution:** use the absolute path of the directory containing this `SKILL.md` file as `<skill-dir>` (or `$CLAUDE_PLUGIN_ROOT/skills/create-agent` if available).

1. **Deliver:** Complete agent definition in `markdown-kv` format. State the file path.
2. **Validate:** Run `python <skill-dir>/scripts/validate_agent.py path/to/your-agent.md`. MUST yield zero ERRORs before presentation.
3. **Test Prompt:** Provide a concrete test input and expected output schema.
4. **Verification:** **Invoke `verification-before-completion`** to ensure the new agent performs its role correctly and adheres to its defined boundaries.

---

## Expert Patterns

- **Recursive Decomposition:** If an agent definition exceeds 100 lines or handles >3 distinct logic branches, decompose it into a **team** of simpler agents or a **workflow** with clear state transitions.
- **Taint-Aware Prompts:** For security or data-processing agents, explicitly define "untrusted" sources (e.g., user input, external APIs) and "trusted" sinks (e.g., database, shell). The procedure must include a mandatory sanitization step.
- **Circuit Breakers:** For long-running or autonomous agents, the procedure must include explicit "Stop and Report" conditions for timeouts, tool failures, or if the agent reaches a state where it lacks necessary context.
- **State Handoff:** In workflows, never assume the next agent knows the full history. Explicitly define the "Context Payload" that is passed between agents.

## Common Failure Modes

- **Context Bleed:** The agent is given too much irrelevant context from the parent session, leading it to make assumptions about files or state it shouldn't access. **Fix:** Be aggressive with `worktree` isolation and explicit file allowlists.
- **Tool Blindness:** The agent has the correct tools but the prompt focuses on "what to do" without explaining "how to use the tools to do it." **Fix:** Include tool-specific instructions in the Procedure (e.g., "Use `Grep` to find X before attempting `Edit`").
- **Infinite Looping:** An agent calls itself or triggers a cycle in a multi-agent workflow without a clear decrementing counter or termination condition. **Fix:** Always include a `max_turns` or `deadline` in the fallback logic.
- **Permission Bloat:** Granting `bypassPermissions` or `acceptEdits` by default. **Fix:** Always start with `default` permissions and only escalate if the specific task requires it and the user is informed.
