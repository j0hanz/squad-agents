# Hook Behaviors — What Fires Automatically

You do not invoke these — they fire on lifecycle events:

| Trigger                       | What happens                                                       |
| ----------------------------- | ------------------------------------------------------------------ |
| Session start                 | Context injected; skill list announced; explorer state initialized |
| `UserPromptSubmit`            | Brainstorm-nudge suggests invoking `brainstorming` skill           |
| `PostToolUse` (Edit/Write)    | Auto-format via ESLint/Prettier (JS) or Ruff (Python)              |
| `PostToolUseFailure` (Bash)   | Diagnose-nudge surfaces `diagnose` skill and `@detective` agent    |
| `PreToolUse` (Grep/Glob/Read) | Explorer pre-fetches and enriches context                          |
| `Stop`                        | Debug artifact scan; explorer state flushed                        |
