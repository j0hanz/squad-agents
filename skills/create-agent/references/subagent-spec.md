# Claude Code Subagent — Full Spec

The complete authoring reference for `.claude/agents/*.md` subagents.

## Table of contents

- [File format](#file-format)
- [Frontmatter fields](#frontmatter-fields)
- [Permission modes](#permission-modes)
- [Tools available to subagents](#tools-available-to-subagents)
- [Advanced Role Profiles](#advanced-role-profiles)
- [Restricting which agents it can spawn](#restricting-which-agents-it-can-spawn)
- [Model resolution order](#model-resolution-order)
- [Scope & priority](#scope--priority)
- [What loads at startup](#what-loads-at-startup)
- [Invocation modes](#invocation-modes)
- [Foreground vs background](#foreground-vs-background)
- [Fork mode](#fork-mode)
- [Plugin subagent limitations](#plugin-subagent-limitations)

---

## File format

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices. Use proactively after code changes.
tools: Read, Grep, Glob, Bash
model: sonnet
---

System prompt here. This REPLACES the default Claude Code system prompt entirely.
```

Subagents are loaded at session start. Changes made through `/agents` apply immediately; edits to files on disk require a restart. Identity comes from the `name` field, not the filename.

---

## Frontmatter fields

| Field             | Required | Description                                                                                                                           |
| :---------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------ |
| `name`            | Yes      | Unique id, lowercase + hyphens. Used as `agent_type` in hooks. Need not match filename.                                               |
| `description`     | Yes      | When Claude should delegate here. Include "use proactively" to encourage auto-delegation.                                             |
| `tools`           | No       | Allowlist of tools. Inherits **all** tools if omitted. `Agent(worker, researcher)` syntax restricts which subagents it may spawn.     |
| `disallowedTools` | No       | Denylist removed from inherited/specified tools. Applied **before** `tools` if both are set.                                          |
| `model`           | No       | `sonnet` · `opus` · `haiku` · a full model ID (`claude-opus-4-8`) · or `inherit`. Default: `inherit`.                                 |
| `permissionMode`  | No       | See [permission modes](#permission-modes). Ignored for plugin subagents.                                                              |
| `maxTurns`        | No       | Max agentic turns before the subagent stops.                                                                                          |
| `skills`          | No       | Skills to preload (full content injected, not just description). Cannot preload skills with `disable-model-invocation: true`.         |
| `mcpServers`      | No       | MCP servers for this subagent: a server-name string (reuses parent connection) or an inline definition. Ignored for plugin subagents. |
| `hooks`           | No       | Lifecycle hooks scoped to this subagent. `Stop` → auto-converted to `SubagentStop`. Ignored for plugin subagents.                     |
| `memory`          | No       | Persistent memory scope: `user` · `project` · `local`.                                                                                |
| `background`      | No       | `true` = always run as a background task. Default `false`.                                                                            |
| `effort`          | No       | `low` · `medium` · `high` · `xhigh` · `max`. Default: inherits session.                                                               |
| `isolation`       | No       | `worktree` = run in a temp git worktree, isolated from the parent checkout. Auto-cleaned if no changes.                               |
| `color`           | No       | Display color (`red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`).                                                 |
| `initialPrompt`   | No       | Auto-submitted first user turn when the agent runs as the **main** session (via `--agent`/`agent` setting).                           |

---

## Permission modes

| Mode                | Behavior                                                                                |
| :------------------ | :-------------------------------------------------------------------------------------- |
| `default`           | Standard permission checking with prompts.                                              |
| `acceptEdits`       | Auto-accept file edits and common filesystem commands in the working dir.               |
| `auto`              | Background classifier reviews commands and protected-dir writes.                        |
| `dontAsk`           | Auto-deny prompts (explicitly allowed tools still work).                                |
| `bypassPermissions` | Skip all prompts. **Allows writes to `.git`, `.claude`, `.vscode`** — use with caution. |
| `plan`              | Read-only exploration (plan mode).                                                      |

If the parent uses `bypassPermissions` or `acceptEdits`, that takes precedence and can't be overridden. If the parent uses `auto`, the subagent inherits it and frontmatter `permissionMode` is ignored.

**Headless trap:** background and `-p` agents auto-deny permission prompts. An agent that needs a tool which would prompt will silently stall. Either grant the tool via an allowlist / `acceptEdits`, or keep the agent in the foreground.

---

## Tools available to subagents

Subagents can use the built-in tools **except** these (unavailable even if listed):

`Agent` · `AskUserQuestion` · `EnterPlanMode` · `ExitPlanMode` (unless `permissionMode: plan`) · `ScheduleWakeup` · `WaitForMcpServers`

Control access with `tools` (allowlist) or `disallowedTools` (denylist). If both are set, `disallowedTools` applies first.

Common profiles:

| Profile           | Tools                                              |
| :---------------- | :------------------------------------------------- |
| Read-only search  | `Read, Grep, Glob`                                 |
| Reviewer/reporter | `Read, Grep, Glob` (+ analysis; no `Edit`/`Write`) |
| Implementer       | `Read, Edit, Write, Bash, Glob, Grep`              |
| Orchestrator      | above + `Agent(worker, researcher)`                |

---

## Advanced Role Profiles

Specialized agent configurations for complex workflows and "Team of Teams" orchestration.

| Role          | Responsibilities                                                                                                                                                   | Capabilities                                                                                                                                                                 |
| :------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FeatureLead` | Orchestrates complex features by breaking them down into sub-tasks. Manages worker agents through hierarchical dispatch. Ensures alignment across multiple agents. | Permitted to use `multi-agent-dispatch` and `multi-agent-development` skills. Utilizes the **Shared Context Blackboard** for inter-agent communication and state management. |

---

## Restricting which agents it can spawn

Applies only when the agent runs as the main thread (via `--agent`).

```yaml
tools: Agent(worker, researcher), Read, Bash
```

Allowlist only — other agent types can't be spawned. Use bare `Agent` to allow spawning any subagent; omit `Agent` entirely to forbid spawning. Block specific agents session-wide via `permissions.deny`: `["Agent(Explore)"]`, or CLI `--disallowedTools "Agent(Explore)"`.

---

## Model resolution order

1. `CLAUDE_CODE_SUBAGENT_MODEL` env var (if set)
2. Per-invocation `model` parameter
3. Subagent definition's `model` frontmatter
4. Main conversation's model

---

## Scope & priority

| Location             | Scope                   | Priority    |
| :------------------- | :---------------------- | :---------- |
| Managed settings     | Organization-wide       | 1 (highest) |
| `--agents` CLI flag  | Current session         | 2           |
| `.claude/agents/`    | Current project         | 3           |
| `~/.claude/agents/`  | All projects            | 4           |
| Plugin `agents/` dir | Where plugin is enabled | 5 (lowest)  |

Higher priority wins on name conflicts. Directories scan recursively; keep `name` unique within a scope.

---

## What loads at startup

For non-fork subagents:

| What                           | Loads?                            |
| :----------------------------- | :-------------------------------- |
| Subagent's own system prompt   | Yes                               |
| Full Claude Code system prompt | No                                |
| `CLAUDE.md` + memory hierarchy | Yes (except `Explore` and `Plan`) |
| Git status (parent snapshot)   | Yes (except `Explore` and `Plan`) |
| Skills listed in `skills:`     | Yes (full content injected)       |
| Parent conversation history    | No                                |
| Previously invoked skills      | No                                |

---

## Invocation modes

**Natural language** — Claude decides whether to delegate:

```
Use the test-runner subagent to fix failing tests
```

**@-mention** — guarantees it runs for one task:

```
@agent-code-reviewer look at the auth changes
```

(`@agent-<name>` local; `@agent-<plugin>:<name>` for plugin subagents.)

**Session-wide** — the whole session runs as that agent:

```bash
claude --agent code-reviewer
```

**Persistent default** in `.claude/settings.json`: `{ "agent": "code-reviewer" }` (CLI flag overrides).

**CLI-defined** (session-only, not saved): `claude --agents '{ "code-reviewer": { "description": "...", "prompt": "...", "tools": ["Read","Grep"], "model": "sonnet" } }'` — same fields as frontmatter, but `prompt` replaces the markdown body.

---

## Foreground vs background

|                          | Foreground    | Background  |
| :----------------------- | :------------ | :---------- |
| Blocks main conversation | Yes           | No          |
| Permission prompts       | Passed to you | Auto-denied |
| Run concurrently         | No            | Yes         |

Background a task by asking Claude to "run this in the background", pressing `Ctrl+B`, or `background: true` in frontmatter. Disable all background tasks: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`.

---

## Fork mode

Experimental (`CLAUDE_CODE_FORK_SUBAGENT=1`, v2.1.117+). A **fork inherits the full conversation history** instead of starting fresh — same system prompt, tools, model, and messages as the main session. Use when the worker genuinely needs everything that came before; use a named subagent when a clean slate is better. A fork can't spawn further forks.

---

## Plugin subagent limitations

Plugin subagents **ignore** `hooks`, `mcpServers`, and `permissionMode` frontmatter. Define those at the project level if a plugin-distributed agent needs them.
