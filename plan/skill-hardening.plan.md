# skill-hardening

Spec: [skill-hardening.specs.md](skill-hardening.specs.md)

## Goal

Harden `using-agent-dev-skills` with a subagent guard, rebuttal red-flags table, and skill-triggering test infrastructure so the skill's correctness is empirically verifiable.

## PHASE-001: Patch SKILL.md

### TASK-001: Add SUBAGENT-STOP guard to SKILL.md

Depends on: none
Files: [skills/using-agent-dev-skills/SKILL.md](skills/using-agent-dev-skills/SKILL.md)
Symbols: none
Satisfies: REQ-001
Action: Insert a `<SUBAGENT-STOP>` block immediately after the YAML frontmatter closing `---` and before `# Using Agent Dev Skills`. Block content: "If you were dispatched as a subagent to execute a specific task, skip this skill."
Validate: `grep -q "<SUBAGENT-STOP>" skills/using-agent-dev-skills/SKILL.md && echo PASS || echo FAIL`
Expected result: PASS printed; block is present and positioned before the first `#` heading.

### TASK-002: Replace prose red-flags with EXTREMELY-IMPORTANT rebuttal table

Depends on: TASK-001
Files: [skills/using-agent-dev-skills/SKILL.md](skills/using-agent-dev-skills/SKILL.md)
Symbols: none
Satisfies: REQ-002
Action: Remove the existing "## Do Not Rationalize Skipping" prose bullet section. Replace it with an `<EXTREMELY-IMPORTANT>` block containing a two-column Markdown table with headers `Rationalization` and `Reality`. Rows must cover all four original rationalizations plus at least two additional ones sourced from obra/superpowers' red-flags table.
Validate: `grep -q "EXTREMELY-IMPORTANT" skills/using-agent-dev-skills/SKILL.md && grep -q "Rationalization" skills/using-agent-dev-skills/SKILL.md && echo PASS || echo FAIL`
Expected result: PASS printed; both the block wrapper and the table header are present in the file.

## PHASE-002: Build test infrastructure

### TASK-003: Write 13 naive-prompt files in tests/skill-triggering/prompts/

Depends on: none
Files: [tests/skill-triggering/prompts/](tests/skill-triggering/prompts/) `[UNVERIFIED — new directory]`
Symbols: none
Satisfies: REQ-003
Action: Create directory `tests/skill-triggering/prompts/`. Write one `.txt` file per routed skill — file name matches skill name exactly (e.g. `brainstorming.txt`). Each prompt is a natural user message that would trigger that skill but does NOT mention the skill name. Base prompts on the routing table's task-signal column.
Validate: `[ "$(ls tests/skill-triggering/prompts/*.txt 2>/dev/null | wc -l)" -ge 13 ] && echo PASS || echo FAIL`
Expected result: PASS printed; at least 13 prompt files exist.

### TASK-004: Write run-test.sh

Depends on: TASK-003
Files: [tests/skill-triggering/run-test.sh](tests/skill-triggering/run-test.sh) `[UNVERIFIED — new file]`
Symbols: none
Satisfies: REQ-004, SEC-001
Action: Create `tests/skill-triggering/run-test.sh`. Script accepts `SKILL_NAME PROMPT_FILE [MAX_TURNS]`, runs `claude -p "$PROMPT" --plugin-dir "$PLUGIN_DIR" --output-format stream-json --max-turns "${MAX_TURNS:-3}"`, greps stream-json output for `"name":"Skill"` and the skill name pattern, exits 0 on match and 1 on no match. `--dangerously-skip-permissions` is added only when `SKIP_PERMISSIONS=1` is set. Make the script executable (`chmod +x`).
Validate: `bash -n tests/skill-triggering/run-test.sh && echo PASS`
Expected result: PASS printed; no bash syntax errors.

### TASK-005: Write run-all.sh

Depends on: TASK-004
Files: [tests/skill-triggering/run-all.sh](tests/skill-triggering/run-all.sh) `[UNVERIFIED — new file]`
Symbols: none
Satisfies: REQ-005
Action: Create `tests/skill-triggering/run-all.sh`. Script iterates over all `.txt` files in `prompts/` (relative to script), derives skill name from filename stem, calls `run-test.sh SKILL_NAME PROMPT_FILE`, accumulates pass/fail counts, prints per-skill result and final summary, exits 0 if all pass and 1 if any fail. Make the script executable.
Validate: `bash -n tests/skill-triggering/run-all.sh && echo PASS`
Expected result: PASS printed; no bash syntax errors.

### TASK-006: Verify SEC-001 — no hardcoded --dangerously-skip-permissions

Depends on: TASK-004, TASK-005
Files: [tests/skill-triggering/run-test.sh](tests/skill-triggering/run-test.sh) `[UNVERIFIED — new file]`
Symbols: none
Satisfies: SEC-001
Action: Confirm that neither `run-test.sh` nor `run-all.sh` contains `--dangerously-skip-permissions` as a hardcoded string. The flag MUST only appear inside a conditional block gated on `$SKIP_PERMISSIONS`.
Validate: `! grep -qn "dangerously-skip-permissions" tests/skill-triggering/run-test.sh tests/skill-triggering/run-all.sh && echo PASS || (grep -n "dangerously-skip-permissions" tests/skill-triggering/run-test.sh tests/skill-triggering/run-all.sh; echo FAIL)`
Expected result: PASS printed; no hardcoded flag found outside a conditional block.

## PHASE-003: Acceptance

### TASK-007: Final acceptance verification

Depends on: TASK-002, TASK-005, TASK-006
Files: none
Symbols: none
Satisfies: AC-001, AC-002, AC-003, AC-004, AC-005
Action: Run all five VAL commands from the spec sequentially and confirm each returns PASS or expected count.
Validate: `grep -q "<SUBAGENT-STOP>" skills/using-agent-dev-skills/SKILL.md && grep -q "EXTREMELY-IMPORTANT" skills/using-agent-dev-skills/SKILL.md && [ "$(ls tests/skill-triggering/prompts/*.txt 2>/dev/null | wc -l)" -ge 13 ] && bash -n tests/skill-triggering/run-test.sh && bash -n tests/skill-triggering/run-all.sh && npm run validate && echo ALL_PASS`
Expected result: All gates pass sequentially; `npm run validate` reports "All validations passed!"; ALL_PASS is printed.
