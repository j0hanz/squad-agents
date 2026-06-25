# Context Pruning & Formatting Guidelines

This reference guide contains the specifications for reducing token usage and preserving context window capacity in Claude Code.

## 1. The Markdown-KV Pattern

Use Markdown-KV to format lists of facts, settings, or checklist items. Every entry must be a single-line `key: value` pair.

### Anti-Pattern (Verbose JSON / Nested Markdown)

```json
{
  "related_files": [
    {
      "path": "src/auth/login.py",
      "test_coverage": true,
      "last_changed": "2 days ago"
    }
  ],
  "status": "in-progress"
}
```

### Good Pattern (Flat Markdown-KV)

```markdown
related_files_0_path: src/auth/login.py
related_files_0_test_coverage: true
related_files_0_last_changed: 2 days ago
status: in-progress
```

- **Benefit**: Saves parsing tokens (braces, brackets, double quotes) and prevents multi-line indentation bloat.

## 2. Log Truncation Specifications

When presenting command failures, test traces, or stack traces:

- Capture the invocation command and its exit status.
- Extract the lines matching standard error patterns (e.g. `Traceback`, `Exception`, `FAIL`, `Error`).
- Retain 2 lines of context before the error and up to 8 lines after.
- Omit the middle of successful test outputs.

Example output:

```text
$ npm test
Status: FAIL
... [omitted 120 lines of successful suite initialization] ...
FAIL src/auth.test.js
  ✕ should reject invalid credentials (12ms)
    at Object.test (src/auth.test.js:42:15)
    Error: Expected 'Authenticated' but got 'Access Denied'
... [omitted 45 lines of passing tests] ...
```

## 3. The Rolling Summary Pattern

Maintain project memory across `/clear` boundary resets using `.claude/rolling_summary.md`.

Format:

```markdown
# Rolling Task Summary

## Current Session State

timestamp: 2026-06-23T23:18:04+02:00
current_skill: multi-agent-development
done: fixed null pointer in auth.py, updated tests
blocking: None
next: implement rate limiting middleware
key_decisions: using sliding window rate limiter at Redis level

## Past Sessions (Collapsed)

- 2026-06-22: Scaffolding API routes (Completed)
- 2026-06-21: Database design and migrations (Completed)
```

By collapsing older sessions into single-line lists, we retain historical context without sending hundreds of lines of conversation history.

`current_skill` records which skill/gate was active at `/clear` time, so resume re-enters that skill directly instead of re-deriving the route from `using-agent-sdlc-skills` Gate 0.
