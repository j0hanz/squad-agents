# Common Hook Patterns

This reference provides common, proven patterns for implementing Claude Code hooks. Use these patterns as starting points for typical hook use cases.

## Pattern 1: Security Validation (PreToolUse)

Block dangerous file writes or commands using prompt-based hooks.

```json
{
  "PreToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "prompt",
          "prompt": "File path: $TOOL_INPUT.file_path. Verify: 1) Not in system directories 2) Not credentials 3) No '..' traversal. Return 'approve' or 'deny'."
        }
      ]
    }
  ]
}
```

## Pattern 2: Test Enforcement (Stop)

Ensure tests run before Claude claims a task is done.

```json
{
  "Stop": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "prompt",
          "prompt": "If code was modified, verify tests were executed. If not, block with reason 'Tests must be run after changes'."
        }
      ]
    }
  ]
}
```

## Pattern 3: Context Loading (SessionStart)

Detect project type and load environment details once per session.

```json
{
  "SessionStart": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/load-context.sh"
        }
      ]
    }
  ]
}
```

## Pattern 4: Auto-Formatting (PostToolUse)

Automatically run formatters after Claude edits a file.

```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "npx prettier --write ${CLAUDE_PROJECT_DIR}/${TOOL_INPUT.file_path}"
        }
      ]
    }
  ]
}
```

## Pattern 5: Destructive Operation Guard (mcp_tool)

Use a specialized MCP tool to validate or backup data before deletion.

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "mcp_tool",
          "server": "my-security-server",
          "tool": "validate-command",
          "arguments": { "command": "$TOOL_INPUT.command" }
        }
      ]
    }
  ]
}
```

## Pattern 6: Webhook Integration (HTTP)

Send audit logs to an external security monitoring system.

```json
{
  "PreToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "http",
          "url": "https://audit.internal.com/log",
          "method": "POST"
        }
      ]
    }
  ]
}
```

## Pattern 7: Session Cleanup (SessionEnd)

Clean up temporary files or close connections when the session finishes.

```json
{
  "SessionEnd": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "rm -rf /tmp/claude-session-$$"
        }
      ]
    }
  ]
}
```

## Pattern 8: Auto-Approve Permissions (PermissionRequest)

Silently approve specific permissions (e.g., in a trusted environment).

```json
{
  "PermissionRequest": [
    {
      "matcher": "BashExecution",
      "hooks": [
        {
          "type": "command",
          "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/check-trust.sh"
        }
      ]
    }
  ]
}
```

## Pattern 9: Staged Validation (Hybrid)

**Stage 1 (Command, 5ms):** Quick allowlist for safe operations.
**Stage 2 (Prompt, 150ms):** Deep reasoning for everything else.

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/allowlist.sh",
          "timeout": 5
        },
        {
          "type": "prompt",
          "prompt": "Analyze bash for security risks.",
          "timeout": 15
        }
      ]
    }
  ]
}
```

## Pattern 10: Temporarily Active Hooks (Flag Files)

Only run the hook if a specific flag file exists in the project root.

```bash
#!/bin/bash
if [ ! -f "${CLAUDE_PROJECT_DIR}/.enable-hook" ]; then
  exit 0 # Pass immediately
fi
# ... validation logic ...
```
