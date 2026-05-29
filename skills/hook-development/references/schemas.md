# Hook Event Schemas

This reference provides the JSON structure of data passed to hook scripts via `stdin` and the expected output formats.

## Global Context

Every hook event includes these top-level fields:

| Field        | Type     | Description                                                     |
| :----------- | :------- | :-------------------------------------------------------------- |
| `event`      | `string` | The event name (e.g., `PreToolUse`)                             |
| `tool_name`  | `string` | The tool being called (only for tool-related events)            |
| `tool_input` | `object` | The arguments passed to the tool (only for tool-related events) |

## Event-Specific Input Schemas

### Every Tool Call Cadence

#### `PreToolUse`

Fires before a tool executes.

```json
{
  "event": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf /"
  }
}
```

#### `PostToolUse`

Fires after a tool succeeds.

```json
{
  "event": "PostToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "index.js", "content": "..." },
  "tool_result": "File written successfully"
}
```

#### `PostToolUseFailure`

Fires after a tool call fails.

```json
{
  "event": "PostToolUseFailure",
  "tool_name": "Bash",
  "tool_input": { "command": "npm test" },
  "error": "Error: Tests failed with exit code 1"
}
```

#### `PermissionRequest`

Fires when a permission dialog appears.

```json
{
  "event": "PermissionRequest",
  "permission": "BashExecution",
  "command": "docker run ..."
}
```

### Once per Turn Cadence

#### `UserPromptSubmit`

Fires before Claude processes a user's prompt.

```json
{
  "event": "UserPromptSubmit",
  "prompt": "Fix all bugs in this project"
}
```

#### `Stop`

Fires when Claude finishes responding (the "last word").

```json
{
  "event": "Stop",
  "transcript": "...",
  "final_response": "I have fixed the bugs."
}
```

#### `StopFailure`

Fires when a response fails to complete.

```json
{
  "event": "StopFailure",
  "reason": "Context window exceeded"
}
```

### Once per Session Cadence

#### `SessionStart`

Fires when a session begins, resumes, or is compacted.

```json
{
  "event": "SessionStart",
  "is_resume": false,
  "is_compact": false
}
```

#### `SessionEnd`

Fires when a session is closed.

```json
{
  "event": "SessionEnd"
}
```

---

## Expected Output Format

Hooks communicate back via `stdout`.

### Command Hooks (Decision)

Expected JSON on `stdout`. Use exit code 2 to block.

```json
{
  "decision": "approve" | "deny" | "ask",
  "reason": "Short message shown to Claude if denied"
}
```

### Prompt Hooks

Prompt hooks return a string ("approve", "deny", or a message). Claude parses the last line of its own response to find the decision.

### Permission Hooks

Can return `{"decision": "approve"}` to auto-approve permissions.

---

## Environment Variables

Available to all hook scripts:

- `CLAUDE_PROJECT_DIR`: The root directory of the current project.
- `CLAUDE_PLUGIN_ROOT`: The root directory where the plugin is installed.
- `CLAUDE_ENV_FILE`: Path to a temporary file. Append `export VAR=val` here to persist environment variables for the session.
- `CLAUDE_TRANSCRIPT_PATH`: Path to a temporary file containing the current session transcript.
