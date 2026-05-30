---
name: hook-development
description: |
  Claude Code's event system for intercepting and shaping agent behavior at lifecycle points.
  Use when designing PreToolUse guards, PostToolUse formatters, SessionStart context loaders,
  Stop validators, or any hook-driven automation. Trigger on: "add a hook", "block this tool",
  "auto-format on save", "run tests before stop", "intercept file writes", or any mention of
  hooks.json. Key mindset: every hook adds latency — only hook when the risk reduction is worth it.
disable-model-invocation: false
---

# Hook Development for Claude Code Plugins

Claude Code hooks are a powerful event system that allows you to intercept and control the agent's behavior at key lifecycle points.

## Core Mindset

1. **Hooks are a Latency Tax.** Every hook adds 50–200ms. Is the risk reduction worth the wait?
2. **Deterministic > Semantic.** Prefer fast Command hooks for simple rules; use Prompt hooks only for reasoning.
3. **Fail Securely.** If a hook fails or hangs, it should fail in a way that doesn't compromise system integrity.
4. **No Hot-Reload.** You MUST restart Claude Code (`ctrl+c` and restart) to load changes to `hooks.json`.

---

## Hook Lifecycle Events

**MANDATORY — READ ENTIRE FILE**: For technical schemas and expected JSON formats, read [`references/schemas.md`](references/schemas.md).

| Cadence              | Event                | Purpose                                                    |
| :------------------- | :------------------- | :--------------------------------------------------------- |
| **Once per Session** | `SessionStart`       | Load context, set env vars. Fires on resume/compact.       |
|                      | `SessionEnd`         | Cleanup temporary files/connections.                       |
| **Once per Turn**    | `UserPromptSubmit`   | Validate or transform user input before Claude sees it.    |
|                      | `Stop`               | Validate completeness (e.g., run tests) before finishing.  |
|                      | `StopFailure`        | React to interrupted or failed turns.                      |
| **Every Tool Call**  | `PreToolUse`         | **Workhorse.** Block or modify operations before they run. |
|                      | `PostToolUse`        | Post-processing (formatting, logging) after success.       |
|                      | `PostToolUseFailure` | Handle tool errors or suggest fixes.                       |
|                      | `PermissionRequest`  | Auto-approve or custom-gate permission dialogs.            |

---

## Thinking Framework: Should I Hook?

**MANDATORY — READ ENTIRE FILE**: Before designing any hook architecture, read the decision trees in [`references/best-practices.md`](references/best-practices.md).

### The ROI Filter

- Is it **Deterministic** and **Fast** (< 5ms)? → Use **Command Hook**.
- Is it **Semantic** and worth **200ms**? → Use **Prompt Hook**.
- Can it be done **In-Tool** (let Claude fix errors)? → **Don't hook**.

### The NEVER List (Summary)

- **NEVER** hook file writes to validate syntax (Claude can fix it in-tool).
- **NEVER** assume hooks see each other (they run in parallel).
- **NEVER** use `eval` on tool inputs (security risk).
- **NEVER** use hardcoded absolute paths (use `${CLAUDE_PLUGIN_ROOT}`).
- **NEVER** configure a hook that prompts the user or blocks execution — `-p` and `/loop` flows run headless; interactive prompts silently stall automation.
- **NEVER** write a blocking hook when a non-blocking one solves it; prefer exit-0 (allow) or exit-2 (block) patterns over prompt hooks for deterministic rules.

---

## Hook Implementation Workflow

1. **Draft in settings** — Test in `~/.claude/settings.json` first.
2. **Choose Type**:
   - `command`: Local script/binary. Exit 0 to allow, exit 2 to block.
   - `prompt`: Single-turn LLM judgment call.
   - `http`: POST request to external API.
   - `mcp_tool`: Call a tool from a connected MCP server.
3. **Verify Output** — Ensure scripts output valid JSON on `stdout`.
4. **Audit & Lint** — Use the utility scripts in `scripts/`.

---

## Proven Patterns

**MANDATORY — READ ENTIRE FILE**: For implementation examples, read [`references/patterns.md`](references/patterns.md).

- **Pattern 1-2**: Security & Test Enforcement.
- **Pattern 3-4**: Context Loading & Auto-Formatting.
- **Pattern 9**: Staged Validation (Hybrid Command + Prompt for performance).
- **Pattern 10**: Opt-in hooks using flag files.

---

## Debugging

- Run with `claude --debug` to see hook input/output.
- Use `jq .` to validate script output format.
- Use `scripts/test-hook.sh` to isolate script logic from Claude Code.
