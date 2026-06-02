# skill-hardening

## 1. Goal

- Harden the `using-agent-dev-skills` skill and create a skill-triggering test suite, based on gaps identified via obra/superpowers comparison.
- Completion signal: `npm run validate` passes; SKILL.md contains `<SUBAGENT-STOP>` and a rebuttal red-flags table; `tests/skill-triggering/prompts/` holds one naive-prompt `.txt` per routed skill; `run-test.sh` and `run-all.sh` are present and syntax-valid.

## 2. Requirements

- `REQ-001`: SKILL.md MUST include a `<SUBAGENT-STOP>` block immediately after the frontmatter that instructs dispatched subagents to skip the skill entirely.
- `REQ-002`: SKILL.md MUST replace the prose "Do Not Rationalize Skipping" bullet list with a two-column Markdown table (columns: `Rationalization` | `Reality`) wrapped in an `<EXTREMELY-IMPORTANT>` HTML block.
- `REQ-003`: `tests/skill-triggering/prompts/` MUST contain one `.txt` naive-prompt file for each of the 13 routed skills (brainstorming, planning, test-driven-development, diagnose, code-review, refactor, architecture, create-hook, create-agent, skill-builder, github-automation, verification-before-completion, agents-maintainer). Prompts MUST NOT mention the skill name — they are natural user messages.
- `REQ-004`: `tests/skill-triggering/run-test.sh` MUST accept two positional arguments (`<skill-name>` `<prompt-file>`), run `claude -p` with `--plugin-dir .` and `--output-format stream-json`, and exit 0 if the `Skill` tool was invoked with the correct skill name, exit 1 otherwise.
- `REQ-005`: `tests/skill-triggering/run-all.sh` MUST iterate over all 13 prompt files, call `run-test.sh` for each, and print a pass/fail summary with total counts.
- `SEC-001`: Test scripts MUST NOT embed `--dangerously-skip-permissions` as a hardcoded flag; if needed, it MUST be passed as an optional environment variable `SKIP_PERMISSIONS=1`.

## 3. Constraints

- `CON-001`: Changes to SKILL.md MUST NOT alter the routing table contents (skill names, task signals) — only structural/markup changes are permitted.
- `CON-002`: `npm run validate` MUST pass after all file changes.
- `CON-003`: Test scripts MUST be POSIX bash (not PowerShell) to match obra's pattern and remain CI-portable.

## 4. Interfaces

**SKILL.md** — consumed by Claude agent via `Skill` tool

- Input: `trigger` (string, implicit) — user message or task context that caused the skill to load
- Output: agent invokes downstream skill from routing table; emits one-line announcement before invoking
- Error/guard: when agent is a dispatched subagent, `SUBAGENT-STOP` block causes skill body to be skipped entirely

**run-test.sh** — accepts `SKILL_NAME PROMPT_FILE [MAX_TURNS]`

- Input: `$1` skill name (string, required); `$2` path to `.txt` prompt file (string, required); `$3` max turns (integer, optional, default 3)
- Output: `✅ PASS` or `❌ FAIL` line plus skills-triggered list on stdout; exit 0 on PASS, exit 1 on FAIL
- Errors: missing arguments → print usage, exit 1; `claude` not on PATH → print actionable error, exit 1

**run-all.sh** — no arguments; reads `prompts/` directory relative to script location

- Input: none
- Output: per-skill pass/fail lines; summary `Passed: N  Failed: M`; exit 0 if all pass, exit 1 if any fail
- Errors: prompts directory missing → print error, exit 1

## 5. Context

- Files: `skills/using-agent-dev-skills/SKILL.md`
- Current behavior: skill has prose bullet red-flags and no subagent guard; no test infrastructure exists
- Conventions: AGENTS.md — ESM for JS, kebab-case names, bash scripts in `tests/`; `npm run validate` is the plugin validation gate

## 6. Acceptance Criteria & Validation

- `AC-001`: SKILL.md contains a `<SUBAGENT-STOP>` block.
- `VAL-001`: `grep -q "<SUBAGENT-STOP>" skills/using-agent-dev-skills/SKILL.md && echo PASS`
- `AC-002`: SKILL.md contains an `<EXTREMELY-IMPORTANT>` block wrapping a rebuttal table.
- `VAL-002`: `grep -q "EXTREMELY-IMPORTANT" skills/using-agent-dev-skills/SKILL.md && echo PASS`
- `AC-003`: All 13 prompt files are present in `tests/skill-triggering/prompts/`.
- `VAL-003`: `[ "$(ls tests/skill-triggering/prompts/*.txt 2>/dev/null | wc -l)" -ge 13 ] && echo PASS || echo FAIL`
- `AC-004`: `npm run validate` passes with zero errors.
- `VAL-004`: `npm run validate`
- `AC-005`: Both shell scripts are present and pass bash syntax check.
- `VAL-005`: `bash -n tests/skill-triggering/run-test.sh && bash -n tests/skill-triggering/run-all.sh && echo PASS`

## 7. Examples & Edge Cases

**Positive example — SUBAGENT-STOP:**

```text
Input:  Subagent dispatched with prompt "refactor this function"
Output: Skill body is skipped; subagent proceeds directly to refactor
```

**Positive example — rebuttal table:**

```text
Input:  Agent thinks "This is simple, skills are overkill"
Output: Table row "This is simple, skills are overkill | Simple things become complex. Use it." is immediately visible
```

**Edge cases:**

- Prompt file missing → run-test.sh prints usage and exits 1 (no claude invocation)
- `claude` not on PATH → run-test.sh prints actionable error, exits 1
- Skill triggered but wrong skill name → FAIL with list of what was actually triggered
