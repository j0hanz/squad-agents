# Agent Primitives — Choosing and Composing

The five ways to run agent work in Claude, compared on the axes that actually drive the choice.

## Table of contents

- [At a glance](#at-a-glance)
- [Claude Code subagent](#claude-code-subagent)
- [Agent team](#agent-team)
- [Agent view](#agent-view)
- [Dynamic workflow](#dynamic-workflow)
- [Managed Agent](#managed-agent)
- [Decision tree](#decision-tree)
- [Composition](#composition)
- [Migration paths](#migration-paths)

---

## At a glance

| | Subagent | Agent team | Agent view | Workflow | Managed Agent |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Invoked by** | Claude, via `Agent` tool | A parent agent | You, from a dashboard | A JS script | External code (API) |
| **Plan lives in** | Claude's context, turn-by-turn | Parent + teammates | Each session | The script | The caller |
| **Context** | Fresh, isolated | Per-teammate | Per-session, persistent | Per-agent, script-held | One run per call |
| **Scale** | A few per turn | A few concurrent | Many sessions | Up to 1,000 agents/run | One run per invocation |
| **Resumable** | No (restarts the turn) | Within session | Yes (background persists) | Yes (within session) | No (single-shot) |
| **Cost model** | Parent token budget | Parent budget, amortized | Per session (quota) | Per run, fans out fast | Per run, platform-billed |
| **Observability** | Transcript in parent | Teammate transcripts | Dashboard + logs | Workflow progress view | Platform run logs |
| **Use when** | Side task floods main context | Parallel independent tasks | Many steered background jobs | Large cross-checked orchestration | API-callable outside a session |
| **Avoid for** | Work needing parallelism at scale | Sequential dependent tasks | One quick delegated task | Anything small | Anything inside a session |

---

## Claude Code subagent

**What:** an isolated worker Claude spawns with the `Agent` tool mid-session. Fresh context, its own system prompt, its own tool surface.

**Lifetime:** one task; returns its final message to the parent and is gone. A new invocation is a new instance with fresh context.

**Why use it:** keep the main thread's context clean (the worker reads 40 files, the parent sees one summary), and encapsulate a reusable narrow role (a `code-reviewer` you invoke across sessions).

**Cost:** counted in the parent session's token budget. A `general-purpose` agent re-derives context from scratch — prefer a typed/named agent when context matters.

**Authoring:** a markdown file with YAML frontmatter in `.claude/agents/` (project) or `~/.claude/agents/` (all projects). Full field catalog in [subagent-spec.md](subagent-spec.md).

**Avoid for:** scheduled jobs or daemons (nothing keeps them alive), and large fan-outs (use a workflow).

---

## Agent team

**What:** a parent agent spawns several teammates that run in parallel and can message each other (`TeamCreate`, `/background`, `SendMessage`).

**Lifetime:** tied to the parent run; the parent closes the team when work is done.

**Why use it:** a handful of *independent* tasks that should run concurrently — e.g. test three hypotheses at once, review four modules in parallel.

**Observability:** each teammate has its own transcript; the parent can read them via `SubagentStop`/`TeammateIdle` lifecycle hooks.

**Avoid for:** sequential dependent steps (a subagent chain is simpler), or scale beyond a few teammates (use a workflow).

---

## Agent view

**What:** a dashboard (`claude agents`) for running and steering **many independent background sessions** from one screen. Each is a full session, not a delegated subtask.

**Lifetime:** background sessions persist across your terminal; a per-user supervisor hosts them. They resume on attach.

**Why use it:** you personally are juggling many parallel jobs (one per PR, one per investigation) and want to dispatch, peek, and answer prompts from a single place.

**Isolation:** edits are auto-moved into a git worktree under `.claude/worktrees/` to avoid conflicts; the worktree is deleted with the session, so merge/push first.

**Avoid for:** a single quick delegation (just spawn a subagent).

---

## Dynamic workflow

**What:** a JavaScript script that orchestrates subagents at scale. Claude writes the script; a runtime executes it in the background. Decisions about what runs next live in the *script*, not in Claude's turn-by-turn judgment.

**Scale:** up to 16 concurrent agents, up to 1,000 per run.

**Why use it:** large, repeatable orchestration — migrate every file in a tree, audit every endpoint, or run cross-checked research where independent agents adversarially review each other's findings (a quality pattern subagents can't express).

**Constraints:** the script has no direct filesystem/shell access (only via agents); subagents always run `acceptEdits` inheriting your allowlist; no mid-run user input; resumable only within the same session.

**Trigger:** include the word `workflow` in the prompt, run a saved/bundled one (`/deep-research`), or use `/effort ultracode`.

**Avoid for:** anything small — the orchestration overhead isn't worth it under a few dozen units.

---

## Managed Agent

**What:** an agent callable from outside any session via the Agent API (`agents.create`, `agents.update`, `agents.invoke`; beta header `managed-agents-2026-04-01`). Your app, a cron, or a webhook invokes it.

**Lifetime:** one invocation = one independent run.

**Why use it:** productionize an agent as a service — something external systems call, not something a human drives in a terminal.

**Config:** `tools[]`, `skills[]`, `mcp_servers[]` arrays plus a permission policy. **`agents.update` replaces arrays wholesale** — omitting an item deletes it silently. See [managed-agents.md](managed-agents.md) and `/claude-api`.

**Avoid for:** anything that should live inside a Claude Code session — use a subagent.

---

## Decision tree

```
Is it invoked from OUTSIDE any session (your app/cron/webhook)?
├─ YES → Managed Agent
└─ NO → Inside a Claude Code session.
   │
   ├─ Does it just need INSTRUCTIONS the model follows inline?
   │     → Skill (not an agent). Use the skill-builder skill.
   │
   ├─ Must a FIXED action fire at a lifecycle point?
   │     → Hook (not an agent). Use the create-hook skill.
   │
   ├─ Is it a LARGE, repeatable orchestration (dozens–hundreds, cross-checked)?
   │     → Dynamic workflow.
   │
   ├─ Are there a FEW INDEPENDENT tasks to run concurrently?
   │     → Agent team (spawned by a parent) or agent view (steered by you).
   │
   └─ Otherwise: a delegated side task or a reusable narrow role
         → Claude Code subagent.
```

---

## Composition

Agents are most effective when they **compose** rather than reimplement:

- **Preload skills** into a subagent (`skills: [name]`) to give it a capability without trusting it to discover one. The skill's full body is injected at startup.
- **Attach hooks** for deterministic guarantees (telemetry, stop-gates, permission enforcement scoped by `agent_type`). Design them with `create-hook`.
- **Reference MCP servers** inline so their tool definitions stay out of the main conversation.
- **Check siblings first.** Before encoding logic in a prompt, ask whether a sibling skill already does it — preload or reference it.

A subagent + a preloaded skill + a `SubagentStop` quality gate is usually better engineering than one giant system prompt.

---

## Migration paths

**Subagent → Managed Agent** (in-session role becomes an external service):
- Lift the system prompt and tool list into the API `tools[]`/`skills[]` arrays.
- Translate permission intent into the agent's permission policy (`always_ask` by default).
- Re-run your test inputs against the deployed agent before pointing callers at it.

**Skill → Subagent** (inline instructions need their own context):
- When the behavior needs isolation, multi-step reasoning, or a distinct tool surface.
- Move the skill body into the agent's system prompt (or preload the skill).

**Subagent → Agent team / workflow** (one role needs to run many times concurrently):
- Team for a few independent runs; workflow for dozens-plus or for cross-checked quality patterns.
- Define per-unit tool surface once; the orchestration layer handles fan-out.
