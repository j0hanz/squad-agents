# Plan — `dispatch-agents`

**Date:** 2026-07-06
**Source design brief:** [docs/design/2026-07-06-multiagent-dispatch-agents-design.md](../docs/design/2026-07-06-multiagent-dispatch-agents-design.md)
**Depth:** blueprint (3 ideators + 1 synthesizer)
**Companion specs:** [plan/dispatch-agents.specs.md](dispatch-agents.specs.md)

## Merge Rationale

Three blind ideator proposals were synthesized:

- **Kept from Conventional (A):** the build-before-delete spine — `implementer-prompt.md` and `subagent-contract.md` must be copied from the old skill dir _before_ it's deleted, and the repo stays valid at every intermediate commit. This is the ordering backbone.
- **Kept from Risk-First (B):** the insight that dangling `../multi-agent-development/` cross-skill refs are **masked** while the old skill still exists (the validator won't ERROR on a ref that still resolves). Resolved _without_ B's delete-first ordering (which breaks the copy-source step): a dedicated post-rewire `git grep` sweep for the four stale name strings acts as the dangler catcher — any hit is a missed referencing file. Also kept B's emphasis on gating the merged-reviewer combined-verdict schema as a first-class verification signal.
- **Kept from Minimalist (C):** the three reference files are a hard constraint (validator's 300-line rule + load-bearing schemas) — do not collapse them. `SKILL.md` stays lean with templates pushed into `references/`. The `bin/validate-plugin.mjs` change is comment-only. README: set both skill counts to 15 and fix the 14/16 inconsistency; no broader audit.
- **Discarded:** B's delete-first ordering (copy-source flaw, flagged by B itself). Any "audit README beyond the named lines" scope creep. Any task that adds narrative beyond the brief's Interface section.

**Resolved ordering:** build (skill + refs, reviewer) → rewire references + bin comment → swap test prompts → validate-on-new-wiring + stale-name grep sweep → hard-delete legacy → final validate + clean sweep.

## Tasks

### TASK-001: Create dispatch-agents skill and three reference files

Depends on: none
Files: [skills/dispatch-agents/SKILL.md](../skills/dispatch-agents/SKILL.md), [skills/dispatch-agents/references/subagent-contract.md](../skills/dispatch-agents/references/subagent-contract.md), [skills/dispatch-agents/references/implementer-prompt.md](../skills/dispatch-agents/references/implementer-prompt.md), [skills/dispatch-agents/references/reviewer-prompt.md](../skills/dispatch-agents/references/reviewer-prompt.md)
Symbols: [dispatch-agents](../skills/dispatch-agents/SKILL.md#L1)
Satisfies: REQ-001, REQ-002, SEC-002
Action: Create `skills/dispatch-agents/SKILL.md` with frontmatter `name: dispatch-agents`, the brief's `description`, `argument-hint`, and `allowed-tools` (`Agent(implementer), Agent(researcher), Agent(reviewer), Agent(conflict-resolver), AskUserQuestion, Bash(git *), Skill(write-commit), Skill(verification-before-completion), Skill(request-code-review)`), then the `MATRIX → WAVES → DISPATCH → REVIEW → INTEGRATE → Final Validation` flow with ≤10 lanes/wave and depth-1. Copy `implementer-prompt.md` verbatim from `skills/multi-agent-development/references/implementer-prompt.md` (copy BEFORE TASK-006 deletes the source). Adapt `subagent-contract.md` from the old one: trim roles table to the 4 named agents, add wave-width ≤10 and depth-1 constraints, keep model tiering + 5-field contract + `.claude/dispatch/` large-artifact rule. Write new `reviewer-prompt.md` merging old `spec-reviewer-prompt.md` + `quality-reviewer-prompt.md` into one dispatch template with the combined `SPEC_VERDICT: SPEC_PASS|SPEC_FAIL` + `QUALITY_VERDICT: QUALITY_PASS|CRITICAL|IMPORTANT|MINOR` + derived `GATE: PASS|FAIL` schema, max 2 tries, 2nd failure escalates to user by name, no split-into-two-agents fallback.
Validate: `node -e "const fs=require('fs');for(const f of ['skills/dispatch-agents/SKILL.md','skills/dispatch-agents/references/subagent-contract.md','skills/dispatch-agents/references/implementer-prompt.md','skills/dispatch-agents/references/reviewer-prompt.md']){if(!fs.existsSync(f))throw new Error('missing '+f)}console.log('all 4 files present')"`
Expected result: All four files exist; `SKILL.md` frontmatter parses with the exact `name`, `allowed-tools`, and `argument-hint` from the brief.

### TASK-002: Create merged reviewer agent

Depends on: [TASK-001](#task-001-create-dispatch-agents-skill-and-three-reference-files)
Files: [agents/reviewer.md](../agents/reviewer.md)
Symbols: [reviewer](../agents/reviewer.md#L1)
Satisfies: REQ-003, SEC-001
Action: Create `agents/reviewer.md` by merging `agents/spec-reviewer.md` + `agents/quality-reviewer.md`. Frontmatter: `name: reviewer`, `tools: Read, Grep, Glob, Bash`, `disallowedTools: Write, Edit`, `model: haiku`, `memory: project`. Body returns the combined schema from TASK-001's `reviewer-prompt.md` (`SPEC_VERDICT` + `QUALITY_VERDICT` + derived `GATE`), max 2 tries, 2nd failure escalate to user by name, no split fallback. Do NOT delete the two source agents yet (TASK-006).
Validate: `node -e "const t=require('fs').readFileSync('agents/reviewer.md','utf8');for(const s of ['name: reviewer','tools: Read, Grep, Glob, Bash','disallowedTools: Write, Edit','model: haiku','SPEC_VERDICT','QUALITY_VERDICT','GATE']){if(!t.includes(s))throw new Error('missing: '+s)}console.log('reviewer schema ok')"`
Expected result: `reviewer` agent file parses with all required schema strings; read-only tools enforced; `reviewer` matches `^[a-z][a-z0-9-]*$` and is unique (sources still present but named differently).

### TASK-003: Rewire referencing files and swap bin comment

Depends on: [TASK-001](#task-001-create-dispatch-agents-skill-and-three-reference-files), [TASK-002](#task-002-create-merged-reviewer-agent)
Files: [skills/using-agent-sdlc-skills/SKILL.md](../skills/using-agent-sdlc-skills/SKILL.md), [skills/diagnose/SKILL.md](../skills/diagnose/SKILL.md), [skills/diagnose/references/phases.md](../skills/diagnose/references/phases.md), [skills/project-init/SKILL.md](../skills/project-init/SKILL.md), [skills/receive-plan/SKILL.md](../skills/receive-plan/SKILL.md), [skills/project-audit/SKILL.md](../skills/project-audit/SKILL.md), [skills/write-commit/SKILL.md](../skills/write-commit/SKILL.md), [skills/verification-before-completion/references/definition-of-done.md](../skills/verification-before-completion/references/definition-of-done.md), [README.md](../README.md), [bin/validate-plugin.mjs](../bin/validate-plugin.mjs)
Symbols: none
Satisfies: REQ-004, REQ-006
Action: In one mechanical sweep, replace every reference to `multi-agent-development` / `multi-agent-dispatch` with `dispatch-agents`, every `spec-reviewer` / `quality-reviewer` with `reviewer`, and every `../multi-agent-development/references/subagent-contract.md` path with `../dispatch-agents/references/subagent-contract.md`. Collapse the Gate 3 fork in `using-agent-sdlc-skills/SKILL.md` lines 38-39 to a single `dispatch-agents` route; remove the "NEVER use multi-agent-dispatch for tasks with shared state" line at line 69 and the auto-invoke duplicate at line 64. Update `diagnose/SKILL.md` line 6 allowed-tools, lines 53/64/92 tournament prose, line 67 ref path. Update `diagnose/references/phases.md` line 6. Update `project-init/SKILL.md` lines 5 and 53. Collapse `receive-plan/SKILL.md` lines 87-88 to one Next-Skills line. Update `project-audit/SKILL.md` line 69. Update `write-commit/SKILL.md` line 10. Update `definition-of-done.md` lines 17 and 33. In `README.md`: line 24 Highlights, line 76 "15 are listed below", line 97 roster (replace the two old agents with `reviewer`; "Two skills orchestrate these."), lines 101-102 table rows (one `dispatch-agents` row), line 150 "15 skills" — fixing the 14/16 inconsistency to 15. In `bin/validate-plugin.mjs` lines 259-260: comment-only swap of the illustrative names; do NOT touch the dangling-ref scan logic. The cited line numbers are advisory (verified accurate as of plan authoring on 2026-07-06); if any file is edited before execution the line numbers may drift, but the `git grep` stale-name sweep in this task's `Validate:` field is the authoritative completeness gate — a missed edit surfaces as a non-"SWEEP CLEAN" result, not a silent break.
Validate: `git grep -n -e multi-agent-development -e multi-agent-dispatch -e spec-reviewer -e quality-reviewer -- skills agents README.md bin tests || echo "SWEEP CLEAN"`
Expected result: "SWEEP CLEAN" — zero hits for the four stale names across the swept paths before any deletion (proves the rewire is complete and no masked danglers remain).

### TASK-004: Swap test prompts

Depends on: [TASK-003](#task-003-rewire-referencing-files-and-swap-bin-comment)
Files: [tests/skill-triggering/prompts/dispatch-agents.txt](../tests/skill-triggering/prompts/dispatch-agents.txt), [tests/skill-triggering/prompts/multi-agent-development.txt](../tests/skill-triggering/prompts/multi-agent-development.txt), [tests/skill-triggering/prompts/multi-agent-dispatch.txt](../tests/skill-triggering/prompts/multi-agent-dispatch.txt)
Symbols: none
Satisfies: REQ-005
Action: Create `tests/skill-triggering/prompts/dispatch-agents.txt` with one prompt exercising a mixed dependent+independent plan mirroring the brief's Worked Example (a width-1 wave, a width-8 fan-out, a width-1 tail). Delete `multi-agent-development.txt` and `multi-agent-dispatch.txt` now (these are test fixtures, not copy sources — safe to delete ahead of the legacy-skill deletion).
Validate: `node -e "const fs=require('fs');if(!fs.existsSync('tests/skill-triggering/prompts/dispatch-agents.txt'))throw new Error('missing new prompt');for(const f of ['tests/skill-triggering/prompts/multi-agent-development.txt','tests/skill-triggering/prompts/multi-agent-dispatch.txt']){if(fs.existsSync(f))throw new Error('not deleted: '+f)}console.log('prompts swapped')"`
Expected result: New prompt present; both old prompts gone.

### TASK-005: Validate on new wiring before any legacy deletion

Depends on: [TASK-004](#task-004-swap-test-prompts)
Files: [bin/validate-plugin.mjs](../bin/validate-plugin.mjs)
Symbols: none
Satisfies: REQ-004, REQ-006, REQ-007
Action: Run the validator and the test suite while the legacy skills/agents still exist. This catches new-wiring errors (bad frontmatter, bad `allowed-tools` entries, line-count warnings, router-graph warnings) without producing false dangling-ref ERRORs from the not-yet-deleted old skills. Confirm the merged-reviewer schema strings match the brief verbatim by manual read.
Validate: `npm run validate && npm test`
Expected result: `npm run validate` exits 0 (no ERRORs; WARNINGs allowed — the two still-present old skills are now unwired in the router until TASK-006 deletes them, and `dispatch-agents` itself is wired so it produces no warning); `npm test` exits 0. Reviewer schema strings confirmed identical to the brief.

### TASK-006: Hard-delete legacy skills and agents

Depends on: [TASK-005](#task-005-validate-on-new-wiring-before-any-legacy-deletion)
Files: [skills/multi-agent-development/](../skills/multi-agent-development/), [skills/multi-agent-dispatch/](../skills/multi-agent-dispatch/), [agents/spec-reviewer.md](../agents/spec-reviewer.md), [agents/quality-reviewer.md](../agents/quality-reviewer.md)
Symbols: none
Satisfies: REQ-003, REQ-004
Action: Hard-delete `skills/multi-agent-development/` (including `references/`), `skills/multi-agent-dispatch/`, `agents/spec-reviewer.md`, `agents/quality-reviewer.md`. No compat shims, no redirects, no renames. The copy-source step (TASK-001) already captured `implementer-prompt.md` and the adapted `subagent-contract.md`, so deletion is safe.
Validate: `node -e "const fs=require('fs');for(const f of ['skills/multi-agent-development','skills/multi-agent-dispatch','agents/spec-reviewer.md','agents/quality-reviewer.md']){if(fs.existsSync(f))throw new Error('still present: '+f)}console.log('legacy deleted')"`
Expected result: All four legacy targets gone.

### TASK-007: Final validation and clean stale-name sweep

Depends on: [TASK-006](#task-006-hard-delete-legacy-skills-and-agents)
Files: none
Symbols: none
Satisfies: REQ-006, REQ-007
Action: Run the full gate post-deletion. The validator must report zero dangling `../<sibling>/` cross-skill refs (the rewire already replaced them; deletion turns any survivors into ERRORs). Re-run the stale-name grep sweep across the whole repo to confirm nothing references the deleted names. Do not commit.
Validate: `npm run validate && npm test && (git grep -n -e multi-agent-development -e multi-agent-dispatch -e spec-reviewer -e quality-reviewer -- . ":(exclude).git" || echo "SWEEP CLEAN")`
Expected result: `npm run validate` exits 0 with zero ERRORs; `npm test` exits 0; grep prints "SWEEP CLEAN" (no stale name strings anywhere outside `.git`).

## Out of Scope

No compat shims, no renames, no new deps. No changes to `implementer.md` / `researcher.md` / `conflict-resolver.md` / `diff-reviewer.md`. No `request-code-review` / `diff-reviewer` changes. No harness `Task*`-tool / agent-teams adoption. No README audit beyond the named lines. No prose beyond the brief's Interface. No commit.

## Commit Guard

Do NOT commit. If the user wants a commit only (no push), hand off to `write-commit`. If the user wants a commit, push, and PR, hand off to `pr-workflow`.
