# Specs — `dispatch-agents`

**Date:** 2026-07-06
**Source design brief:** [docs/design/2026-07-06-multiagent-dispatch-agents-design.md](../docs/design/2026-07-06-multiagent-dispatch-agents-design.md)
**Depth:** blueprint (3 ideators + 1 synthesizer)

## Goal

Replace two skills (`multi-agent-development`, `multi-agent-dispatch`) and two agents (`spec-reviewer`, `quality-reviewer`) with ONE new skill `dispatch-agents` — a dependency-ordered wave scheduler (≤10 lanes/wave, depth-1) — and ONE merged agent `reviewer` that returns a combined `SPEC_VERDICT` + `QUALITY_VERDICT` in a single pass. Hard delete + hard merge; no compat shims, no redirects, no renames.

## Requirements

- **REQ-001:** New skill `skills/dispatch-agents/SKILL.md` with the brief's frontmatter, `MATRIX → WAVES → DISPATCH → REVIEW → INTEGRATE → Final Validation` flow, ≤10 lanes/wave, depth-1.
- **REQ-002:** Three reference files under `skills/dispatch-agents/references/`: adapted `subagent-contract.md`, copied `implementer-prompt.md`, new merged `reviewer-prompt.md`.
- **REQ-003:** Merged `agents/reviewer.md` (read-only, `model: haiku`, combined `SPEC_VERDICT` + `QUALITY_VERDICT` + derived `GATE` schema); both source agents deleted.
- **REQ-004:** All ~9 referencing files rewired to the new skill/agent names; `bin/validate-plugin.mjs` comment-only swap (logic untouched).
- **REQ-005:** Test prompts swapped — delete `multi-agent-{development,dispatch}.txt`, create `dispatch-agents.txt` (one prompt exercising a mixed dependent+independent plan).
- **REQ-006:** No stale name strings (`multi-agent-development`, `multi-agent-dispatch`, `spec-reviewer`, `quality-reviewer`) remain in `skills/`, `agents/`, `README.md`, `bin/`, `tests/`.
- **REQ-007:** `npm run validate` and `npm test` pass after deletion; no commits made.
- **SEC-001:** Reviewer is read-only (`disallowedTools: Write, Edit`); no write capability on the gate agent.
- **SEC-002:** No overlapping write lanes; the Matrix is the launch gate (no assumed context; 5-field contract on every dispatch).

## Scope

**In scope:**

- New: `skills/dispatch-agents/` (+ `references/subagent-contract.md`, `references/implementer-prompt.md`, `references/reviewer-prompt.md`).
- New: `agents/reviewer.md` (merges `spec-reviewer.md` + `quality-reviewer.md`).
- Delete: `skills/multi-agent-development/` (incl. `references/`), `skills/multi-agent-dispatch/`, `agents/spec-reviewer.md`, `agents/quality-reviewer.md`.
- Unchanged: `agents/implementer.md`, `agents/researcher.md`, `agents/conflict-resolver.md`, `agents/diff-reviewer.md`.
- Update ~9 referencing files + the `bin/validate-plugin.mjs` illustrative comment (see plan TASK-003).
- Merge test prompts into one `dispatch-agents.txt`.
- Collapse router Gate 3's independent/sequential fork into one line.
- `bin/validate-plugin.mjs` illustrative-comment path swap only.

**Out of scope:** `request-code-review` / `diff-reviewer` (separate consumer, untouched); harness `Task*`-tool / agent-teams adoption (rejected — see brief Why #1 and #4); `parallel-brainstorming` and `project-audit` mechanisms beyond their one-line cross-references; any README audit beyond the named lines; any prose beyond the brief's Interface section.

## Constraints

- **AGENTS.md:** breaking changes are fine — no legacy-compat shims, rewrite directly.
- **`bin/validate-plugin.mjs`:** ERRORs on dangling `../<sibling>/` cross-skill refs; WARNINGs if a skill isn't wired into the router graph; WARNINGs on skills >300 lines without `references/`. After edits, `npm run validate` must pass (no ERRORs).
- **Skill/agent frontmatter:** flat YAML (`name` + `description` required); `allowed-tools`/`tools` entries must match the validator's `VALID_TOOL_ENTRY` regex. Note: `Bash(git *)` is valid in skill `allowed-tools` but NOT in agent `tools:` (agent `tools:` accepts only bare names, `mcp__*`, `Agent(...)`, `Task(...)`).
- **Agent `name`:** must match `^[a-z][a-z0-9-]*$` and stay unique across `agents/*.md`. `reviewer` satisfies.
- **No new dependencies.** Same four named agents (`implementer`, `researcher`, `reviewer`, `conflict-resolver`) plus built-in `general-purpose`/`Explore` only as a documented fallback.
- **Verdict schemas preserved:** writer (`DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`), investigator (`SUCCESS | FAILURE | BLOCKED | NEEDS_CONTEXT`); reviewer becomes ONE combined schema (`SPEC_VERDICT: SPEC_PASS|SPEC_FAIL` + `QUALITY_VERDICT: QUALITY_PASS|CRITICAL|IMPORTANT|MINOR` + derived `GATE: PASS|FAIL`).
- **Review-gate cap unchanged:** max 2 tries; 2nd failure escalates to the user by name — no split-into-two-agents fallback.
- **`isolation: "worktree"` stays call-site-enforced** (dispatcher states it explicitly; not an agent-definition property).
- **Explicit `model:` override at every dispatch call site** — never silently inherit the orchestrator's model.
- **Wave width ≤ 10 lanes**, sized to the Matrix's actual independent-task count (never padded to hit the cap).
- **Dispatch stays at depth 1** — none of the four named agents spawn further subagents; the orchestrator (main thread) is the only dispatcher.
- **Commit Guard:** do not commit. Hand off to `write-commit` (commit only) or `pr-workflow` (commit + push + PR) only if the user explicitly asks.

## Interface (target artifacts)

### `skills/dispatch-agents/SKILL.md`

- **frontmatter:** `name: dispatch-agents`; `description:` "Use when implementing a multi-task plan or backlog — independent, dependent, or a mix. Groups tasks into dependency-ordered waves and dispatches up to 10 subagents per wave, in parallel where safe. Prefer over hand-rolling sequential or ad hoc parallel execution."; `argument-hint: [path to plan file, or the tasks to execute]`; `allowed-tools: Agent(implementer), Agent(researcher), Agent(reviewer), Agent(conflict-resolver), AskUserQuestion, Bash(git *), Skill(write-commit), Skill(verification-before-completion), Skill(request-code-review)`.
- **Flow:** `Read tasks → MATRIX → WAVES (topological sort; same-file tasks merge into one lane) → per wave: DISPATCH (≤10 lanes; writers=implementer+worktree; read-only=researcher) → REVIEW (per writer lane, reviewer combined pass, max 2 tries else escalate) → INTEGRATE (real tests, conflict-resolver) → after last wave: Final Validation (DoD → tests → verification-before-completion → request-code-review)`.
- **References:** `subagent-contract.md`, `implementer-prompt.md`, `reviewer-prompt.md`.
- **Next Skills:** `write-commit`, `verification-before-completion`, `diagnose`, `request-code-review` (mandatory at Final Validation).

### `skills/dispatch-agents/references/`

- `subagent-contract.md` — adapted from old `multi-agent-development/references/subagent-contract.md`: roles table trimmed to the 4 named agents, wave-width ≤10 + depth-1 constraints added, model tiering + 5-field contract + `.claude/dispatch/` large-artifact rule preserved.
- `implementer-prompt.md` — copied verbatim from old `multi-agent-development/references/implementer-prompt.md`.
- `reviewer-prompt.md` — NEW merged dispatch template + verdict rules table (combined `SPEC_VERDICT` + `QUALITY_VERDICT` + derived `GATE`, max 2 tries, 2nd failure escalate by name).

### `agents/reviewer.md`

- **frontmatter:** `name: reviewer`; `description:` read-only combined spec+quality reviewer; `tools: Read, Grep, Glob, Bash`; `disallowedTools: Write, Edit`; `model: haiku`; `memory: project`.
- **body:** merges `spec-reviewer.md` + `quality-reviewer.md` checks; returns the combined schema; max 2 tries, 2nd failure escalate by name, no split fallback.

### Agent roster (before → after)

```text
agents/implementer.md          unchanged  (writer, worktree)
agents/researcher.md           unchanged  (read-only investigator)
agents/conflict-resolver.md    unchanged  (writer, merge conflicts)
agents/spec-reviewer.md    ┐
agents/quality-reviewer.md ┴─► agents/reviewer.md   (NEW — one combined-verdict pass)
agents/diff-reviewer.md         unchanged  (different consumer: request-code-review only)
```
