# hooks-audit-fixes

## 1. Goal

- One sentence: Fix the five verified bugs found in the `C:\agent-dev\hooks` audit (one fail-open in the blocking security guard, one broken JSON-escaping helper, and three low-severity correctness/cleanup issues) without changing any intended-block/intended-allow behavior.
- Completion signal: all five findings' reproduction commands (documented in Section 7) now produce the expected/fixed behavior, and the existing hook test suite (if present) still passes.

## 2. Requirements

- `REQ-001`: The `extract_command` function in `shell-safety.sh` MUST NOT let a non-zero `jq` exit status abort the script via `set -e`; on any malformed/unindexable JSON payload the script MUST fall through to the existing "no command present → exit 0" branch instead of crashing with an uncontrolled exit code.
- `REQ-002`: `agent_dev_json_escape` in `lib.sh` (jq-less fallback) MUST produce a backslash-faithful JSON string value for any input, on the project's actual bash runtime (GNU bash 5.3.9, Cygwin/Git Bash, `patsub_replacement` on) — every literal backslash escaped to two backslashes, with the backslash preserved in `\n`/`\r`/`\t` escapes.
- `REQ-003`: The local `json_escape` helper in `shell-safety.sh` MUST receive the identical backslash-escaping fix specified in `REQ-002`.
- `REQ-004`: `telemetry-capture.sh` MUST strip embedded newline and carriage-return bytes from `tool_name` before it is written to `telemetry.log`, preserving the one-line-per-event log contract.
- `REQ-005`: The `sed` expression in `shell-safety.sh`'s segment splitter MUST NOT contain the dead `\|\|` alternation (made dead by the preceding `tr ';|' '\n'`, which already removes every literal `|`).

## 3. Constraints

- `CON-001`: The fix MUST NOT change any of the guard's existing intended-block or intended-allow outcomes (verified set: `rm -rf /` variants, `git push --force` to main/master variants, `git clean -fdx` variants all still block; `rm -rf /tmp/foo`, `git push origin maintenance`, `git clean -fd` still allow).
- `CON-002`: The fix MUST NOT introduce a `jq` hard dependency — the jq-absent fallback paths in `lib.sh` and `shell-safety.sh` must continue to work standalone.
- `CON-003`: MUST NOT add new abstractions, config flags, or refactor unrelated code — this is a surgical bugfix pass, not a redesign.

## 4. Interfaces

These are Bash hook scripts invoked by the Claude Code hook runner via stdin/exit-code/stdout-JSON, not HTTP/RPC interfaces. Documented as input/output/error per the template:

### `shell-safety.sh` (PreToolUse Bash guard)

**Input:**
- stdin (string, required): PreToolUse JSON payload, expected shape `{"tool_input":{"command": "..."}}`, but may be malformed/abnormal.

**Output:**
- exit code `0`: command allowed, no stdout.
- exit code `2`: command denied; JSON with `hookSpecificOutput.permissionDecision="deny"` and `systemMessage` on stderr.

**Errors:**
- Malformed JSON / non-object payload → MUST still resolve to exit `0` (no command found) per REQ-001, never an uncontrolled non-0/non-2 exit.
- jq absent → falls back to regex extraction (existing behavior, unchanged by this plan).

### `lib.sh: agent_dev_json_escape` (shared helper, no jq)

**Input:**
- `$1` (string, required): raw text to embed as a JSON string value.

**Output:**
- stdout (string): the input with `\`, `"`, `\n`, `\r`, `\t` escaped such that wrapping it in `"..."` yields valid JSON, verified via `jq .` round-trip.

**Errors:**
- N/A (pure string transform; no failure mode beyond incorrect escaping, which is the bug being fixed).

### `telemetry-capture.sh` (PostToolUse logger)

**Input:**
- stdin (string, required): PostToolUse JSON payload with `.tool_name`.

**Output:**
- one line appended to `.claude/telemetry.log` per invocation, regardless of `tool_name` content.

**Errors:**
- jq absent or `tool_name` missing → logs `unknown` (existing behavior, unchanged).

## 5. Context

- Files:
  - [hooks/shell-safety.sh](hooks/shell-safety.sh) — `extract_command` (~L21-40), `json_escape` (~L48-58), segment splitter (~L107).
  - [hooks/lib.sh](hooks/lib.sh) — `agent_dev_json_escape` (~L9-24).
  - [hooks/telemetry-capture.sh](hooks/telemetry-capture.sh) — tool name extraction/log line (~L13-16).
- Current behavior: documented and reproduced in the audit (see Section 7 for exact repro commands/outputs). All five issues were confirmed by direct execution on this machine's bash (GNU bash 5.3.9, Cygwin), not just static reading.
- Conventions: this project's hook scripts use `set -euo pipefail`, prefer `jq` with a bash-only fallback, and follow a strict design rule that `shell-safety.sh` must never silently disable itself, while the additive hooks (`lib.sh`, `skill-nudge.sh`, `telemetry-capture.sh`) must degrade to a no-op on failure, never emit wrong/corrupt output.

## 6. Acceptance Criteria & Validation

- `AC-001`: A malformed JSON payload (e.g. `[1,2,3]`) piped into `shell-safety.sh` exits `0`, not an uncontrolled code.
  `VAL-001`: `printf '%s' '[1,2,3]' | bash hooks/shell-safety.sh >/dev/null 2>&1; echo $?` → expected output `0`.
- `AC-002`: A truncated/malformed JSON payload containing a dangerous command still does not crash the script (falls through to allow, consistent with "no command extracted", not a guard bypass regression since the well-formed case still blocks).
  `VAL-002`: `printf '%s' '{"tool_input":{"command":"rm -rf /"}' | bash hooks/shell-safety.sh >/dev/null 2>&1; echo $?` → expected output `0` (was `5` before fix).
- `AC-003`: The existing guard behavior for all previously-verified block/allow cases is unchanged.
  `VAL-003`: `printf '%s' '{"tool_input":{"command":"rm -rf /"}}' | bash hooks/shell-safety.sh >/dev/null 2>&1; echo $?` → expected `2`. `printf '%s' '{"tool_input":{"command":"ls -la"}}' | bash hooks/shell-safety.sh >/dev/null 2>&1; echo $?` → expected `0`.
- `AC-004`: `agent_dev_json_escape` round-trips a backslash-containing string into valid, faithful JSON.
  `VAL-004`: `bash -c 'source hooks/lib.sh; v=$(agent_dev_json_escape "C:\Users\x"); printf "{\"v\":\"%s\"}" "$v" | jq -e ".v == \"C:\\\\Users\\\\x\""'` → expected exit `0` (true).
- `AC-005`: `agent_dev_json_escape` round-trips an embedded newline into valid JSON containing a real `\n` escape (not a bare `n`).
  `VAL-005`: `bash -c 'source hooks/lib.sh; v=$(agent_dev_json_escape $"line1\nline2"); printf "{\"v\":\"%s\"}" "$v" | jq -e ".v == \"line1\nline2\""'` → expected exit `0` (true).
- `AC-006`: `shell-safety.sh`'s local `json_escape` has the same backslash fix and produces valid JSON for a denied command containing a backslash.
  `VAL-006`: `printf '%s' '{"tool_input":{"command":"rm -rf C:\\\\Windows"}}' | bash hooks/shell-safety.sh 2>&1 1>/dev/null | jq . >/dev/null; echo $?` → expected `0` (valid JSON on stderr; note: this command path doesn't match the rm-deny regex's root-target pattern, so use any denied command containing a literal backslash in the test, or directly unit-test the local `json_escape` function as in VAL-004's pattern).
- `AC-007`: A `tool_name` containing an embedded newline produces exactly one line in `telemetry.log`.
  `VAL-007`: `rm -f .claude/telemetry.log; printf '%s' '{"tool_name":"a\nb"}' | bash hooks/telemetry-capture.sh; wc -l < .claude/telemetry.log` → expected `1`.
- `AC-008`: The dead `\|\|` sed alternation is removed and segment splitting still works identically for `&&`/`;`/`|`-joined commands.
  `VAL-008`: `grep -n "sed -E 's/&&" hooks/shell-safety.sh` → expected pattern shows only `&&` in the alternation (no `\|\|`); re-run `VAL-003` to confirm no regression.

## 7. Examples & Edge Cases

**Positive example (REQ-001/AC-002):**
```
Input:  printf '%s' '{"tool_input":{"command":"rm -rf /"}' | bash hooks/shell-safety.sh   (truncated JSON)
Before: exit 5 (set -e abort inside extract_command, jq parse error swallowed by 2>/dev/null but exit status not)
After:  exit 0 (falls through to "no command" branch, same as if command were genuinely absent)
```

**Positive example (REQ-002/AC-004):**
```
Input:  agent_dev_json_escape 'C:\Users\x'
Before: C:\Users\x            (unescaped — embedding in {"v":"..."} produces invalid JSON, confirmed via jq parse error)
After:  C:\\Users\\x          (valid JSON when embedded)
```

**Edge cases:**
- Well-formed dangerous payload (`{"tool_input":{"command":"rm -rf /"}}`) → must still exit `2` (deny) after the REQ-001 fix — this is the regression guard for CON-001.
- jq absent from `PATH` → `agent_dev_json_escape` and `extract_command` both fall back to their bash-only paths; REQ-001's fix (`|| command=""`) is independent of which extraction path ran, so it must protect both.
- Empty `tool_name` (missing key) → `telemetry-capture.sh` already defaults to `"unknown"`; REQ-004's newline-stripping must not affect this default path.
- Multiple consecutive `&&`/`;`/`|` operators (e.g. `a && && b`) → segment splitter already skips empty trimmed segments (existing behavior); REQ-005's cleanup must not change this.
