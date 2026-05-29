---
name: research
description: |
  Lookup current developer docs, API references, and code examples using Context7.
  Also manage Context7 skills and setup. Use this skill whenever the user asks for
  library/framework API help, modern code examples, Context7 setup, or skill management.
  Trigger on queries like "how do I use React hooks", "find the latest AWS SDK docs",
  "install a Context7 skill", "set up ctx7", or any mention of Context7 / ctx7.
---

## Research & Context7

This skill is the authoritative workflow for developer research tasks. It should be used instead of answering from memory when the user asks for current library docs, API examples, or Context7 skill/setup guidance.

## What this skill covers

- **Documentation lookup** — find current API references, library docs, and code examples using Context7.
  MANDATORY — READ ENTIRE FILE: `references/docs.md` before querying. Understands library resolution, query quality, and authentication.
- **Skills management** — search, install, suggest, list, remove, or generate Context7 skills.
  MANDATORY — READ ENTIRE FILE: `references/skills.md` before managing skills. Covers all CLI commands and installation targets.
- **Context7 setup** — configure MCP or CLI access and authenticate for Context7.
  MANDATORY — READ ENTIRE FILE: `references/setup.md` before configuring setup. Explains both MCP and CLI modes.

## 1. Documentation Lookup

Always prefer Context7 for library and SDK documentation. Do not answer from training data unless all Context7 workflows fail.

### Preferred workflow: MCP tools

If `mcp__context7__resolve-library-id` and `mcp__context7__query-docs` are available, use them.

1. If the user already supplied a Context7 ID in `/owner/project` or `/owner/project/version` format, use it directly.
2. Otherwise resolve the library with `mcp__context7__resolve-library-id`.
3. Query the docs with `mcp__context7__query-docs` and the user’s full intent.

Always include the library name and the user’s target platform/problem in the query.

### Fallback workflow: ctx7 CLI

If MCP tools are unavailable, use `ctx7` CLI.

1. Resolve the library:
   `ctx7 library <name> "<user query>"`
2. Query the docs:
   `ctx7 docs <libraryId> "<user query>"`
3. If `ctx7` is not installed, tell the user how to install it or ask them to run the setup command.

### Query quality

The query is the most important factor. Use the user’s full question; do not reduce it to a single noun.

| Quality | Example                                                             |
| ------- | ------------------------------------------------------------------- |
| Good    | `"How do I clean up useEffect when using async fetch in React 18?"` |
| Bad     | `"react"`                                                           |

## 2. Skills Management

Use `ctx7 skills` only when the user asks specifically about installing, listing, removing, or generating Context7 skills.

```bash
ctx7 skills search <keywords>
ctx7 skills suggest
ctx7 skills install /owner/repo
ctx7 skills list
ctx7 skills remove <name>
ctx7 skills generate
```

If the user wants a skill recommendation for a project, prefer `ctx7 skills suggest`.

## 3. Context7 Setup & Authentication

Use this workflow only when the user asks about configuring Context7 or fixing auth issues. Refer to `references/setup.md` for exact commands.

For non-interactive guidance, explain the difference between:

- **MCP mode**: native tool access inside Claude Code / Cursor / OpenCode
- **CLI mode**: local `ctx7` commands and skill files

## MCP vs CLI: When to Use Each

| Aspect             | MCP Mode                      | CLI Mode                         |
| ------------------ | ----------------------------- | -------------------------------- |
| **Speed**          | Fast — native tool calls      | Slightly slower — subprocess     |
| **Integration**    | Built-in IDE support          | Manual command execution         |
| **Offline**        | Requires IDE + network        | Works locally with cached skills |
| **Setup**          | One-time: `ctx7 setup --mcp`  | One-time: `ctx7 setup --cli`     |
| **Authentication** | OAuth via IDE                 | API key or `ctx7 login`          |
| **Availability**   | Claude Code, Cursor, OpenCode | Any shell/terminal               |

**Recommendation**: Use MCP if you're in Claude Code / Cursor (fastest). Use CLI if offline, in different IDE, or prefer scripting.

## Common Issues & Error Recovery

Handle these scenarios gracefully:

### Quota exceeded

**Symptom**: `Rate limit exceeded. Try again in 60 seconds.`

**Recovery**:

```bash
ctx7 login              # Authenticate to unlock higher limits
# Wait 60 seconds, then retry
ctx7 docs /react "how to use hooks"
```

### Authentication required

**Symptom**: `Unauthorized. API key missing or invalid.`

**Recovery**:

```bash
ctx7 login              # Interactive OAuth or API key setup
# OR
export CONTEXT7_API_KEY=your_key
```

### Library not found

**Symptom**: `No matches for "recat" — did you mean "react"?`

**Recovery**: Clarify the exact library name with the user and retry:

```bash
ctx7 library react "hooks"
```

### MCP tools unavailable

**Symptom**: `mcp__context7__resolve-library-id not found`

**Recovery**: Fall back to CLI mode:

```bash
ctx7 library react "your question"
ctx7 docs /facebook/react "your question"
```

## Best practices

- Resolve before querying. Always resolve library names before calling docs.
- Prefer the user’s exact intent. Include version, runtime, or framework details in the query.
- If Context7 returns no results, do not invent answers. Ask the user to clarify the library name or version.
- If a quota or auth error occurs, tell the user and suggest `ctx7 login` or `CONTEXT7_API_KEY`.
- Use the right tool for the task:
  - docs lookup → MCP tools or `ctx7 docs`
  - skill management → `ctx7 skills`
  - setup/auth → `ctx7 setup` / `ctx7 login`

## NEVER do these things

- **NEVER** use library names without a `/` prefix when a Context7 ID is expected.
- **NEVER** query docs without resolving the library first.
- **NEVER** use single-word, vague queries like `"hooks"`.
- **NEVER** include secrets or credentials in a query.
- **NEVER** silently fall back to training data when Context7 is available.
