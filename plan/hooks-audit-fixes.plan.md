# hooks-audit-fixes

Spec: [hooks-audit-fixes.specs.md](hooks-audit-fixes.specs.md)

## Goal

Fix the five verified bugs from the `hooks/` audit — a fail-open crash in the blocking security guard, a broken JSON-escaping helper (duplicated in two files), an unsanitized telemetry log field, and a dead code branch — without changing any existing intended-block/intended-allow behavior.

## Current Context

- [hooks/shell-safety.sh](hooks/shell-safety.sh): PreToolUse Bash guard. `extract_command` (~L21-40) crashes via `set -e` when `jq` returns non-zero on malformed JSON, because `2>/dev/null` (L29) hides stderr but not exit status — confirmed: `printf '[1,2,3]' | bash hooks/shell-safety.sh` exits `5`, not `0`. Local `json_escape` (~L48-58) shares the broken backslash-escaping idiom from `lib.sh`. Segment splitter (~L107) has a dead `\|\|` sed alternation.
- [hooks/lib.sh](hooks/lib.sh): `agent_dev_json_escape` (~L9-24) jq-less fallback uses `${out//\\/\\\\}` which does not match a literal backslash on this bash (5.3.9, Cygwin, `patsub_replacement` on), and `${out//$'\n'/\\n}` drops the backslash in the replacement — confirmed via direct execution, both produce invalid/wrong output.
- [hooks/telemetry-capture.sh](hooks/telemetry-capture.sh): `tool` (~L14) is written unsanitized into a one-line-per-event log; an embedded newline breaks that contract — confirmed via direct execution.
- All findings and their exact repro commands are in [hooks-audit-fixes.specs.md](hooks-audit-fixes.specs.md) Section 7 and `AC-001`–`AC-008`.

## PHASE-001: Implementation

### TASK-001: Fix fail-open crash in extract_command

Depends on: none
Files: [hooks/shell-safety.sh](hooks/shell-safety.sh)
Symbols: [extract_command](hooks/shell-safety.sh#L21), [call site](hooks/shell-safety.sh#L42)
Satisfies: REQ-001
Action: At line 42, change `command=$(extract_command "$input")` to `command=$(extract_command "$input") || command=""` so a non-zero exit from the jq branch inside `extract_command` cannot abort the script under `set -e`; the existing `[ -z "$command" ]` check at L44 then handles it as the pre-existing "no command present" allow path.
Validate: `printf '%s' '[1,2,3]' | bash hooks/shell-safety.sh >/dev/null 2>&1; echo $?; printf '%s' '{"tool_input":{"command":"rm -rf /"}' | bash hooks/shell-safety.sh >/dev/null 2>&1; echo $?`
Expected result: both print `0` (was `5` before the fix).

### TASK-002: Fix backslash/control-char escaping in agent_dev_json_escape

Depends on: TASK-001
Files: [hooks/lib.sh](hooks/lib.sh)
Symbols: [agent_dev_json_escape](hooks/lib.sh#L9)
Satisfies: REQ-002
Action: In the bash-only fallback branch (~L17-23), replace the backslash/newline/CR/tab substitutions with pattern-matching forms that work under `patsub_replacement`: introduce `local bs='\'`, change the backslash line to `out="${out//"$bs"/\\\\}"` (must run before the other substitutions), and change the `\n`/`\r`/`\t` replacement strings to single-quoted literals (`'\n'`, `'\r'`, `'\t'`) so the backslash in the replacement is preserved.
Validate: `bash -c 'source hooks/lib.sh; v=$(agent_dev_json_escape "C:\Users\x"); printf "{\"v\":\"%s\"}" "$v" | jq -e ".v == \"C:\\\\Users\\\\x\""'; echo EXIT=$?` and `bash -c 'source hooks/lib.sh; v=$(agent_dev_json_escape $"line1\nline2"); printf "{\"v\":\"%s\"}" "$v" | jq -e ".v == \"line1\nline2\""'; echo EXIT=$?`
Expected result: both print `true` then `EXIT=0`.

### TASK-003: Apply the identical escaping fix to shell-safety.sh's local json_escape

Depends on: TASK-002
Files: [hooks/shell-safety.sh](hooks/shell-safety.sh)
Symbols: [json_escape](hooks/shell-safety.sh#L48)
Satisfies: REQ-003
Action: Apply the same pattern-matching fix from TASK-002 to the local `json_escape` function (~L48-58) — `local bs='\'`, backslash substitution via `"${s//"$bs"/\\\\}"` first, then single-quoted `'\n'`/`'\r'`/`'\t'` replacements — keeping this copy self-contained (no sourcing of `lib.sh`, per the file's existing design note at L3-5).
Validate: `bash -c 'source <(sed -n "48,58p" hooks/shell-safety.sh; echo); '` — instead, unit-test inline: `bash -c "$(awk '/^json_escape\(\)/,/^}/' hooks/shell-safety.sh); v=\$(json_escape 'C:\\Windows'); printf '{\"v\":\"%s\"}' \"\$v\" | jq -e '.v == \"C:\\\\\\\\Windows\"'"; echo EXIT=$?`
Expected result: prints `true` then `EXIT=0`.

### TASK-004: Sanitize tool_name before writing to telemetry.log

Depends on: TASK-003
Files: [hooks/telemetry-capture.sh](hooks/telemetry-capture.sh)
Symbols: [tool extraction](hooks/telemetry-capture.sh#L14)
Satisfies: REQ-004
Action: After line 14's `tool=$(...)` assignment, add `tool="${tool//$'\n'/ }"; tool="${tool//$'\r'/}"` to strip embedded newlines (replaced with a space) and carriage returns before `agent_dev_telemetry_append` writes the line at L16.
Validate: `rm -f .claude/telemetry.log; printf '%s' '{"tool_name":"a\nb"}' | bash hooks/telemetry-capture.sh; wc -l < .claude/telemetry.log`
Expected result: prints `1`.

### TASK-005: Remove dead sed alternation in segment splitter

Depends on: TASK-004
Files: [hooks/shell-safety.sh](hooks/shell-safety.sh)
Symbols: [segment splitter](hooks/shell-safety.sh#L107)
Satisfies: REQ-005
Action: At line 107, simplify `sed -E 's/&&|\|\|/\n/g'` to `sed -E 's/&&/\n/g'`, since the preceding `tr ';|' '\n'` already removes every literal `|` so the `\|\|` alternative can never match.
Validate: `grep -n "sed -E 's/&&" hooks/shell-safety.sh`
Expected result: output shows `sed -E 's/&&/\n/g'` with no `\|\|` present.

## PHASE-END: Acceptance

### TASK-006: Final acceptance verification

Depends on: [TASK-005](#task-005-remove-dead-sed-alternation-in-segment-splitter)
Files: none
Symbols: none
Satisfies: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008
Action: Run every `VAL-###` command from the spec in sequence and confirm each matches its expected result, including the regression guard (`VAL-003`: well-formed `rm -rf /` payload still exits `2`; `ls -la` payload still exits `0`).
Validate: `printf '%s' '{"tool_input":{"command":"rm -rf /"}}' | bash hooks/shell-safety.sh >/dev/null 2>&1; echo $?; printf '%s' '{"tool_input":{"command":"ls -la"}}' | bash hooks/shell-safety.sh >/dev/null 2>&1; echo $?`
Expected result: prints `2` then `0` — all prior block/allow behavior unchanged after TASK-001 through TASK-005.
