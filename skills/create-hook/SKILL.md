---
name: create-hook
description: "Design, write, test Claude Code hooks. Trigger on 'add hook', 'block tool', 'auto-format', 'run tests', 'inject context'. Also: hook types, lifecycle events, debugging non-firing hooks."
disable-model-invocation: false
argument-hint: '[what the hook should guarantee]'
---

# Create Hook

A hook trades latency and complexity for a **guarantee**: an action that happens every time, deterministically, instead of relying on the model to choose it. Engineer every hook by working through seven decisions, then test it before shipping.

**Core mindset:** every hook adds latency to its event and is a maintenance liability. Only add one when the deterministic guarantee is worth more than the cost. If judgment is needed rather than a fixed rule, reach for a `prompt`/`agent` hook or a skill instead.

---

## Step 0 — Decide whether a hook is even the right tool

| Need                                                                               | Use                                      |
| :--------------------------------------------------------------------------------- | :--------------------------------------- |
| An action must **always** happen at a lifecycle point (format, block, log, inject) | **Hook**                                 |
| A decision needs **judgment**, not a fixed rule                                    | `type: "prompt"` or `type: "agent"` hook |
| Give the model _instructions/capabilities_ it invokes when relevant                | **Skill**, not a hook                    |
| A one-off action right now                                                         | Just do it — no hook                     |
| Inject the same context on _every_ session                                         | `CLAUDE.md`, not a `SessionStart` hook   |

If a hook is still the answer, walk the seven decisions below.

---

## The seven decisions

1. **Name the guarantee** — one sentence: "Every time X happens, Y must happen." If you can't state it, stop.
2. **Pick the event** — _when_ must Y fire? → [references/events.md](references/events.md)
3. **Pick the handler type** — `command` (default), `http`, `prompt`, or `agent`. → [Handler types](#3--pick-the-handler-type)
4. **Pick the matcher (+ `if`)** — _which_ occurrences? → [Matchers and `if`](#4--narrow-with-matcher-and-if)
5. **Pick the scope** — who gets this hook? → [Location](#5--pick-the-location-scope)
6. **Write the handler** — honor the I/O contract. → [I/O contract](#6--write-the-handler-the-io-contract)
7. **Test before shipping** — pipe sample JSON, check exit code + output. → [Test](#7--test-before-shipping)

---

## 1 — Name the guarantee

Write it as `When <trigger>, <action> must <happen>`. Examples:

- "When Claude edits a `.ts` file, Prettier must format it."
- "When Claude runs `rm -rf`, the command must be blocked with a reason."
- "When a session resumes, recent git log must be injected into context."

This sentence determines the event (the _when_), the matcher (the _which_), and whether the hook must **block** (the _must_).

---

## 2 — Pick the event

Choose the lifecycle point from the _when_. The most common:

| Goal                                                      | Event                              | Can block?          | Output schema shortcut                                                             |
| :-------------------------------------------------------- | :--------------------------------- | :------------------ | :--------------------------------------------------------------------------------- |
| Guard / block a tool call before it runs                  | `PreToolUse`                       | Yes                 | exit 2 + stderr, or `hookSpecificOutput.permissionDecision` (allow/deny/ask/defer) |
| React after a tool **actually ran** (format, lint, log)   | `PostToolUse`                      | No (already ran)    | `decision: "block"` + `reason` to feed back to Claude                              |
| Inject context / env at session begin or resume           | `SessionStart`                     | No                  | plain stdout on exit 0 becomes context automatically                               |
| Validate or add context to a prompt before Claude sees it | `UserPromptSubmit`                 | Yes                 | plain stdout on exit 0 becomes context; exit 2 erases prompt                       |
| Force Claude to keep working until a condition holds      | `Stop`                             | Yes                 | exit 2 + stderr reason; **check `stop_hook_active` first**                         |
| Auto-answer or modify a permission dialog                 | `PermissionRequest`                | Yes                 | `hookSpecificOutput.decision.behavior` (allow/deny)                                |
| Desktop notification when Claude needs input              | `Notification`                     | No                  | side effects only                                                                  |
| Re-inject context after compaction                        | `SessionStart` (matcher `compact`) | No                  | plain stdout on exit 0 becomes context automatically                               |
| Audit/guard config edits                                  | `ConfigChange`                     | Yes (except policy) | `decision: "block"` + `reason`                                                     |

**Timing rule:** Use `PreToolUse` to block or modify before execution. Use `PostToolUse` to react to commands that _actually ran_ — `PreToolUse` fires even for commands later blocked by other hooks, so audit logs and formatters belong on `PostToolUse`.

**The full table of ~30 events, their input fields, output schemas, and exit-code-2 behavior lives in [references/events.md](references/events.md). Read it before committing to an event** — pick the one whose timing and blocking ability match the guarantee.

**Coverage trap:** `PreToolUse`/`PostToolUse` on `Edit|Write` does **not** catch files changed via `Bash` (e.g. `sed`, `>`). For compliance scanning, add a `Stop` hook that scans the working tree once per turn, or also match `Bash`.

**Context injection:** For `SessionStart` and `UserPromptSubmit`, plain stdout on exit 0 is automatically appended to Claude's context — no JSON required. This is the primary mechanism for injecting dynamic content (git log, env state, etc.). For `SessionStart`, prefer a hook over `CLAUDE.md` only when the content changes between sessions; static instructions belong in `CLAUDE.md`.

---

## 3 — Pick the handler type

| Type      | Use when                                                 | Notes                                                          |
| :-------- | :------------------------------------------------------- | :------------------------------------------------------------- |
| `command` | Default. A shell command/script decides.                 | stdin = JSON, stdout/stderr + exit code = decision.            |
| `http`    | A web service should handle the logic.                   | POSTs event JSON; must return 2xx + JSON to block.             |
| `prompt`  | The decision needs **judgment** but only the hook input. | Single fast-model call returns `{"ok": bool, "reason": str}`.  |
| `agent`   | Judgment that must **inspect files/run commands**.       | Spawns a subagent (Read/Grep/Glob). Experimental; 60s default. |

Default to `command`. Reach for `prompt`/`agent` only when a deterministic rule genuinely can't express the check (e.g. "are all the user's tasks actually done?").

**Fire-and-forget side effects** (logging, notifications, metrics) should set `"async": true` on the hook. This runs the command in the background so it adds zero latency to the event's hot path. Never use `async` when the hook needs to block or return a decision.

**NEVER set `"async": true` on a hook that must block, deny, or return a decision.** Async hooks cannot influence the tool's execution — their exit code and stdout are discarded. A hook that sets `"async": true` and then exits `2` to block a command will silently fail to block it. Only use `async` for pure side effects (logging, notifications) where the outcome doesn't matter.

`prompt`/`agent` are supported only on: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `Stop`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `UserPromptSubmit`.

---

## 4 — Narrow with matcher and `if`

- **`matcher`** filters at the group level. For tool events it matches the **tool name** (regex): `Bash`, `Edit|Write`, `mcp__github__.*`. For other events it matches that event's field (e.g. `SessionStart` → `startup|resume`, `compact`). Empty/absent = fire on every occurrence. Matchers are **case-sensitive**.
- **`if`** (Claude Code v2.1.85+) filters by tool name **and arguments** using permission-rule syntax, so the hook process only spawns on a real match: `"if": "Bash(git *)"`, `"if": "Edit(*.ts)"`. Tool events only. **Use `if` to restrict by file extension at the config level** — this prevents the hook process from spawning for non-matching files entirely, which is faster and cleaner than a script-level check. Example: `"if": "Edit(*.ts) | Write(*.ts)"` restricts a Prettier hook to TypeScript files without needing any extension check inside the script.

MCP tools are named `mcp__<server>__<tool>`. Match a whole server with `mcp__memory__.*`.

Keep matchers as **narrow** as the guarantee allows — especially for `PermissionRequest` auto-approval, where a broad matcher silently approves everything.

Full matcher value tables per event: [references/events.md](references/events.md).

---

## 5 — Pick the location (scope)

| File                          | Scope                  | Committed         |
| :---------------------------- | :--------------------- | :---------------- |
| `~/.claude/settings.json`     | All your projects      | No (your machine) |
| `.claude/settings.json`       | This project, the team | Yes               |
| `.claude/settings.local.json` | This project, you only | No (gitignored)   |
| Plugin `hooks/hooks.json`     | When plugin enabled    | Yes               |
| Skill / agent frontmatter     | While component active | Yes               |

Match scope to intent: a personal notification → user settings; a team guardrail → project settings (committed); a secret-bearing audit hook → local settings.

**Config shape** — the `hooks` object keys events; never replace the whole object, add your event as a sibling:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

Reference bundled scripts with `"$CLAUDE_PROJECT_DIR"` (settings) or `${CLAUDE_PLUGIN_ROOT}` (plugins) — never relative paths.

---

## 6 — Write the handler (the I/O contract)

A command hook reads **JSON on stdin**, does its work, and signals the outcome via **exit code** or **stdout JSON**. Pick one signalling style — never both.

### Exit codes (simple block / allow)

| Code  | Meaning                                                                                                      |
| :---- | :----------------------------------------------------------------------------------------------------------- |
| `0`   | No objection. stdout becomes context for `UserPromptSubmit`/`SessionStart`; otherwise shown only in verbose. |
| `2`   | **Block.** stderr is fed to Claude as feedback. (Non-blockable events just show stderr to the user.)         |
| other | Non-blocking error; action proceeds, stderr in debug log.                                                    |

Exit-2 behavior is **per event** — `PreToolUse` blocks the tool, `UserPromptSubmit` erases the prompt, `Stop` prevents stopping, `SessionStart` can't block. Confirm in [references/events.md](references/events.md).

### Structured JSON (richer control)

Exit `0` and print JSON to stdout. Universal fields: `continue` (false = Claude stops entirely), `systemMessage`, `suppressOutput`. Event-specific decision shapes:

- `PreToolUse`: `hookSpecificOutput.permissionDecision` = `allow`/`deny`/`ask`, plus `permissionDecisionReason`, optional `updatedInput`.
- `PostToolUse`/`Stop`/`UserPromptSubmit`/`ConfigChange`: top-level `decision: "block"` + `reason`.
- `PermissionRequest`: `hookSpecificOutput.decision.behavior` = `allow`/`deny`.
- `UserPromptSubmit`/`SessionStart`: `hookSpecificOutput.additionalContext` to inject text.

> Do not mix: if you exit `2`, stdout JSON is ignored. `"allow"` skips the prompt but **cannot** override a deny rule from settings — hooks tighten, never loosen.

### Handler template (bash)

```bash
#!/usr/bin/env bash
# Reads hook JSON on stdin, blocks on a condition.
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *".env"* ]]; then
  echo "Blocked: $FILE_PATH is protected" >&2   # stderr = feedback to Claude
  exit 2                                          # exit 2 = block
fi
exit 0
```

### Handler template (PowerShell — set `"shell": "powershell"`)

```powershell
$raw = [Console]::In.ReadToEnd()
$input = $raw | ConvertFrom-Json
if ($input.tool_input.file_path -like "*.env*") {
    [Console]::Error.WriteLine("Blocked: protected file")
    exit 2
}
exit 0
```

### Authoring checklist

- [ ] Read **all** of stdin (`$(cat)` / `ReadToEnd()`) before parsing — partial reads corrupt JSON.
- [ ] Use `// empty` (jq) / null-guards; fields are event-specific and may be absent.
- [ ] Keep **stdout clean** for JSON; send logs/diagnostics to **stderr**.
- [ ] Make scripts executable: `chmod +x` (macOS/Linux). Reference via `$CLAUDE_PROJECT_DIR`.
- [ ] **`Stop`/`SubagentStop` handlers: read `stop_hook_active` from stdin and `exit 0` immediately when it is `true`** — skipping this causes an infinite loop. The block cap fires after 8 consecutive blocks; raise it with `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`.
- [ ] Set a sensible `timeout` (seconds); command default is 600, `UserPromptSubmit` caps at 30. Stop hooks running test suites should set a realistic timeout (e.g. 120).
- [ ] **Define a Timeout Fallback (Dead-Letter):** When a hook script invokes an external process or subagent that might timeout or fail, the script MUST implement a graceful fallback (e.g., return a safe default, log to a dead-letter file, or use shallow heuristics) instead of causing the hook to crash or hang the workflow.
- [ ] If a profile prints to stdout for non-interactive shells, guard it (`[[ $- == *i* ]]`) — it corrupts hook JSON.
- [ ] PowerShell handlers require `"shell": "powershell"` in the hook config — without it the command runs under bash/sh and will fail.
- [ ] Fire-and-forget hooks (logging, notifications) should set `"async": true` to avoid adding latency.

Env vars available: `$CLAUDE_PROJECT_DIR` (all hooks), `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_PLUGIN_DATA}` (plugins), `$CLAUDE_ENV_FILE` (`SessionStart`/`CwdChanged`/`FileChanged` — write `export KEY=val` to persist into Bash).

---

### After Creation

1. Test the hook manually using the provided test command.
2. Run project-specific validation (e.g., `npm run test:node`).
3. **Invoke `verification-before-completion`** to ensure the new hook doesn't break existing workflows or introduce latency issues.

When you produce a hook for the user, always give all three:

1. **The settings JSON block** — ready to paste, with the correct event/matcher/scope.
2. **The handler script** (if `command` type) — complete, no placeholders, executable.
3. **One test command** — sample stdin proving it blocks/allows correctly.

State which settings file it goes in and any `chmod`/`jq` prerequisite.

### Quick reference — correct JSON output by event

The required output schema differs by event. Use the right one or the hook is silently ignored:

| Event                                                     | Correct output to stdout                                                                                                                                    |
| :-------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PreToolUse` (block)                                      | exit 2 + `stderr` message, OR exit 0 + `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}` |
| `PreToolUse` (allow, skip prompt)                         | exit 0 + `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}`                                                               |
| `PostToolUse`, `Stop`, `UserPromptSubmit`, `ConfigChange` | exit 0 + `{"decision":"block","reason":"..."}` — or exit 2 + stderr                                                                                         |
| `PermissionRequest` (allow)                               | exit 0 + `{"hookSpecificOutput":{"hookEventName":"PermissionRequest","decision":{"behavior":"allow"}}}`                                                     |
| `PermissionRequest` (deny)                                | exit 0 + `{"hookSpecificOutput":{"hookEventName":"PermissionRequest","decision":{"behavior":"deny","message":"..."}}}`                                      |
| `SessionStart`, `UserPromptSubmit` (inject context)       | exit 0, plain stdout — automatically appended to Claude's context                                                                                           |

**PermissionRequest example** (auto-approve ExitPlanMode):

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PermissionRequest\",\"decision\":{\"behavior\":\"allow\"}}}'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Test: `echo '{"tool_name":"ExitPlanMode","tool_input":{}}' | bash -c "echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PermissionRequest\",\"decision\":{\"behavior\":\"allow\"}}}'"`

Security: `PermissionRequest` with an empty or `.*` matcher silently auto-approves every permission dialog including writes and shell commands. Always name the exact tool. This event does **not** fire in `-p` (headless) mode — use `PreToolUse` there.

## Reference map

- [references/events.md](references/events.md) — full event catalog: every event's input fields, output schema, matcher values, and exit-code-2 behavior. **Read before picking an event.**
- [references/recipes.md](references/recipes.md) — ready-to-use patterns (format-on-save, block files, notify, context injection, audit, auto-approve), debugging, and security considerations.
- [scripts/test_hook.py](scripts/test_hook.py) — local test harness: pipes sample JSON to a hook, reports exit code and parsed output.

---

## Command Usage & Troubleshooting Guidelines

### Usage Scenarios

- **Check Hook Wiring** (`check`): Run when hook behavior seems silently broken or after modifying a hook configuration/wiring in `hooks/hooks.json` to ensure everything is wired correctly.
- **Scaffold New Hook** (`new <hook-name>`): Scaffolding a handler for a new hook event (e.g. `PreToolUse`, `PostToolUse`, `Stop`, etc.).
- **Fix Hook Handler** (`fix <handler-file>`): When a specific handler throws errors, does not fire, or produces incorrect output.

### Hook Workflow Steps in `agent-dev`

1. **Check Workflow**:
   - Read `hooks/hooks.json` and verify every handler path exists.
   - Run the hook unit tests (`npm run test:node`) to verify wiring.
   - Report any missing handlers or wiring mismatches.
2. **New Hook Workflow**:
   - Scaffold a new handler under `hooks/handlers/` using the ESM pattern.
   - Register the handler under the appropriate event list in `hooks/hooks.json`.
3. **Fix Hook Workflow**:
   - Diagnose the issue in the handler. Fix import errors, syntax bugs, or invalid return schemas.
   - Re-run `npm run test:node` to verify.

### Troubleshooting

- **Wiring passes but hooks don't fire** — Verify the hook event name in `hooks.json` matches the Claude Code event name exactly (case-sensitive).
- **Handler is created but never runs** — Ensure the handler is correctly registered in `hooks.json` under the active event name.
- **Dynamic import error** — Path in `hooks.json` is wrong. Path must be relative to `runner.mjs`, not the project root.
- **Success Criteria** — All hook handlers exist, no wiring gaps exist in `hooks.json`, repaired handlers pass tests, and all unit tests run cleanly.
