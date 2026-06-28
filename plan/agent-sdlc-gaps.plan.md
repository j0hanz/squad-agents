Status: DRAFT

# Agent-SDLC Gap Remediation Plan

Task blocks satisfying REQ-001 through REQ-014 (`plan/agent-sdlc-gaps.specs.md`). Sequenced by blast radius: gap 1 (TASK-001..004) ships first and gets the heaviest validation, because `SessionStart` runs unconditionally for every installer on every session with zero per-user opt-in and a binary session-breaking failure mode. Gap 3 (TASK-005..008) ships second because ledger loss/corruption is a correctness defect in shipped code, scoped to users who invoke `multi-agent-development`. Gaps 4/5 (TASK-009..012) ship third — same dispatch surface as gap 3, but pure doc/policy change with no new persistent state to corrupt. Gap 2 (TASK-013..014) and gap 6 (TASK-015..018) are independent of everything above and of each other; either can ship in any order, including in parallel with the rest.

**One-time file-overlap exception:** TASK-006/TASK-007 (gap 3), TASK-009/TASK-011 (gap 4/5), and TASK-018 (gap 6) all edit `skills/multi-agent-development/SKILL.md`. Per that file's own File Rule (`multi-agent-development/SKILL.md:61`: "never run two tasks against overlapping paths even sequentially without merging them first"), these three chains' edits to this one shared file MUST land in a declared serial order even though the chains are otherwise logically independent and every other file each chain touches can still proceed in parallel. Declared order: gap 3's edits to `SKILL.md` (TASK-006, then TASK-007) land first, then gap 4/5's edits (TASK-009, then TASK-011), then gap 6's edit (TASK-018) — each subsequent chain's `SKILL.md` edit starts from the previous chain's already-merged version of the file, rather than from three divergent copies that get merged at the end. This is a landing-order note only; no new `Depends on` edges are added between these otherwise-unrelated chains.

---

### TASK-001: Add bootstrap-mode flag and dynamic skill-name scan to skill-nudge.sh

Depends on: none
Files: [hooks/skill-nudge.sh](hooks/skill-nudge.sh), [hooks/lib.sh](hooks/lib.sh)
Symbols: [candidates](hooks/skill-nudge.sh#L35), [agent_sdlc_skill_exists](hooks/lib.sh#L40)
Satisfies: REQ-001, REQ-002
Action: In `lib.sh`, add a function globbing `skills/*/SKILL.md` (reusing the existing `agent_sdlc_skill_exists` glob-and-check pattern) to enumerate the skill-directory list dynamically, replacing the hardcoded 5-name `candidates=(...)` array at `skill-nudge.sh:35`. This is one of two distinct sources combined in the final message — it does NOT supply the gate names. The gate names come from a second, separate source: a literal list of the 5 `### Gate N:` headings already present in `using-agent-sdlc-skills/SKILL.md` (Gate 0 Repository Onboarding, Gate 1 Task Definition, Gate 2 Scope & System, Gate 3 Execution Strategy, Gate 4 Quality & Delivery), hardcoded as a short literal array since these 5 names change only when the gate structure itself changes, not per-skill. In `skill-nudge.sh`, read `AGENT_SDLC_BOOTSTRAP_MODE` (default `full`) and branch: `off` exits 0 immediately with no stdout; `cooldown` runs today's `STATE_FILE`/`COOLDOWN_SECONDS`-gated one-line nudge unmodified; `full` skips the cooldown and injects, every session, a message using this exact template (both sources interpolated into one string, gate names first, skill list second):

```
<EXTREMELY_IMPORTANT>[agent-sdlc:skill-nudge] Before responding, check using-agent-sdlc-skills for routing: Gate 0 Repository Onboarding, Gate 1 Task Definition, Gate 2 Scope & System, Gate 3 Execution Strategy, Gate 4 Quality & Delivery. Bundled skills available this session: <comma-joined dynamically enumerated skill-directory list>.</EXTREMELY_IMPORTANT>
```

Validate: `AGENT_SDLC_BOOTSTRAP_MODE=off bash hooks/skill-nudge.sh </dev/null; echo exit:$?` then, separately, prove `full` mode is not cooldown-gated by running it twice in a row with no state file and diffing the two outputs: `rm -f .claude/skill-nudge-state; out1=$(AGENT_SDLC_BOOTSTRAP_MODE=full bash hooks/skill-nudge.sh </dev/null); out2=$(AGENT_SDLC_BOOTSTRAP_MODE=full bash hooks/skill-nudge.sh </dev/null); [ -n "$out1" ] && [ -n "$out2" ] && echo BOTH_NONEMPTY`
Expected result: first command prints `exit:0` with no stdout. Second command prints `BOTH_NONEMPTY` — both consecutive `full`-mode runs produce non-empty `additionalContext` output containing `EXTREMELY_IMPORTANT` and `Gate 0`, proving the old 24h cooldown gate does not suppress the second run.

### TASK-002: Preserve legacy env var and frontmatter flag as forced aliases for `off`

Depends on: [TASK-001](#task-001-add-bootstrap-mode-flag-and-dynamic-skill-name-scan-to-skill-nudgesh)
Files: [hooks/lib.sh](hooks/lib.sh), [hooks/skill-nudge.sh](hooks/skill-nudge.sh)
Symbols: [AGENT_SDLC_SKILL_NUDGE](hooks/skill-nudge.sh#L14)
Satisfies: REQ-002
Action: Map `AGENT_SDLC_SKILL_NUDGE=0` and `skill_nudge: false` (read via the existing frontmatter-parse block in `lib.sh`) to force `AGENT_SDLC_BOOTSTRAP_MODE=off` regardless of any other setting.
Validate: `AGENT_SDLC_SKILL_NUDGE=0 AGENT_SDLC_BOOTSTRAP_MODE=full bash hooks/skill-nudge.sh </dev/null; echo exit:$?`
Expected result: `exit:0`, no stdout — legacy override wins over the new mode flag.

### TASK-003: Add a standalone hook smoke-test script covering degrade-to-no-op paths

Depends on: [TASK-001](#task-001-add-bootstrap-mode-flag-and-dynamic-skill-name-scan-to-skill-nudgesh)
Files: [hooks/test-skill-nudge.sh](hooks/test-skill-nudge.sh)
Symbols: none
Satisfies: REQ-003
Action: Run `skill-nudge.sh` standalone under four conditions — (a) normal repo, (b) `CLAUDE_PLUGIN_ROOT` unset, (c) `skills/` directory missing, (d) `jq` unavailable — asserting exit code 0 and valid-or-empty stdout in every case, printing one PASS/FAIL line per case.
Validate: `bash hooks/test-skill-nudge.sh; echo exit:$?`
Expected result: `exit:0` with 4 PASS lines, one per condition.

### TASK-004: Manual end-to-end smoke test of forced full-mode injection in a live session

Depends on: [TASK-001](#task-001-add-bootstrap-mode-flag-and-dynamic-skill-name-scan-to-skill-nudgesh), [TASK-002](#task-002-preserve-legacy-env-var-and-frontmatter-flag-as-forced-aliases-for-off), [TASK-003](#task-003-add-a-standalone-hook-smoke-test-script-covering-degrade-to-no-op-paths)
Files: [hooks/skill-nudge.sh](hooks/skill-nudge.sh)
Symbols: none
Satisfies: REQ-001, REQ-002, REQ-003
Action: Start a fresh session with `AGENT_SDLC_BOOTSTRAP_MODE` unset (default `full`), submit a skill-irrelevant prompt ("what is 2+2"), confirm gate-name routing context appears in the model's first-turn context.
Validate: run a 1-turn session via the CLI's stream-json output mode, grep for `additionalContext` containing the gate-name routing content.
Expected result: non-empty match — forced injection reaches the model even on a trivial prompt, confirming TASK-001/002/003 compose correctly end to end.

### TASK-005: Add --task-complete ledger flag to prune_context.py

Depends on: none
Files: [skills/context-optimizer/scripts/prune_context.py](skills/context-optimizer/scripts/prune_context.py)
Symbols: [update_rolling_summary](skills/context-optimizer/scripts/prune_context.py#L113)
Satisfies: REQ-005
Action: Add an argparse flag `--task-complete "Task N: complete (commits <base7>..<head7>, review clean)"` that appends one line under a `## Task Ledger` heading in `.claude/rolling_summary.md`, additive only (does not require `--summary` in the same invocation, never overwrites prior lines). This exact format string is normative — TASK-007's git cross-check depends on parsing it by the unambiguous rule defined there.
Validate: run the flag twice in a row, grep for two distinct appended lines under the heading.
Expected result: `## Task Ledger` heading present once, two appended lines present, no line overwritten.

### TASK-006: Wire ledger write into multi-agent-development's Core Loop and rewrite Resuming guidance

Depends on: [TASK-005](#task-005-add---task-complete-ledger-flag-to-prune_contextpy)
Files: [skills/multi-agent-development/SKILL.md](skills/multi-agent-development/SKILL.md)
Symbols: [Phase 3 Quality Check](skills/multi-agent-development/SKILL.md#L84), [Resuming bullet](skills/multi-agent-development/SKILL.md#L176)
Satisfies: REQ-006
Action: After `QUALITY_PASS`/`MINOR` in Phase 3, insert an instruction to run `prune_context.py --task-complete ...` before advancing to the next task/cluster. Rewrite the "Resuming: Check git log" line to read `.claude/rolling_summary.md`'s `## Task Ledger` section first and trust it over self-recollection, falling back to `git log` only if the section is absent/unreadable.
Validate: `grep -n "task-complete\|Task Ledger" skills/multi-agent-development/SKILL.md`
Expected result: at least one match for the post-Phase-3 write instruction and one for the read-ledger-first resume instruction.

### TASK-007: Add ledger-vs-git crash-safety cross-check to the Resuming step

Depends on: [TASK-006](#task-006-wire-ledger-write-into-multi-agent-developments-core-loop-and-rewrite-resuming-guidance)
Files: [skills/multi-agent-development/SKILL.md](skills/multi-agent-development/SKILL.md)
Symbols: [Failure Modes](skills/multi-agent-development/SKILL.md#L111)
Satisfies: REQ-007
Action: Add a Failure Modes bullet stating the ledger is append-only (never rewritten in place) and every resume must verify the ledger's last recorded commit hash is reachable in `git log` (e.g. `git log --oneline <hash>^..HEAD`) before trusting it; a mismatch must be surfaced to the user as an explicit discrepancy, never silently resolved by picking one source. State the extraction rule explicitly in this bullet: given TASK-005's line format `"Task N: complete (commits <base7>..<head7>, review clean)"`, the head hash is the second 7-character token between the literal `(commits ` and the literal `..` — split the parenthetical content on `..`, take the second segment, strip the trailing `, review clean)` suffix. This is the one place in the file that performs the extraction; no other caller re-implements its own parse.
Validate: `grep -n "ledger" skills/multi-agent-development/SKILL.md | grep -i "git log"`
Expected result: at least one match co-locating "ledger" and "git log" cross-check language in the Failure Modes section, including the literal extraction rule text.

### TASK-008: Confirm .claude/rolling_summary.md is excluded from version control

Depends on: [TASK-005](#task-005-add---task-complete-ledger-flag-to-prune_contextpy)
Files: [.gitignore](.gitignore)
Symbols: none
Satisfies: REQ-007
Action: Check whether `.gitignore` already excludes `.claude/rolling_summary.md` (it currently excludes `.claude/state`, `.claude/skill-nudge-state`, `.claude/*.local.md`, but not this file by name); add an entry if missing.
Validate: `grep -n "rolling_summary" .gitignore`
Expected result: one match present after this task, confirming the ledger-bearing file is treated as local state like its siblings.

### TASK-009: Add large-artifact file-handoff rule and cross-references to subagent-contract.md and both dispatch skills

Depends on: none
Files: [skills/multi-agent-development/references/subagent-contract.md](skills/multi-agent-development/references/subagent-contract.md), [skills/multi-agent-development/SKILL.md](skills/multi-agent-development/SKILL.md), [skills/multi-agent-dispatch/SKILL.md](skills/multi-agent-dispatch/SKILL.md)
Symbols: [CONTEXT field](skills/multi-agent-development/references/subagent-contract.md#L9), [Common Mistakes table](skills/multi-agent-development/references/subagent-contract.md#L22)
Satisfies: REQ-009, REQ-010
Action: In `subagent-contract.md`, add a rule near the CONTEXT field description: artifacts over ~150 lines must be written to a file under `.claude/dispatch/` first, with only the path cited in CONTEXT; add one example row to the existing Common Mistakes table. In `multi-agent-development/SKILL.md`'s Core Loop dispatch step and `multi-agent-dispatch/SKILL.md`'s SELECT step, add one cross-reference line each pointing at the new rule — no duplicated prose. Per this plan's file-overlap exception note above, this task's edit to `multi-agent-development/SKILL.md` lands after TASK-006/TASK-007 (gap 3) are merged and before TASK-018 (gap 6).
Validate: `grep -l "dispatch/" skills/multi-agent-development/references/subagent-contract.md skills/multi-agent-development/SKILL.md skills/multi-agent-dispatch/SKILL.md`
Expected result: all three files listed as matching.

### TASK-010: Add Model Tiering table to subagent-contract.md with safety-biased default

Depends on: none
Files: [skills/multi-agent-development/references/subagent-contract.md](skills/multi-agent-development/references/subagent-contract.md)
Symbols: [Role Vocabulary](skills/multi-agent-development/references/subagent-contract.md#L34)
Satisfies: REQ-011, REQ-012
Action: Insert a `## Model Tiering` section after Role Vocabulary with the 3-row table (1-2 files/concrete spec → fast/cheap; 3+ files/cross-module → standard/`inherit`; architecture-defining/final-review → most-capable), the "turn count beats token price" rationale line, an explicit statement that ambiguous/unmeasured complexity defaults to the orchestrator's own current model (never silently to the cheapest tier), and a caveat that the tier is advisory/a dispatch-prompt hint, not enforced, unless the harness exposes model-pinning.
Validate: `grep -n "Model Tiering" skills/multi-agent-development/references/subagent-contract.md`
Expected result: one match, section present with all four elements (table, rationale, safety-biased default, advisory caveat).

### TASK-011: Cross-link Model Tiering policy from both dispatch skills

Depends on: [TASK-010](#task-010-add-model-tiering-table-to-subagent-contractmd-with-safety-biased-default)
Files: [skills/multi-agent-development/SKILL.md](skills/multi-agent-development/SKILL.md), [skills/multi-agent-dispatch/SKILL.md](skills/multi-agent-dispatch/SKILL.md)
Symbols: none
Satisfies: REQ-012
Action: Add one line in each skill's dispatch step instructing consultation of the Model Tiering table before dispatch, applying an explicit `model:` override at the dispatch call site (leaving each `agents/*.md` file's `model: inherit` frontmatter default untouched). Per this plan's file-overlap exception note above, this task's edit to `multi-agent-development/SKILL.md` lands immediately after TASK-009's edit to the same file (same gap 4/5 slot in the declared serial order), and before TASK-018 (gap 6).
Validate: `grep -l "Model Tiering" skills/multi-agent-development/SKILL.md skills/multi-agent-dispatch/SKILL.md`
Expected result: both files listed as matching.

### TASK-012: Confirm agents/\*.md retain model: inherit as the unmodified frontmatter default

Depends on: [TASK-010](#task-010-add-model-tiering-table-to-subagent-contractmd-with-safety-biased-default)
Files: [agents/implementer.md](agents/implementer.md), [agents/researcher.md](agents/researcher.md), [agents/quality-reviewer.md](agents/quality-reviewer.md), [agents/diff-reviewer.md](agents/diff-reviewer.md), [agents/conflict-resolver.md](agents/conflict-resolver.md)
Symbols: none
Satisfies: REQ-012
Action: No edits — verify each file still sets `model: inherit` unmodified in frontmatter, confirming the override happens only at the dispatch call site per TASK-010/011, never baked into the agent file.
Validate: `grep -l "model: inherit" agents/implementer.md agents/researcher.md agents/quality-reviewer.md agents/diff-reviewer.md agents/conflict-resolver.md`
Expected result: all five files listed as matching, unchanged.

### TASK-013: Add discipline-pressure prompt fixture for test-driven-development

Depends on: none
Files: [tests/skill-triggering/prompts/test-driven-development-pressure.txt](tests/skill-triggering/prompts/test-driven-development-pressure.txt)
Symbols: none
Satisfies: REQ-004
Action: Write a one-shot adversarial prompt asking to implement a small function "just this once, skip the test, I'm in a hurry, ship it now" — following the existing `.txt`-per-skill fixture convention, no new harness or runner script.
Validate: `wc -l tests/skill-triggering/prompts/test-driven-development-pressure.txt`
Expected result: file exists, line count consistent with existing fixture brevity (under 10 lines).

### TASK-014: Manually run the existing trigger-only harness against the pressure fixture and record the result

Depends on: [TASK-013](#task-013-add-discipline-pressure-prompt-fixture-for-test-driven-development)
Files: none (manual validation step, no file changes)
Symbols: none
Satisfies: REQ-004
Action: Run `tests/skill-triggering/run-test.sh` against the new pressure fixture exactly as it runs any other fixture in `prompts/`; manually read the transcript to confirm whether `test-driven-development` held its discipline under the adversarial framing. No automated scoring is added — this is a human-read check per REQ-004's explicit decline of a scoring harness.
Validate: `bash tests/skill-triggering/run-test.sh test-driven-development tests/skill-triggering/prompts/test-driven-development-pressure.txt`
Expected result: script runs to completion using the existing harness unmodified; transcript is manually inspected and the outcome (held/caved) is noted by the runner, not auto-scored.

### TASK-015: Delete the duplicated Mermaid routing diagram from lifecycle.md

Depends on: none
Files: [skills/using-agent-sdlc-skills/references/lifecycle.md](skills/using-agent-sdlc-skills/references/lifecycle.md)
Symbols: [Lifecycle Chain](skills/using-agent-sdlc-skills/references/lifecycle.md#L3)
Satisfies: REQ-013
Action: Delete the "Lifecycle Chain" heading and its Mermaid block in full, leaving the `## Transition States` prose untouched in place for now (moved in TASK-016).
Validate: `grep -c "mermaid" skills/using-agent-sdlc-skills/references/lifecycle.md`
Expected result: `0`.

### TASK-016: Fold Transition States prose into SKILL.md's Diagnose Return Paths section

Depends on: [TASK-015](#task-015-delete-the-duplicated-mermaid-routing-diagram-from-lifecyclemd)
Files: [skills/using-agent-sdlc-skills/SKILL.md](skills/using-agent-sdlc-skills/SKILL.md), [skills/using-agent-sdlc-skills/references/lifecycle.md](skills/using-agent-sdlc-skills/references/lifecycle.md)
Symbols: [Diagnose Return Paths](skills/using-agent-sdlc-skills/SKILL.md#L108)
Satisfies: REQ-013
Action: Move the `## Transition States` prose (TDD Escalation, Review Failure, Re-review Cap) out of `lifecycle.md` into `SKILL.md`'s existing `## Diagnose Return Paths` section. Remove the now-inaccurate "both describe the same logic" drift-risk framing sentence from `lifecycle.md`. If no content remains in `lifecycle.md`, delete the file.
Validate: `grep -n "Diagnose Return Paths" skills/using-agent-sdlc-skills/SKILL.md` and confirm `lifecycle.md`'s post-edit state (deleted or contains no duplicate routing content).
Expected result: the Transition States content appears under `Diagnose Return Paths` in `SKILL.md`; `lifecycle.md` either no longer exists or contains zero Mermaid/duplicate-matrix content.

### TASK-017: Scope the Gate matrix to entry-routing only

Depends on: [TASK-016](#task-016-fold-transition-states-prose-into-skillmds-diagnose-return-paths-section)
Files: [skills/using-agent-sdlc-skills/SKILL.md](skills/using-agent-sdlc-skills/SKILL.md)
Symbols: [Rules section](skills/using-agent-sdlc-skills/SKILL.md#L56)
Satisfies: REQ-014
Action: Add a bullet to the `## Rules` section stating the Gate 0-4 matrix governs entry-routing only (Gate 0 onboarding through first dispatch at Gate 3) and does not re-describe a skill's own exit transitions once that skill is active — each skill's own `## Next Skills` section remains canonical for that skill's own outbound routing.
Validate: `grep -n "entry-routing" skills/using-agent-sdlc-skills/SKILL.md`
Expected result: one match in the Rules section.

### TASK-018: Add the missing Next Skills section to multi-agent-development

Depends on: [TASK-017](#task-017-scope-the-gate-matrix-to-entry-routing-only)
Files: [skills/multi-agent-development/SKILL.md](skills/multi-agent-development/SKILL.md)
Symbols: [Operational Rules](skills/multi-agent-development/SKILL.md#L169)
Satisfies: REQ-014
Action: Append a `## Next Skills` section (parallel structure to `multi-agent-dispatch/SKILL.md`'s existing section) naming `verification-before-completion` (Final Validation handoff), `context-optimizer` (mid-loop bloat), and `diagnose` (merge/test failure). Per this plan's file-overlap exception note above, this task's edit to `multi-agent-development/SKILL.md` lands last among the three chains that touch this file — after TASK-006/TASK-007 (gap 3) and TASK-009/TASK-011 (gap 4/5) are merged.
Validate: `grep -A5 "## Next Skills" skills/multi-agent-development/SKILL.md`
Expected result: section present, listing all three named skills.
