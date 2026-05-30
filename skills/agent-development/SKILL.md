---
name: agent-development
description: |
  Use when building, testing, auditing, or debugging agents — Managed Agents, Claude Code subagents, agent teams, skill composition, or behavior shaping. Triggers on: "build an agent", "create a subagent", "multi-agent pipeline", "agent prompt", "agent permissions", "agent toolset", "agent system prompt", "spawn an agent", or any mention of Managed Agents, Claude API agents, or designing agent workflows.
disable-model-invocation: true
allowed-tools: Bash(python *) Bash(python3 *)
---

## Core Philosophy

Building agents is a **Process** task. Configuration formats must match API expectations exactly (low freedom), while system prompts and hook designs benefit from iteration (medium freedom). We use an eval-first loop: define the behavioral constraints, baseline the tests with hook-based assertions, build the agent, and measure.

Compose first; build only where no sibling skill exists. The workspace has 20 sibling skills — running `scripts/recommend-skills.py` is part of Phase 1, not an afterthought.

## NEVER

- **NEVER test agent behavior changes directly in production** — use `simulate.py` with `--sandbox` first; production agents can make irreversible API calls, send real messages, or charge real money
- **NEVER grant `computer` or `bash` tools to an agent without explicit per-task justification** — these tools can exfiltrate data and modify the host; start with read-only tools and escalate only when required
- **NEVER inline credentials or secrets in agent config** — agent configs appear in logs, diffs, and API responses; use environment variable references

## Critical Anti-Patterns

| Rule                                                                               | Why                                                                                                            |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **NEVER omit items during a Managed Agent update**                                 | `agents.update` replaces arrays wholesale — omitting a tool/skill/MCP silently deletes it                      |
| **NEVER pin custom skills to `latest` in production**                              | Pin exact versions; `latest` moves under you                                                                   |
| **NEVER apply `always_allow` broadly**                                             | Default `always_ask` for `agent_toolset`; `always_allow` only for explicitly pinned, fully trusted MCP servers |
| **NEVER write a blocking hook when a non-blocking one solves it**                  | CI/CD pipelines, `-p`, and `/loop` cannot process interactive prompts — blocking hooks silently stall automation |
| **NEVER skip `diff.py` before deploy**                                             | Deletions are silent in API responses; applies to subagents and plugin manifests too                           |
| **NEVER use the `Agent` tool's `general-purpose` for tasks a typed subagent fits** | Re-derives context cold — more expensive                                                                       |
| **NEVER configure hooks that prompt the user**                                     | Breaks headless mode (`-p` and `/loop` flows) — unattended automation cannot respond to prompts                |
| **NEVER trust LLM-as-judge for deterministic checks**                              | Use a `PreToolUse` observer hook instead; LLM-judge is for output quality only                                 |

---

## Phase 0: Pick the Right Primitive

```
trigger: API-callable from external code          primitive: Managed Agent
trigger: spawned by Claude during a session       primitive: Claude Code subagent
trigger: long-running parallel workers            primitive: Agent team (/background, TeamCreate)
trigger: behavior shaping only (no new context)   primitive: Skill + hooks → use hook-development skill
```

When the primitive is **Skill + hooks**, hand off to the **`hook-development`** skill for design, linting, and testing. This skill covers agent-specific hook patterns only (Phase 3 below).

For the deep comparison (cost, observability, migration paths), read [`references/primitives.md`](references/primitives.md).

---

## Phase 1: Specify & Design

### 1.0 Description

One sentence. What the agent does and when to use it — nothing else.

```text
avoid: trigger lists, "Trigger on:" blocks, verbose use-when enumerations, examples
```

### 1.1 Model Routing

```
model: haiku    use-when: classification, narrowly scoped tool dispatch
model: sonnet   use-when: default; multi-step reasoning, complex tool orchestration
model: opus     use-when: root-cause analysis, deep security boundaries, adversarial reasoning
```

Sanity check:

```bash
python <skill-dir>/scripts/recommend.py path/to/your/agent.md
```

### 1.2 Read Grounding

**MANDATORY — READ ENTIRE FILE** (conditional by primitive):

| Primitive                                       | Grounding file                                                                     |
| ----------------------------------------------- | ---------------------------------------------------------------------------------- |
| Managed Agent                                   | [`references/grounding-managed-agents.md`](references/grounding-managed-agents.md) |
| Claude Code subagent / agent team / skill+hooks | [`references/grounding-claude-code.md`](references/grounding-claude-code.md)       |

**Tell the user:** "Before writing any config, read the grounding file above in full — it has the exact API shape, field names, and permission policy syntax. Skipping it is the leading cause of silent misconfiguration."

### 1.3 Discover & Pin Composable Skills

```bash
python <skill-dir>/scripts/recommend-skills.py path/to/your/agent.md --json
```

Review top candidates. For each accepted, pin an exact version (NEVER `latest`). See [`references/skill-composition.md`](references/skill-composition.md).

### 1.4 Permission Model

Default to least-privilege.

> **Critical — tell the user:** Never set `always_allow` for `agent_toolset` or apply it broadly across MCP servers. `always_allow` is safe only for a single, explicitly pinned, fully trusted MCP server where you control the server code. Everything else defaults to `always_ask`.

---

## Phase 2: Build

| Primitive            | Template                                                                             | Validate with                                 |
| -------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------- |
| Managed Agent        | [`templates/managed-agent.md`](references/templates/managed-agent.md)                | `audit.py` + `compile.py`                     |
| Claude Code subagent | [`templates/claude-code-subagent.md`](references/templates/claude-code-subagent.md)  | `audit.py` + `compile.py` (auto-detects kind) |
| Agent team           | same subagent template per teammate; parent spawns with `--bg` flag; results via `Monitor` tool or shared output file | `audit.py` per teammate |
| Skill + hooks        | [`templates/hooks.json`](references/templates/hooks.json) + `hook-development` skill | `hook-development/scripts/hook-linter.sh`     |

Validation gate (run in order, fail fast):

```bash
<skill-dir>/scripts/validate.sh path/to/your/agent.md
python <skill-dir>/scripts/audit.py path/to/your/agent.md
python <skill-dir>/scripts/compile.py path/to/your/agent.md
```

| Code                       | Severity     | Action                                                 |
| -------------------------- | ------------ | ------------------------------------------------------ |
| `PERM*`, `PIN001`, `CCSA*` | blocker      | must fix before deploy                                 |
| `SKILL001`                 | soft-warning | address or suppress with `skill_composition: declined` |

---

## Phase 3: Add Safety Nets via Hooks

For general hook design, use the **`hook-development`** skill. This phase covers agent-specific patterns only.

**MANDATORY — READ ENTIRE FILE:** [`references/agent-hook-patterns.md`](references/agent-hook-patterns.md). Six patterns:

| Pattern                                              | Type                                      |
| ---------------------------------------------------- | ----------------------------------------- |
| Subagent telemetry pipeline                          | foundational                              |
| Hook-based behavioral assertions                     | deterministic eval (powers `simulate.py`) |
| Permission-policy enforcement scoped by `agent_type` | safety                                    |
| "Are you done?" stop gates for autonomous agents     | quality                                   |
| Agent identity reload after compaction               | advanced                                  |
| MCP elicitation auto-handler for headless agents     | advanced                                  |

Pick the patterns that match your agent's risk profile. Each pattern's "See also" footer links to `hook-development/references/patterns.md` for mechanics.

---

## Phase 4: Estimate Cost

```bash
python <skill-dir>/scripts/cost.py path/to/your/agent.md --runs 3
```

Heuristic only — skill bodies and hook prompt/agent invocations aren't counted. See [`references/pricing.md`](references/pricing.md).

---

## Phase 5: Eval-First Testing

**MANDATORY — READ ENTIRE FILE:** [`references/testing-patterns.md`](references/testing-patterns.md).

Quick reference (share this with the user):

```
Layer A — Deterministic (hook-based assertions):
  python <skill-dir>/scripts/simulate.py path/to/agent.md tests/cases.yaml --runs 3 --sandbox
  ↳ checks: Tool(arg-glob) assertions in cases.yaml
  ↳ reports: flakiness score, p95 latency, cost per run
  ↳ --sandbox is REQUIRED for agents with side effects (writes, deploys, DB changes)

Layer B — Qualitative (LLM-as-judge):
  use-for: output clarity, reasoning quality, formatting
  never-for: tool-call checks or deterministic outputs — those belong in Layer A
```

Default: run both layers. Write `cases.yaml` first (eval-first), then build the agent prompt.

---

## Phase 6: Deploy & Update Safely

Before any update (Managed Agent, plugin manifest, subagent rename, hooks.json change):

```bash
python <skill-dir>/scripts/diff.py path/to/prod path/to/proposed --json
```

Exit code `2` means the update will **silently delete** something (Managed Agent wholesale replacement, removed hook, removed plugin component). Explicitly acknowledge each deletion before proceeding.

For visual review (PR comments, architecture diff):

```bash
python <skill-dir>/scripts/diagram.py path/to/your/agent.md --include-hooks hooks/hooks.json --format mermaid
```

The Mermaid output is a starting point. **For diagram refinement, hand off to the `diagrams` skill** (`diagrams/scripts/preview_diagram.js` for visualization).

---

## See Also

| Skill              | Purpose                                      |
| ------------------ | -------------------------------------------- |
| `hook-development` | general hook design mechanics                |
| `diagrams`         | Mermaid rendering and architectural diagrams |
