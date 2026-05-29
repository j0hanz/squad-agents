---
name: agent-development
description: |
  Use when building, testing, auditing, or debugging agents — Managed Agents, Claude Code subagents, agent teams, or skill+hooks behavior shaping.
disable-model-invocation: true
---

## Core Philosophy

Building agents is a **Process** task. Configuration formats must match API expectations exactly (low freedom), while system prompts and hook designs benefit from iteration (medium freedom). We use an eval-first loop: define the behavioral constraints, baseline the tests with hook-based assertions, build the agent, and measure.

Compose first; build only where no sibling skill exists. The workspace has 20 sibling skills — running `scripts/recommend-skills.py` is part of Phase 1, not an afterthought.

## Critical Anti-Patterns

| Rule                                                                               | Why                                                                                                            |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **NEVER omit items during a Managed Agent update**                                 | `agents.update` replaces arrays wholesale — omitting a tool/skill/MCP silently deletes it                      |
| **NEVER pin custom skills to `latest` in production**                              | Pin exact versions; `latest` moves under you                                                                   |
| **NEVER apply `always_allow` broadly**                                             | Default `always_ask` for `agent_toolset`; `always_allow` only for explicitly pinned, fully trusted MCP servers |
| **NEVER write a blocking hook when a non-blocking one solves it**                  | Blocking hooks break headless mode and `/loop`                                                                 |
| **NEVER skip `diff.py` before deploy**                                             | Deletions are silent in API responses; applies to subagents and plugin manifests too                           |
| **NEVER use the `Agent` tool's `general-purpose` for tasks a typed subagent fits** | Re-derives context cold — more expensive                                                                       |
| **NEVER configure hooks that prompt the user**                                     | Breaks headless mode (`-p` and `/loop` flows)                                                                  |
| **NEVER trust LLM-as-judge for deterministic checks**                              | Use a `PreToolUse` observer hook instead; LLM-judge is for output quality only                                 |

---

## Phase 0: Pick the Right Primitive

```
trigger: API-callable from external code          primitive: Managed Agent
trigger: spawned by Claude during a session       primitive: Claude Code subagent
trigger: long-running parallel workers            primitive: Agent team (/background, TeamCreate)
trigger: behavior shaping only (no new context)   primitive: Skill + hooks (no agent needed)
```

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
python ${CLAUDE_SKILL_DIR}/scripts/recommend.py path/to/your/agent.md
```

### 1.2 Read Grounding

**MANDATORY — READ ENTIRE FILE** (conditional by primitive):

| Primitive                                       | Grounding file                                                                     |
| ----------------------------------------------- | ---------------------------------------------------------------------------------- |
| Managed Agent                                   | [`references/grounding-managed-agents.md`](references/grounding-managed-agents.md) |
| Claude Code subagent / agent team / skill+hooks | [`references/grounding-claude-code.md`](references/grounding-claude-code.md)       |

### 1.3 Discover & Pin Composable Skills

```bash
python ${CLAUDE_SKILL_DIR}/scripts/recommend-skills.py path/to/your/agent.md --json
```

Review top candidates. For each accepted, pin an exact version (NEVER `latest`). See [`references/skill-composition.md`](references/skill-composition.md).

### 1.4 Permission Model

Default to least-privilege. The audit step will flag any `always_allow` outside a fully trusted MCP.

---

## Phase 2: Build

| Primitive            | Template                                                                             | Validate with                                 |
| -------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------- |
| Managed Agent        | [`templates/managed-agent.md`](references/templates/managed-agent.md)                | `audit.py` + `compile.py`                     |
| Claude Code subagent | [`templates/claude-code-subagent.md`](references/templates/claude-code-subagent.md)  | `audit.py` + `compile.py` (auto-detects kind) |
| Agent team           | compose from subagent templates; declare via `TeamCreate` API                        | `audit.py` per teammate                       |
| Skill + hooks        | [`templates/hooks.json`](references/templates/hooks.json) + `hook-development` skill | `hook-development/scripts/hook-linter.sh`     |

Validation gate (run in order, fail fast):

```bash
${CLAUDE_SKILL_DIR}/scripts/validate.sh path/to/your/agent.md
python ${CLAUDE_SKILL_DIR}/scripts/audit.py path/to/your/agent.md
python ${CLAUDE_SKILL_DIR}/scripts/compile.py path/to/your/agent.md
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
python ${CLAUDE_SKILL_DIR}/scripts/cost.py path/to/your/agent.md --runs 3
```

Heuristic only — skill bodies and hook prompt/agent invocations aren't counted. See [`references/pricing.md`](references/pricing.md).

---

## Phase 5: Eval-First Testing

**MANDATORY — READ ENTIRE FILE:** [`references/testing-patterns.md`](references/testing-patterns.md).

```
layer:   A — Hook-based assertions (deterministic)
command: python ${CLAUDE_SKILL_DIR}/scripts/simulate.py path/to/your/agent.md tests/cases.yaml --runs 3 --sandbox
checks:  Tool(arg-glob) assertions from cases.yaml
reports: flakiness, p95 latency, cost per run

layer:   B — LLM-as-judge (qualitative)
use-for: clarity, reasoning, formatting — questions a hook cannot answer
```

Default: combine both layers.

---

## Phase 6: Deploy & Update Safely

Before any update (Managed Agent, plugin manifest, subagent rename, hooks.json change):

```bash
python ${CLAUDE_SKILL_DIR}/scripts/diff.py path/to/prod path/to/proposed --json
```

Exit code `2` means the update will **silently delete** something (Managed Agent wholesale replacement, removed hook, removed plugin component). Explicitly acknowledge each deletion before proceeding.

For visual review (PR comments, architecture diff):

```bash
python ${CLAUDE_SKILL_DIR}/scripts/diagram.py path/to/your/agent.md --include-hooks hooks/hooks.json --format mermaid
```

The Mermaid output is a starting point. **For diagram refinement, hand off to the `diagrams` skill** (`diagrams/scripts/preview_diagram.js` for visualization).

---

## See Also

| Skill              | Purpose                                      |
| ------------------ | -------------------------------------------- |
| `hook-development` | general hook design mechanics                |
| `diagrams`         | Mermaid rendering and architectural diagrams |
