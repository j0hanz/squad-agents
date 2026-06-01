---
name: create-agent
description: "Design, write, test agents and subagents. Trigger on 'build agent', 'subagent', 'agent prompt', 'multi-agent'. Also: agent role selection, misfires, permission and tool scoping."
disable-model-invocation: false
argument-hint: "[what the agent should do]"
allowed-tools: Bash(python *) Bash(python3 *)
---

# Create Agent

An agent is a worker with its **own context window, system prompt, and tool surface**. It trades coordination overhead and cost for isolation: work that would flood the main thread, or that benefits from a narrow role and a clean slate, gets delegated. Engineer every agent by working through seven decisions, then test it before shipping.

**Core mindset:** an agent is the *expensive* primitive. A fresh agent re-derives context cold, burns its own token budget, and adds a coordination boundary you now have to design across. Reach for one only when isolation, parallelism, or a reusable narrow role earns its keep. If the model just needs *instructions* it can follow inline, that is a **skill**. If a fixed action must happen at a lifecycle point, that is a **hook**. If you need it once, just do it.

---

## Step 0 — Decide whether an agent is even the right tool

| Need | Use |
| :--- | :--- |
| A side task would **flood the main context** (large search, log triage, broad refactor) | **Subagent** |
| A **reusable role** invoked across many sessions (reviewer, debugger, researcher) | **Subagent** (saved definition) |
| Several **independent** tasks should run **in parallel** | **Agent team** or **agent view** |
| A **large, repeatable orchestration** — dozens to hundreds of units, cross-checked | **Workflow** |
| An agent must be **callable from outside** a session (your app, a cron, a webhook) | **Managed Agent** (API) |
| The model needs *instructions/knowledge* it applies inline | **Skill** — not an agent |
| A fixed action must happen at a lifecycle point (format, block, log) | **Hook** → use the `create-hook` skill |
| A one-off task right now | Just do it — no agent |

If an agent is still the answer, walk the seven decisions below.

---

## The seven decisions

1. **Name the job** — one sentence: "This agent <does X> so the main thread doesn't have to." If you can't state it, stop.
2. **Pick the primitive** — subagent, team, workflow, or Managed Agent. → [Step 2](#2--pick-the-primitive)
3. **Write the system prompt** — the agent's entire brain. → [Step 3](#3--write-the-system-prompt)
4. **Scope tools & permissions** — least privilege, every time. → [Step 4](#4--scope-tools--permissions)
5. **Route model & effort** — match capability to the job, not the ceiling. → [Step 5](#5--route-model--effort)
6. **Set context & composition** — isolation, skills, hooks, MCP, memory. → [Step 6](#6--set-context--composition)
7. **Test before shipping** — invoke it on real inputs; check behavior, not vibes. → [Step 7](#7--test-before-shipping)

---

## 1 — Name the job

Write it as `This agent <verb + object> so that <main-thread benefit>`. Examples:

- "This agent searches the codebase for every call site of an API so the main thread keeps a clean context."
- "This agent reviews a diff for security issues so review runs in an isolated, role-focused context."
- "This agent runs the test suite and fixes failures autonomously so the user isn't blocked."

A good job statement is **narrow**. "An agent that helps with code" is not a job; "an agent that audits TypeScript for unsafe `any` usage" is. Narrow jobs produce sharp system prompts, tight tool lists, and testable behavior.

**Split check — run before proceeding:** If the job statement contains `AND` connecting two unrelated verbs (e.g., "review AND fix", "analyze AND deploy", "scan AND commit"), **stop and split**. Write two job statements. Two jobs = two agents. Do not combine them — propose the split to the user and produce separate definitions unless they explicitly confirm a combined design is intentional. A reviewer with write access is a misconfigured agent, not a combined agent.

---

## 2 — Pick the primitive

The *when* and *who-invokes* determine the primitive. Read the deep comparison — cost, lifetime, observability, and migration paths — in **[references/primitives.md](references/primitives.md)** before committing.

| Primitive | Invoked by | Context | Best for |
| :--- | :--- | :--- | :--- |
| **Claude Code subagent** | Claude, mid-session, via the `Agent` tool | Fresh, isolated | Delegated side tasks; reusable narrow roles |
| **Agent team** | A parent agent (`TeamCreate`, `/background`) | Per-teammate, parallel | A few independent tasks running concurrently |
| **Agent view** | You, from a dashboard (`claude agents`) | Per-session, persistent | Many independent background sessions you steer |
| **Dynamic workflow** | A JS script the runtime executes | Per-agent, script-held | Large migrations/audits; cross-checked research at scale |
| **Managed Agent** | External code via the Agent API | One run per invocation | API-callable services outside any session |

**Built-in subagents** (don't rebuild these): `Explore` (Haiku, read-only search), `Plan` (read-only research), `general-purpose` (all tools). Prefer a **typed/named** subagent over `general-purpose` — `general-purpose` re-derives context cold and costs more.

For subagents, the full frontmatter field catalog and invocation modes are in **[references/subagent-spec.md](references/subagent-spec.md)**. For the API shape (`agents.create/update/invoke`, the wholesale-replace trap, permission policy), see **[references/managed-agents.md](references/managed-agents.md)** and the `/claude-api` reference.

---

## 3 — Write the system prompt

The system prompt **is** the agent — for a subagent it *replaces* the default Claude Code prompt entirely. This is the craft. Read **[references/system-prompt-craft.md](references/system-prompt-craft.md)** for the full treatment; the skeleton:

1. **Role & job** — one or two sentences. Who the agent is and the single job from Step 1.
2. **Operating procedure** — the steps to follow, in order. Imperative. This is where most of the quality lives.
3. **Boundaries** — what it must *not* do (scope limits, "don't touch X", "never commit"). Agents over-reach without explicit fences.
4. **Output contract** — the exact shape of what it returns. The parent only sees the agent's **final message**, so define it: a structured summary, a file path, a verdict. Vague output = useless delegation.
5. **Tone/length** — terse and factual unless the job needs otherwise.

**Principles:**

- **Self-contained.** A subagent gets no parent conversation history. Everything it needs must be in its system prompt or the invocation prompt. Never assume it "knows what we were doing."
- **Imperative, not aspirational.** "Read the file before editing" — not "you should try to read files."
- **Design the handoff.** State exactly what the agent returns, because that final message is the *only* thing the parent keeps. Tool calls and intermediate reasoning are discarded.
- **One job, fenced.** Boundaries prevent the classic failure: an agent asked to review code that starts rewriting it.
- **No angle brackets in `description`.** The `description` field must not contain `<` or `>` — use plain words instead of `<example>` tags or `<field-name>` placeholders. `validate_agent.py` warns on `DESC003`; avoid triggering it.

---

## 4 — Scope tools & permissions

Default to **least privilege**. Start read-only; add write/execute only when the job provably needs it.

| Job shape | Tool surface |
| :--- | :--- |
| Search / read / analyze | `Read, Grep, Glob` (this is the `Explore` profile) |
| Review / report | `Read, Grep, Glob` + the analysis it needs — **no** `Edit`/`Write` |
| Implement / fix | `Read, Edit, Write, Bash, Glob, Grep` |
| Orchestrate sub-work | add `Agent(worker, researcher)` — allowlist *which* agents it may spawn |

**Rules:**

- **`tools` is an allowlist; omit it to inherit all tools.** `disallowedTools` is a denylist applied first. Prefer naming an allowlist over inheriting everything.
- **`Bash` and write tools are escalations.** They can modify the host and exfiltrate data. Justify each one against the job. A reviewer does not need `Bash`.
- **Restrict spawn rights.** If the agent can spawn others, use `Agent(name1, name2)` to allowlist them; omit `Agent` entirely to forbid spawning.
- **Pick a permission mode deliberately.** `default` prompts; `plan` is read-only; `acceptEdits`/`bypassPermissions` remove guardrails. Background/headless agents auto-deny prompts — a blocking prompt there silently stalls the agent. See the permission-mode table in [references/subagent-spec.md](references/subagent-spec.md).
- **Never inline secrets** in an agent config — configs land in logs, diffs, and API responses. Use env-var references.

For Managed Agents, default `agent_toolset` to `always_ask`; reserve `always_allow` for a single, pinned, fully-trusted MCP server.

**Mandatory safety challenges — trigger these before producing the definition:**

| Request contains | Required action before proceeding |
| :--- | :--- |
| `bypassPermissions` | (1) State what it unlocks: writes to `.git/`, `.claude/`, `.vscode/` with no prompts. (2) Ask: "What specific capability requires bypass that `acceptEdits` doesn't cover?" (3) Present `acceptEdits` as the default recommendation. Only produce `bypassPermissions` after the user provides a concrete, scoped justification. |
| Auto-commit (`git commit`, `Bash` staging, push) | (1) Warn: "Autonomous commit means no human review before git history changes." (2) Ask whether `--no-commit` (report findings instead) would suffice. (3) If proceeding, the system prompt **must** include an explicit boundary: "Do not force-commit. Stop and report if a pre-commit hook fails." |
| Two unrelated jobs (`AND` in the job from Step 1) | Already caught in Step 1. If you reach here with a dual-job definition, go back and split it. |

---

## 5 — Route model & effort

Match the model to the *hardest* thing the agent must do — not the ceiling, not the floor.

| Model | `model:` value | Use when |
| :--- | :--- | :--- |
| Haiku | `haiku` / `claude-haiku-4-5-20251001` | Classification, search/discovery, narrow tool dispatch (the `Explore` profile) |
| Sonnet | `sonnet` / `claude-sonnet-4-6` | Default. Multi-step reasoning, implementation, tool orchestration |
| Opus | `opus` / `claude-opus-4-8` | Root-cause analysis, security boundaries, adversarial or deep reasoning |
| Inherit | `inherit` | Match the parent session's model (default when omitted) |

- A read-only search agent on Opus is waste; a security auditor on Haiku is a liability.
- `effort` (`low`…`max`) overrides the session effort for this agent — raise it for deep reasoning, lower it for mechanical work.
- Resolution order: `CLAUDE_CODE_SUBAGENT_MODEL` env → per-invocation override → frontmatter `model` → parent session model.

---

## 6 — Set context & composition

An agent starts with a fresh context. Decide what goes into it and what it composes with.

- **Isolation.** Set `isolation: worktree` for an agent that writes files but must not disturb the parent checkout (auto-cleaned if it makes no changes). Set `background: true` for always-async work — but remember background agents auto-deny permission prompts.
- **Preloaded skills.** `skills: [name, ...]` injects those skills' **full content** at startup (not just the description). Use this to give an agent a capability without relying on it to discover the skill. Cannot preload skills marked `disable-model-invocation: true`.
- **Hooks.** Scope a lifecycle guard to just this agent via frontmatter `hooks`, or shape it project-wide with `SubagentStart`/`SubagentStop`. For anything beyond a trivial guard, design it with the **`create-hook`** skill.
- **MCP servers.** `mcpServers` attaches tools inline (connect on start, disconnect on finish) or by reference — keeps MCP tool defs out of the *main* conversation's context.
- **Memory.** `memory: user|project|local` gives the agent a persistent `MEMORY.md` scope across runs. Use for agents that should accumulate learnings.
- **Compose, don't rebuild.** Before writing logic, check whether a sibling skill already does it. Preload or reference it instead of duplicating it in the prompt. See **[references/primitives.md](references/primitives.md#composition)**.

What loads at startup (non-fork subagent): its own system prompt **yes**; full Claude Code prompt **no**; `CLAUDE.md` + memory **yes** (except `Explore`/`Plan`); parent conversation history **no**; `skills:` content **yes**.

---

## 7 — Test before shipping

Never ship an agent you haven't invoked on a real input. The failure modes are behavioral, not syntactic.

**Validate the definition** (catches the silent misconfigurations — bad `name`, dangerous tools, broad permissions, invalid `model`):

```bash
python scripts/validate_agent.py path/to/your-agent.md
```

**Then exercise behavior.** Run the agent on 2–3 representative inputs, including one edge case and one it should *refuse* or scope out of. Check:

- [ ] Does it stay inside its boundaries (no scope creep, no unrequested writes)?
- [ ] Is the **final message** the output contract you designed — parseable, complete, self-contained?
- [ ] Does it use only the tools you granted, and stop when done (no thrashing)?
- [ ] For autonomous/background agents: does it terminate, or loop?

The full eval-first method — deterministic checks vs. LLM-as-judge, baseline-vs-agent comparison, flakiness — is in **[references/testing-agents.md](references/testing-agents.md)**. For rigorous skill-style benchmarking, hand off to the `skill-builder` skill.

---

## Output format when delivering an agent

Before producing the definition, state the job in the `This agent <verb + object> so that <benefit>` form — one sentence, visible to the user. This makes the single-job check auditable and catches misaligned scope before tool choices are locked in.

When you produce an agent for the user, always give:

1. **The agent definition** — complete frontmatter + system prompt, no placeholders, ready to save. State the file path (`.claude/agents/<name>.md` for project scope, `~/.claude/agents/` for all projects).
2. **Why these choices** — one line each on primitive, model, tool list, and permission mode.
3. **How to invoke it** — the natural-language trigger, the `@agent-<name>` mention, or the `--agent`/API call.
4. **One test** — a concrete prompt to run it against, and what a correct final message looks like.

**Mandatory pre-delivery:** Run `validate_agent.py` on the definition. Do not present it until you have run it and confirmed zero ERRORs. Report the exact `[OK]` / `[FAIL]` result inline. If warnings exist, note each one and whether it was accepted and why.

---

## Reference map

- **[references/primitives.md](references/primitives.md)** — subagent vs. team vs. workflow vs. Managed Agent: cost, lifetime, observability, migration paths, composition. **Read before picking a primitive.**
- **[references/subagent-spec.md](references/subagent-spec.md)** — full Claude Code subagent frontmatter catalog, permission modes, invocation modes, what loads at startup, fork mode.
- **[references/system-prompt-craft.md](references/system-prompt-craft.md)** — the craft of agent system prompts: structure, the handoff contract, worked examples, anti-patterns.
- **[references/managed-agents.md](references/managed-agents.md)** — API-callable Managed Agents: config shape, the wholesale-replace trap, permission policy. Pairs with `/claude-api`.
- **[references/testing-agents.md](references/testing-agents.md)** — eval-first testing: deterministic vs. qualitative, baseline comparison, flakiness.
- **[references/templates/](references/templates/)** — ready-to-fill `claude-code-subagent.md` and `managed-agent.json`.
- **[scripts/validate_agent.py](scripts/validate_agent.py)** — dependency-free linter for subagent definitions (name, fields, model, tools, permissions).

## See also

| Skill | For |
| :--- | :--- |
| `create-hook` | Lifecycle hooks — the deterministic guarantees you attach to agents |
| `agents-maintainer` | `AGENTS.md`/`CLAUDE.md` instruction files (not agent configs) |
| `skill-builder` | Building a skill, and rigorous benchmarked evals |
| `diagrams` | Visualizing a multi-agent architecture |
