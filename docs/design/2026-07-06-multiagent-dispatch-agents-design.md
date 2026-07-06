# Design Brief — `dispatch-agents`

**Date:** 2026-07-06
**Status:** DRAFT — supersedes the previous brief this file held (that brief was APPROVED but never implemented; this is a full rewrite per direct request, not a `receive-plan` pass)
**Replaces:** `multi-agent-development`, `multi-agent-dispatch`, `agents/spec-reviewer.md`, `agents/quality-reviewer.md`, and the two-skill (`multiagent` + `dispatch-agents`) brief this file previously held

---

## Approach

**One skill, one loop: a dependency-ordered wave scheduler.**

`dispatch-agents` replaces the seq-vs-parallel skill split with a single mechanism. Turn a task list into a **Matrix** (files touched / depends-on / risk / verification — unchanged from today, it's the load-bearing safety gate), topologically sort it into **waves** (a wave is every task whose dependencies are already satisfied), and dispatch each wave's tasks together — up to **10 concurrent lanes**. A wave of width 1 behaves exactly like today's sequential `multi-agent-development`; a single wave of width N behaves exactly like today's parallel `multi-agent-dispatch`; a mixed plan is just several waves of varying width. Nothing about the mechanism changes between these cases — only how many lanes land in one wave.

Per lane:

- **Writer** → `implementer` (`isolation: "worktree"`, explicit `model:`).
- **Read-only** (investigate/probe, no code change) → `researcher`.
- **Review gate** (writer lanes only) → ONE merged `reviewer` agent returning a spec-compliance verdict AND a quality verdict in a single pass — replaces today's `spec-reviewer` + `quality-reviewer` pair and the prior brief's combined-then-split escalation. Max 2 tries; 2nd failure escalates to the user by name.
- **Conflict** → `conflict-resolver`, unchanged.

No `Task*`-tool integration, no per-cluster risk classification, no light/heavy path branching. The Matrix already carries risk and dependency data — the wave scheduler reads it directly instead of routing it through a second classification step.

## Why

Brief research pass — [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system), [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents), [Claude Code: Create custom subagents](https://code.claude.com/docs/en/sub-agents).

1. **"Add complexity only when it demonstrably improves outcomes."** (Building effective agents.) The previous brief's `Task*`-tool dependency graph, per-cluster light/heavy risk gate, and combined-then-split review escalation are three separate mechanisms doing one job the Matrix already does — deciding what can safely run together. One wave scheduler reading one Matrix replaces all three.
2. **Effort should scale with task count, not a fixed cap.** Anthropic's own dispatch heuristic: "simple fact-finding requires just 1 agent... direct comparisons might need 2-4 subagents... complex [work] might use more than 10 subagents with clearly divided responsibilities." This replaces the old "MAX 3 foreground, background-exempt" carve-out with a single knob — wave width — sized directly off the Matrix's independent-task count. The same source warns against the opposite failure: early Anthropic agents "spawned 50 subagents for simple queries" — a wave is sized to how many tasks are genuinely independent, never padded to hit 10.
3. **Orchestrator-workers is the named pattern that already fits.** (Building effective agents.) "A central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results" — used precisely when "you can't predict the subtasks needed... in coding, for example." That's a single orchestrator loop, not two skills layered on top of each other.
4. **The harness already does work the old brief was re-implementing.** Per the Claude Code subagent docs, subagents now run in the background by default and still surface permission prompts in the main session; `isolation: "worktree"` and nested dispatch are first-class. The old "MAX 3 agents in the foreground... background lanes are exempt from that cap" rule was compensating for a harness default that no longer needs compensating for.
5. **Multi-agent systems already cost roughly 15x more tokens than a single chat turn** (Anthropic's own measurement). That's an argument for keeping the orchestration mechanism itself as thin as possible — every extra tracking layer (`Task*` tool, risk classifier, split-review mode) adds tokens on top of an already-expensive pattern without adding correctness.
6. **Custom agents stay because they're the DRY option, not a legacy holdover.** `implementer`'s and `conflict-resolver`'s output schemas live once in the agent file instead of being restated in every dispatch prompt — replacing them with generic `general-purpose` calls, as the prior brief proposed, would mean repeating the schema at every call site. That's less maintainable, not more.

## Scope

**Size:** M — one new skill, one merged agent, two skills + two agents deleted, ~9 referencing files updated, 2 test prompts merged into 1.

**In scope:**

- New: `skills/dispatch-agents/` (+ `references/subagent-contract.md`, `references/implementer-prompt.md`, `references/reviewer-prompt.md`).
- New: `agents/reviewer.md` (merges `agents/spec-reviewer.md` + `agents/quality-reviewer.md`).
- Delete: `skills/multi-agent-development/`, `skills/multi-agent-dispatch/`, `agents/spec-reviewer.md`, `agents/quality-reviewer.md`.
- Unchanged: `agents/implementer.md`, `agents/researcher.md`, `agents/conflict-resolver.md`, `agents/diff-reviewer.md`.
- Update ~9 referencing files (see First Step).
- Merge test prompts: `multi-agent-development.txt` + `multi-agent-dispatch.txt` → `dispatch-agents.txt`.
- Collapse router Gate 3's independent/sequential fork into one line.

**Out of scope:** `request-code-review` / `diff-reviewer` (separate consumer, untouched); harness `Task*`-tool or agent-teams adoption (considered, rejected — see Why #1 and #4); `parallel-brainstorming` and `project-audit`'s own mechanisms beyond their one-line cross-reference.

## Constraints

- **AGENTS.md:** breaking changes are fine — no legacy-compat shims, rewrite directly. → hard delete + hard merge, no redirects.
- **`bin/validate-plugin.mjs`:** errors on dangling `../<sibling>/` cross-skill refs; warns if a skill isn't wired into the router graph; warns on skills >300 lines without `references/`. → the dangling-ref scan is generic (matches any `../<name>/` against real skill dirs), so only its illustrative comment needs a path update, not its logic.
- **Skill/agent frontmatter:** flat YAML (`name` + `description` required); `allowed-tools`/`tools` entries must match the validator's `VALID_TOOL_ENTRY` regex; agent `name` must match `^[a-z][a-z0-9-]*$` and stay unique across `agents/*.md`.
- **No new dependencies.** Same four named agents (`implementer`, `researcher`, `reviewer`, `conflict-resolver`) plus built-in `general-purpose`/`Explore` only as a documented fallback for domains with no specialist.
- **Verdict schemas preserved:** writer (`DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`), investigator (`SUCCESS | FAILURE | BLOCKED | NEEDS_CONTEXT`); reviewer becomes ONE combined schema (`SPEC_VERDICT: SPEC_PASS|SPEC_FAIL` + `QUALITY_VERDICT: QUALITY_PASS|CRITICAL|IMPORTANT|MINOR` + derived `GATE: PASS|FAIL`).
- **Review-gate cap unchanged:** max 2 tries; 2nd failure escalates to the user by name — no split-into-two-agents fallback.
- **`isolation: "worktree"` stays call-site-enforced** (dispatcher states it explicitly; it isn't an agent-definition property).
- **Explicit `model:` override at every dispatch call site** — never silently inherit the orchestrator's model.
- **NEW — wave width ≤ 10 lanes**, sized to the Matrix's actual independent-task count (never padded to hit the cap).
- **NEW — dispatch stays at depth 1.** None of the four named agents spawn further subagents; the orchestrator (main thread) is the only dispatcher — keeps the whole mechanism inside one level, regardless of the harness's own nesting limit.

## Interface

### `dispatch-agents/SKILL.md`

- **frontmatter:** `name: dispatch-agents`; `description:` "Use when implementing a multi-task plan or backlog — independent, dependent, or a mix. Groups tasks into dependency-ordered waves and dispatches up to 10 subagents per wave, in parallel where safe. Prefer over hand-rolling sequential or ad hoc parallel execution."
- **`argument-hint`:** `[path to plan file, or the tasks to execute]`
- **`allowed-tools`:** `Agent(implementer), Agent(researcher), Agent(reviewer), Agent(conflict-resolver), AskUserQuestion, Bash(git *), Skill(write-commit), Skill(verification-before-completion), Skill(request-code-review)`
- **Flow:**

  ```text
  Read tasks -> MATRIX (files / depends-on / risk / verification, per task)
             -> WAVES (topological sort on depends-on; same-file tasks merge into one lane)
             -> per wave, in order:
                  DISPATCH  all lanes in ONE message, <=10 lanes (writers: implementer+worktree; read-only: researcher)
                  REVIEW    per writer lane, as it reports back: reviewer (combined pass, max 2 tries, else escalate)
                  INTEGRATE once the wave's lanes are done/escalated: real tests, conflict-resolver on merge conflicts
  -> after the last wave: Final Validation (DoD -> tests -> verification-before-completion -> request-code-review)
  ```

- **Strict Rules:** no overlapping writes (Matrix is the launch gate); no assumed context (5-field contract, every dispatch); wave width sized to genuinely independent tasks, never padded; no blind trust (real tests, independent verification); no hidden skips (name every escalated/blocked lane in the report).
- **References:** `references/subagent-contract.md` (5-field contract, verdict schemas, model tiering, roles table, large-artifact `.claude/dispatch/` rule), `references/implementer-prompt.md` (writer dispatch template, unchanged), `references/reviewer-prompt.md` (NEW — merged combined-verdict dispatch template).
- **Next Skills:** `write-commit`; `verification-before-completion`; `diagnose` (test/merge failure); `request-code-review` (mandatory at Final Validation).

## Architecture

**System diagram (ASCII):**

```text
====================================================================
 BEFORE: two skills, two mental models
====================================================================

  using-agent-sdlc-skills
        │
   independent            sequential/dependent
        │                          │
        ▼                          ▼
  multi-agent-dispatch     multi-agent-development
  (parallel batches)       (strict order + clusters)

====================================================================
 AFTER: one skill, one wave scheduler
====================================================================

  using-agent-sdlc-skills
        │
   2+ tasks, any shape
        │
        ▼
  dispatch-agents
        │
        ▼
  MATRIX   (files / depends-on / risk / verification)
        │
        ▼
  WAVES    (topological sort — width varies per wave)
        │
   ┌────┴──────┬─────────────┬─────────────┐
   ▼            ▼             ▼             ▼
 wave 1       wave 2        wave 3        wave N
 width 1      width 8       width 2         ...
 (chain)      (fan-out)     (fan-out)
   │            │             │
   ▼            ▼             ▼
 DISPATCH → REVIEW (writer lanes only) → INTEGRATE (tests, conflicts)
        │
        ▼ (after last wave)
  Final Validation
  (DoD -> tests -> verification-before-completion -> request-code-review)
```

**Agent roster (before → after):**

```text
agents/implementer.md          unchanged  (writer, worktree)
agents/researcher.md           unchanged  (read-only investigator)
agents/conflict-resolver.md    unchanged  (writer, merge conflicts)
agents/spec-reviewer.md    ┐
agents/quality-reviewer.md ┴─► agents/reviewer.md   (NEW — one combined-verdict pass)
agents/diff-reviewer.md         unchanged  (different consumer: request-code-review only)
```

**References layout:**

```text
skills/dispatch-agents/references/
  subagent-contract.md   ← canonical contract + verdict schemas + tier map + roles table
  implementer-prompt.md  ← writer dispatch template (copied unchanged)
  reviewer-prompt.md     ← NEW combined spec+quality dispatch template
```

## Worked Example

Feature: real-time notification delivery across 8 channels, schema-first.

| Task | Files touched                                                     | Depends on | Risk | Verification               |
| :--- | :---------------------------------------------------------------- | :--------- | :--- | :------------------------- |
| 1    | `migrations/notifications.sql`, `models/notification.ts`          | none       | med  | `npm test models`          |
| 2-9  | `channels/{email,sms,push,slack,webhook,in-app,discord,teams}.ts` | Task 1     | low  | `npm test channels/<name>` |
| 10   | `tests/integration/notifications.test.ts`                         | Tasks 2-9  | med  | `npm test integration`     |

**WAVES:** Wave 1 = `{Task 1}` (width 1 — nothing else can start yet). Wave 2 = `{Tasks 2-9}` (width 8 — all file-disjoint, same `Depends on`, dispatched together in ONE message, under the 10-lane cap). Wave 3 = `{Task 10}` (width 1 — waits for every Wave 2 lane to clear review).

```text
Wave 1: Task 1    — DONE, reviewer PASS — merged
Wave 2: Tasks 2-9 — 8 lanes dispatched together;
        7x DONE + reviewer PASS; 1x (webhook) DONE_WITH_CONCERNS -> IMPORTANT -> fixed, re-reviewed -> PASS
        all 8 merged
Wave 3: Task 10   — DONE, reviewer PASS — merged
Tests: PASS — `npm test` (full suite)
Blocked/escalated: none
```

Same Matrix, same wave loop, no special-casing — Wave 1 and Wave 3 look exactly like the old sequential skill; Wave 2 looks exactly like the old parallel skill, scaled to 8 of the 10 available lanes.

## Risks

| Risk                                                                                           | Severity | Mitigation                                                                                                                                                                                                                                   |
| :--------------------------------------------------------------------------------------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Merging spec+quality review into one pass misses what a second fresh pair of eyes would catch. | Med      | Keep the max-2-try cap + escalation. A task repeatedly failing combined review is a signal to split the _task_ smaller at the Matrix step, not to reintroduce a second reviewer.                                                             |
| A wave of up to 10 concurrent writer lanes collides because the Matrix missed a shared file.   | Med      | File-disjoint check stays a hard launch gate, unchanged from today; `conflict-resolver` is the unchanged safety net.                                                                                                                         |
| Dropping `Task*`-tool tracking loses a structured mid-session dependency query surface.        | Low      | The Matrix (plain text, already in the orchestrator's own context) + `git log` commit-subject resume cover the same need — without a tool dependency or the "`Task*` tools are session-scoped" failure mode the prior brief flagged as High. |
| Renaming/deleting 2 skills + 2 agents breaks a referencing file that gets missed.              | Med      | First Step enumerates every referencing file; `npm run validate` gates dangling refs and unwired-router warnings before merge.                                                                                                               |
| A wave gets padded toward 10 lanes when only 2-3 tasks are genuinely independent.              | Low      | Wave width is read directly off the Matrix's independent-task count — padding a wave is named explicitly as a failure mode, not a goal.                                                                                                      |
| Background-by-default subagent execution means permission prompts can interleave across lanes. | Low      | Documentation-only: name this as expected behavior so a wave of several lanes doesn't look like a hang when one lane prompts for permission.                                                                                                 |

## First Step

1. **Create `skills/dispatch-agents/`**: `SKILL.md` per Interface above; `references/subagent-contract.md` (adapt from the old `multi-agent-development/references/subagent-contract.md` — trim the roles table to the 4 named agents, add the wave-width and depth-1 constraints, keep model tiering); `references/implementer-prompt.md` (copy unchanged); `references/reviewer-prompt.md` (NEW — merge `spec-reviewer-prompt.md` + `quality-reviewer-prompt.md` into one combined dispatch template + verdict rules table).
2. **Create `agents/reviewer.md`**: merge `agents/spec-reviewer.md` + `agents/quality-reviewer.md` frontmatter and checks into one read-only agent (`tools: Read, Grep, Glob, Bash`, `memory: project`) returning the combined `SPEC_VERDICT` + `QUALITY_VERDICT` schema. Delete both source files.
3. **Delete** `skills/multi-agent-development/` (incl. `references/`), `skills/multi-agent-dispatch/`.
4. **Update referencing files:**
   - `skills/using-agent-sdlc-skills/SKILL.md` — collapse Gate 3's independent/sequential fork into `-- 2+ tasks (any shape) --> dispatch-agents`; update the Auto-invoke list; drop the now-inapplicable `multi-agent-dispatch` NEVER-list entry.
   - `skills/diagnose/SKILL.md` + `references/phases.md` — rename `Skill(multi-agent-dispatch)` → `Skill(dispatch-agents)`; tournament-path prose; `subagent-contract.md` path.
   - `skills/project-init/SKILL.md` — "Send Searchers" line + frontmatter `Skill(...)` reference.
   - `skills/receive-plan/SKILL.md` — collapse the two Next-Skills lines into one `dispatch-agents` line.
   - `skills/project-audit/SKILL.md` — Next Skills line.
   - `skills/write-commit/SKILL.md` — canonical-source cross-reference line.
   - `skills/verification-before-completion/references/definition-of-done.md` — both mentions.
   - `README.md` — skill count (16 → 15), Highlights table, Subagent Dispatch section (agent roster + table), "What's Included" intro line.
   - `bin/validate-plugin.mjs` — update the illustrative comment's path (logic is unaffected).
5. **Merge test prompts:** delete `tests/skill-triggering/prompts/multi-agent-development.txt` and `multi-agent-dispatch.txt`; create `tests/skill-triggering/prompts/dispatch-agents.txt` with a prompt that exercises a mixed (dependent + independent) plan.
6. **Validate:** `npm run validate` (dangling refs + router wiring); `npm test` (skill-triggering, incl. new `dispatch-agents.txt`).

## Commit Guard

Do not commit. If the user wants to commit only (no push), hand off to `write-commit`. If the user wants to commit, push, and open a PR, hand off to `pr-workflow`.
