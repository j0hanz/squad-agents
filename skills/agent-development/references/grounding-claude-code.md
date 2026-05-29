# Claude Code Agents Grounding

## Authoritative Sources

- Claude API Reference (https://docs.anthropic.com)
- Claude Code Agent Tool (for subagent spawning mechanics)
- Hooks API Reference (for event types and lifecycle)
- Claude Code Permission Rules (for tool-permission syntax)

## Claude Code Subagent Frontmatter Spec

| Field | Type | Required? | Description |
|-------|------|-----------|-------------|
| name | string | yes | Unique subagent identifier in lowercase with hyphens |
| description | string | yes | Trigger phrase and purpose for invocation (40-80 chars) |
| model | string | optional | Model override; defaults to parent session model (claude-opus-4-1, claude-sonnet-4-20250514, etc.) |
| tools | array of strings | optional | Tool allowlist; additive to parent permissions (never restrictive) |

### Minimal Subagent Example

```yaml
name: code-formatter
description: Format and beautify code according to style standards
```

### Subagent with Tool Allowlist Example

```yaml
name: typescript-auditor
description: Audit TypeScript code for type safety and best practices
model: claude-opus-4-1
tools:
  - Bash
  - Read
  - Grep
  - Skill
```

**Note:** The `tools` array is additive only. Subagent tools inherit parent permissions plus listed tools. Tool allowlist cannot restrict parent permissions.

## The Agent Tool (how Claude spawns subagents)

Claude Code spawns subagents via the Agent tool with these key concepts:

**Subagent Types:**
- `general-purpose`: Generic agent; requires full context re-derivation
- `code-reviewer`: Specialized for code review and feedback
- `debugger`: Specialized for bug investigation and fixing
- `refactoring-specialist`: Specialized for refactoring and architecture improvements
- `typescript-pro`: Specialized for TypeScript analysis and improvements
- `documentation-engineer`: Specialized for documentation creation and updates
- `security-auditor`: Specialized for security analysis

**Core Parameters:**
- `subagent_type`: Determines pre-loaded skills and tool set
- `prompt`: Task description passed to the subagent; must be self-contained
- `description`: Short summary for logging and audit trails
- `isolation_mode`: `worktree` (git-safe isolation), `sandbox` (process isolation), `none` (shared context)

**Critical Notes:**
- `subagent_type` determines which skills and tools are pre-loaded automatically
- `general-purpose` agents require full context re-derivation from scratch (avoid when context matters)
- Typed agents (code-reviewer, debugger, etc.) are context-aware and preferred
- Task isolation protects parent session from subagent side effects

## Permission Rule Syntax (canonical)

| Pattern | Applies To | Syntax |
|---------|-----------|--------|
| Bash(pattern) | Bash, Monitor | `Bash(find .* -name *.js)` |
| PowerShell(pattern) | PowerShell | `PowerShell(Get-ChildItem -Include *.cs)` |
| Read(glob-pattern) | Read, Grep, Glob, LSP | `Read(src/**/*.ts)` |
| Edit(glob-pattern) | Edit, Write, NotebookEdit | `Edit(docs/**/*.md)` |
| Skill(name) | Skill | `Skill(typescript-best-practices)` |
| Agent(subagent_type) | Agent | `Agent(code-reviewer)` |
| WebFetch(domain:example.com) | WebFetch | `WebFetch(domain:github.com)` |
| WebSearch | WebSearch | `WebSearch` |

**Permission Scoping Rules:**
- Glob patterns support `*`, `**`, and character ranges
- Domain filters in WebFetch support wildcards: `domain:*.github.com`
- Bash/PowerShell patterns match command arguments via regex
- Deny rules override allow rules

## Hook Lifecycle High-Level

Claude Code hooks organize into 4 lifecycle classes:

**1. Per-Session Hooks**
- `SessionStart`: Fires once when session begins; initialize global state or environment

**2. Per-Turn Hooks**
- `PreInput`: Before user input is processed
- `PostCompact`: After context compaction (memory consolidation)
- `PreToolUse`: Before any tool executes
- `PostToolUse`: After any tool completes

**3. Per-Tool Hooks**
- Tool-specific handlers (e.g., `hooks.bash`, `hooks.read`)
- Can observe, defer (non-interactive mode only), or deny tool execution
- Run before tool invocation (gates execution)

**4. Advanced Hooks**
- `SubagentStart`: Before subagent spawns
- `SubagentStop`: After subagent completes
- `TeamCreate`: Parent creates agent team
- `Elicitation`: Prompt user for decisions (interactive only)

**Hook Handler Types and Decision Semantics:**
- `command` (shell): Execute shell script; exit code determines action
  - Exit 0: approve tool use or continue
  - Exit 1: deny tool use or stop
  - Exit 2: defer (non-interactive mode only; blocked in web)
- `prompt` (decision): Ask user for approval (interactive mode only; blocked in -p)

Refer to the `hook-development` skill for deep design guidance, hook performance tuning, and advanced patterns.

## Agent Teams Essentials

Agent teams enable parallel task execution and hierarchical workflows:

**Team Lifecycle Events:**

| Event | Fired When | Typical Use |
|-------|-----------|------------|
| `TeamCreate` | Parent spawns a new team | Initialize team context or validate team composition |
| `TaskCreated` | Parent adds task to queue | Prepare task-specific resources or validate task |
| `TeammateIdle` | Teammate finishes its task | Reassign teammate or aggregate results |
| `TaskCompleted` | Task finished successfully or failed | Process task results or trigger cleanup |

**CLI Flags:**
- `--bg` or `--background`: Spawn agents in background; parent continues without blocking
- Without flag: Parent waits for agent completion (blocking mode)

**Transcript Access:**
- Team member transcripts available in `SubagentStop` hook after completion
- Parent can parse transcript for results, errors, or context drift
- Enables post-processing and result validation workflows

## Common Pitfalls

1. **Tool Defer in Interactive Mode**
   - Tool defer (exit code 2) is non-interactive only; blocked in web UI
   - Hooks attempting defer in interactive mode fail silently or raise errors
   - Always check execution mode before using defer

2. **general-purpose Agent Context Loss**
   - `general-purpose` subagents re-derive context from scratch (expensive, error-prone)
   - Use typed agents (code-reviewer, debugger, typescript-pro) when context matters
   - Typed agents inherit parent context automatically

3. **User-Prompting Hooks Break Headless Mode**
   - Hooks that call `Elicitation` or prompt user break automation (-p mode)
   - Headless mode (-p) cannot process interactive prompts; hooks block or fail
   - Use decision hooks (shell commands with exit codes) for automation

4. **Missing agent_type in Main Session**
   - Main session tool calls lack `agent_type` (not applicable to parent)
   - Subagent tool requires `subagent_type` (default: `general-purpose`)
   - Forgetting to set `subagent_type` causes context loss; always specify

5. **Skill Pinning Without Version Control**
   - Skills auto-update without explicit version pins (flaky in production)
   - Pin skill versions in CLAUDE.md or settings.json for reproducibility
   - Unversioned skills cause non-deterministic behavior across sessions

6. **Overly Broad Permission Patterns**
   - Patterns like `Bash(.*)`  or `Read(**)` are too broad; invite future vulnerabilities
   - Use specific glob patterns: `Read(src/**/*.ts)` not `Read(src/**/*)`
   - Narrow patterns reduce blast radius and improve auditing

---

**Last Updated:** 2026-05-19
**Audience:** Claude Code agent developers and skill authors
