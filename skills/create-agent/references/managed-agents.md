# Managed Agents — API-Callable Agents

A **Managed Agent** is an agent your own code invokes through the Agent API, outside any Claude Code session. Use it to productionize an agent as a service: a webhook handler, a scheduled job, a backend endpoint.

> This file is a design-level orientation. For the authoritative, current API surface (exact request/response shapes, SDK calls, model IDs, beta headers), use the **`/claude-api`** reference — it tracks the live API. Treat this file as *how to think about* Managed Agents, not as the API contract.

## Table of contents

- [When to choose a Managed Agent](#when-to-choose-a-managed-agent)
- [Lifecycle](#lifecycle)
- [Configuration shape](#configuration-shape)
- [The wholesale-replace trap](#the-wholesale-replace-trap)
- [Permission policy](#permission-policy)
- [Secrets](#secrets)
- [Testing before pointing callers at it](#testing-before-pointing-callers-at-it)

---

## When to choose a Managed Agent

Choose it when the invoker is **external code**, not a human in a terminal or Claude mid-session:

- An app endpoint that runs an agent per request.
- A cron / scheduled task.
- A webhook (PR opened → review agent runs).

If the invoker is Claude during a session, you want a **subagent**. If it's you steering many jobs, **agent view**. See [primitives.md](primitives.md).

---

## Lifecycle

| API call | Purpose |
| :--- | :--- |
| `agents.create` | Register an agent: system prompt, tools, skills, MCP servers, permission policy. |
| `agents.update` | Modify an existing agent. **Replaces array fields wholesale** — see below. |
| `agents.invoke` | Run the agent once. One invocation = one independent run. |

The beta header for this surface is `managed-agents-2026-04-01`. Confirm the current header and call signatures via `/claude-api`.

---

## Configuration shape

A Managed Agent config carries, conceptually:

- **System prompt** — same craft as a subagent prompt. See [system-prompt-craft.md](system-prompt-craft.md).
- **`tools[]`** — the tool allowlist.
- **`skills[]`** — composed skills. **Pin exact versions** — never `latest`, which moves under you and makes runs non-reproducible.
- **`mcp_servers[]`** — external tool integrations.
- **Permission policy** — `always_ask` / `always_allow` per toolset/server.

---

## The wholesale-replace trap

**`agents.update` replaces array fields wholesale.** If you send a `tools[]` array that omits a tool the agent currently has, that tool is **silently deleted** — no error, no warning. The same applies to `skills[]` and `mcp_servers[]`.

Always:

1. Read the agent's current config first.
2. Build the new arrays from the current ones plus your change.
3. Diff old vs. new and explicitly confirm every removal is intended before calling `update`.

This is the single most common way a Managed Agent silently loses a capability in production.

---

## Permission policy

Default everything to **`always_ask`**. Reserve **`always_allow`** for a *single, explicitly pinned, fully-trusted* MCP server whose code you control. Never apply `always_allow` broadly across an `agent_toolset` — a broad always-allow turns the agent into an unsupervised actor with whatever blast radius its tools permit.

Least privilege is the same discipline as for subagents (see SKILL.md Step 4): start read-only, escalate only with per-capability justification.

---

## Secrets

Never inline credentials, API keys, or tokens in an agent config. Configs appear in logs, diffs, and API responses. Reference secrets through environment variables or your platform's secret store.

---

## Testing before pointing callers at it

A Managed Agent runs unattended, so behavioral bugs surface in production unless you catch them first:

1. Invoke it directly (not through your app) on representative inputs, including an edge case and an input it should refuse.
2. Verify the output contract is stable and parseable — your calling code depends on its shape.
3. Confirm it terminates and stays within its tool surface.
4. Only then wire it into the caller.

See [testing-agents.md](testing-agents.md) for the eval-first method.
