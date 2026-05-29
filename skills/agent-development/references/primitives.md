# Agent Primitives in Claude

## At a glance

| Dimension | Managed Agent | Claude Code Subagent | Agent Team | Skill + Hooks | Notes | Key Constraint | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Invocation** | External API: agents.create, agents.invoke | Session Agent tool (isolated) | TeamCreate hook (parallel spawn) | Embedded in SKILL.md + hooks.json | Where it lives | API-callable externally vs in-session | External → Managed; In-session → subagent/team/skill |
| **Lifetime** | One invocation = one run | Lives in parent session | Tied to parent agent run | Active for parent session | Duration affects cost model | Single-shot vs persistent | Choose based on invocation model |
| **Permission** | always_ask default; always_allow trusted MCPs | Inherits parent; scope via tools[] | Inherits parent; scope per teammate | Inherits parent; hooks enforce | Escalation rules | Never broad always_allow | Default to least privilege |
| **Tool Surface** | tools[], skills[], mcp_servers[] arrays | Frontmatter tools[] (additive) | Per-teammate tools[] in manifest | No direct surface; shape via hooks | Configuration syntax | Wholesale replace risk on update | Use diff.py before deploy |
| **Cost Model** | Per-run; estimable via cost.py | In parent session budget | In parent; amortized across team | Additive prompt tokens only | Budget tracking | Impacts cost estimation | Use cost.py for planning |
| **Observability** | Platform-side run logs | Transcript in parent; stdout/hooks | TeammateStopped hook transcripts | Hook logs + system prompt traces | Inspection method | How to debug/audit | Varies by primitive |
| **Best for** | API-callable external services | Multi-step reasoning; decomposition | Parallel independent work | Behavior shaping; safety nets | Primary use case | Matches to right primitive | See decision tree |
| **Avoid for** | Inside Claude Code session | Scheduled jobs; daemons | Sequential dependent tasks | Isolated context needs | Anti-pattern | Wrong use leads to waste | See decision tree |

## Managed Agent

**Invocation:** External code calls platform API (agents.create, agents.update, agents.invoke); beta managed-agents-2026-04-01.

**Lifetime:** One invocation = one independent run.

**Permission model:** always_ask default; always_allow only for trusted MCPs.

**Tool surface:** Configured via tools[], skills[], mcp_servers[] arrays (WHOLESALE REPLACED on update).

**Cost:** Per-run; estimable via cost.py.

**Observability:** Platform-side run logs.

**Best for:** API-callable agents called by external apps.

**Avoid for:** Anything that needs to live inside a Claude Code session.

## Claude Code Subagent

**Invocation:** Session-level Agent tool spawns a fresh subagent with isolated context.

**Lifetime:** Lives within parent session; completes when task finishes or times out.

**Permission model:** Inherits parent allowlist; can be scoped further via frontmatter tools[].

**Tool surface:** Frontmatter tools[] array (additive to parent baseline; cannot deny parent-allowed tools).

**Cost:** Counted within parent session token budget.

**Observability:** Transcript visible in parent session; can emit via stdout or custom hooks.

**Best for:** Multi-step reasoning, decomposing complex tasks, isolated reasoning context.

**Avoid for:** Systems that live outside a session (standalone daemons, scheduled jobs).

## Agent Team

**Invocation:** TeamCreate hook (inside another agent's run); teammates spawned in parallel.

**Lifetime:** Lifetime tied to parent agent run; completed when parent closes the team.

**Permission model:** Each teammate inherits parent permissions; can further scope via type.

**Tool surface:** Each teammate has own tools[] config in team manifest.

**Cost:** Counted within parent session; parallel cost is amortized across team members.

**Observability:** Individual teammate transcripts available via TeammateStopped hooks.

**Best for:** Parallel independent work (e.g., testing multiple hypotheses, concurrent reviews).

**Avoid for:** Sequential dependent tasks (use subagents instead).

## Skill + Hooks (no agent)

**Invocation:** Embedded in parent agent behavior via SKILL.md frontmatter and hooks.json.

**Lifetime:** Active for duration of parent session; teardown on session end.

**Permission model:** Inherits parent; hooks can enforce scoped policies.

**Tool surface:** No direct tool surface; shaping done via hooks and system prompt injection.

**Cost:** Additive prompt tokens only (no new runs).

**Observability:** Via hook logs and system prompt traces in parent transcript.

**Best for:** Behavior shaping, safety guardrails, cost/latency optimization, testing harnesses.

**Avoid for:** Tasks that need independent context or isolated reasoning.

## Decision Tree

```
Do you need a separate API endpoint to invoke your agent?
├─ YES → Managed Agent
│         (External code calls agents.create, agents.invoke)
│         See: Managed Agent section above
│
└─ NO → Is this inside a Claude Code session?
   │
   ├─ YES → Is your agent a behavior modifier (not an independent worker)?
   │  │
   │  ├─ YES → Skill + Hooks
   │  │         (Hooks shape behavior; no separate context)
   │  │         See: Skill + Hooks section above
   │  │
   │  └─ NO → Do you need parallel, independent work?
   │     │
   │     ├─ YES → Agent Team
   │     │         (TeamCreate; spawned in parallel)
   │     │         See: Agent Team section above
   │     │
   │     └─ NO → Claude Code Subagent
   │             (Multi-step reasoning; isolated context)
   │             See: Claude Code Subagent section above
   │
   └─ NO → Is this a long-running, persistent system?
      │
      ├─ YES → Agent Team with --background flag
      │         (Persistent teammates; parent-spawned)
      │         See: Agent Team section above
      │
      └─ NO → Managed Agent
              (API-callable for external systems)
              See: Managed Agent section above
```

## Migration Paths

**Subagent → Managed Agent:**
- Extract system prompt + tools from subagent frontmatter
- Preserve permission rules; translate to agent.tools[] allowlist
- Preserve behavioral constraints from original prompt
- Use cost.py to estimate per-run cost
- Test with existing test cases before migrating users

**Skill + Hooks → Subagent:**
- When behavior shaping needs its own context
- When you need to decompose complex multi-step logic
- When isolation from parent session is required
- Convert hook rules to frontmatter tools[] allowlist
- Document expected composition with sibling skills

**Subagent → Team:**
- When concurrent independent runs are needed
- When you want to parallelize work across multiple teammates
- Use TeamCreate to spawn teammates; each teammate inherits parent permissions
- Define per-teammate tools[] in team manifest
- Amortize cost across parallel runs via parent session budget
