# Agent-Hook Patterns

## Overview

Agent-specific hook patterns for implementing cross-cutting concerns: telemetry, behavioral testing, permission enforcement, quality gates, agent persistence, and MCP integration.

---

## Pattern 1: Subagent Telemetry Pipeline [FOUNDATIONAL]

### When to use
When you need visibility into subagent execution: transcripts, tool calls, timing, and error rates.

### Mechanism
- Hook: `SubagentStart` (fires when subagent spawns)
- Hook: `SubagentStop` (fires when subagent completes)
- Two shell command hooks capture start/stop timestamps and task description
- One JSONL writer appends structured events to a log file
- One summary script aggregates metrics post-run

### Template

**hooks.json entry:**
```json
{
  "event": "SubagentStart",
  "type": "command",
  "command": "echo '{ \"event\": \"start\", \"timestamp\": \"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'\", \"subagent_type\": \"'${CLAUDE_CODE_AGENT_TYPE}'\", \"prompt_len\": '$(echo -n \"${CLAUDE_CODE_PROMPT}\" | wc -c)' }' >> .claude/telemetry.jsonl"
}
```

**Aggregation script (summary.py):**
- Reads `.claude/telemetry.jsonl`
- Computes total duration, tool call counts, error rate
- Outputs human-readable summary to stdout

### Pitfall
⚠️ **Field naming:** The hook environment provides `agent_transcript_path` (subagent's isolated transcript), NOT `transcript_path`. Using the wrong variable name silently fails to capture transcripts.

### See also
For advanced hook patterns and event lifecycle, see [hook-development/references/patterns.md](../../../hook-development/references/patterns.md).

---

## Pattern 2: Hook-Based Behavioral Assertions [POWERS simulate.py]

### When to use
When you want deterministic, reproducible tests of agent behavior without LLM-as-judge: "agent must call Tool X with argument pattern Y", "agent must not exceed N tool calls", "agent must finish in < 30s".

### Mechanism
- Hooks: `PreToolUse` and `PostToolUse` (observer mode only; always exit 0)
- An observer.py script is injected via hook; it emits JSONL records with tool name, arguments, duration, return value
- After the agent run completes, assertions are evaluated against the JSONL log
- Assertions are defined in a simple schema: must_call, must_not_call, max_tool_calls, max_duration_s, final_response pattern, etc.

### Template

**observer.py (injected by hook):**
```python
import os, json, sys
from datetime import datetime

log_path = os.getenv("CLAUDE_CODE_TEST_LOG", ".claude/tool-calls.jsonl")
def record_tool(tool_name, args, duration, result):
    with open(log_path, "a") as f:
        json.dump({
            "tool": tool_name,
            "args": args,
            "duration_ms": duration,
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }, f)
        f.write("\n")
```

**assertions.yaml:**
```yaml
must_call:
  - tool: "Read"
    arg_pattern: "*.md"
must_not_call:
  - tool: "PowerShell"
max_tool_calls: 50
max_duration_s: 120
```

**simulate.py (evaluates assertions post-run):**
- Parses assertions.yaml
- Replays tool calls from the JSONL log
- Reports pass/fail and detailed evidence

### Pitfall
⚠️ **Exit codes:** Observer hooks MUST exit 0 even if a tool call is unexpected. Exit 2 (defer) or exit 1 (deny) changes agent behavior under test and invalidates the test. Observers record only; they do not gate.

### See also
For event filtering and advanced hook observability patterns, see [hook-development/references/patterns.md](../../../hook-development/references/patterns.md).

---

## Pattern 3: Permission-Policy Enforcement Scoped by `agent_type` [SAFETY]

### When to use
When you want role-based tool access control: "code-reviewer agents can call Bash and Read, but not Write"; "security-auditor agents can call Bash, Read, and WebSearch, but not Skill".

### Mechanism
- Hook: `PreToolUse` (decision hook; exit 0 = allow, exit 1 = deny)
- A generic Python policy script looks up the agent's `agent_type` in a YAML policy table
- The table maps {agent_type → {allowed_tools: [...], denied_tools: [...]}}
- If a tool call doesn't match the policy, the hook exits 1 to deny it
- If the agent_type is missing or unrecognized, a default policy applies (deny-all or allow-all, configurable)

### Template

**policy.yaml:**
```yaml
default_policy: "deny_all"
policies:
  code_reviewer:
    allowed:
      - Read
      - Grep
      - Bash(npm test)
    denied:
      - Write
      - Edit
  security_auditor:
    allowed:
      - Read
      - Bash
      - WebSearch
    denied:
      - Edit
      - Skill
```

**policy.py (invoked by PreToolUse hook):**
```python
import os, yaml, sys
agent_type = os.getenv("CLAUDE_CODE_AGENT_TYPE", "unknown")
tool_name = os.getenv("CLAUDE_CODE_TOOL_NAME")
policy = yaml.safe_load(open("policy.yaml"))
allowed = policy.get("policies", {}).get(agent_type, {}).get("allowed", [])
if tool_name not in allowed:
    sys.exit(1)  # Deny
sys.exit(0)  # Allow
```

### Pitfall
⚠️ **Main-session calls:** `agent_type` is absent when the agent is running in the main session (no subagent). Your hook must handle the `agent_type == None` case. Define a sensible default policy for main-session runs.

### See also
For comprehensive permission model documentation and advanced scoping, see [hook-development/references/patterns.md](../../../hook-development/references/patterns.md).

---

## Pattern 4: "Are You Done?" Stop Gates for Autonomous Agents [QUALITY]

### When to use
When an agent is autonomous (running via `/background` or scheduled) and you want to gate completion: verify that all TODOs are resolved, all tests pass, no uncommitted changes, or other stopping conditions are met.

### Mechanism
- Hook: `Stop` (or `SubagentStop` for subagents)
- A shell wrapper script runs a series of verification checks: pytest, git status, grep for TODO, etc.
- If any check fails, the hook exits 1 to block agent completion
- The agent receives the stop_reason and can decide to retry or escalate

### Template

**stop-gate.sh:**
```bash
#!/bin/bash
set -e

# Check 1: No uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
  echo "STOP: Uncommitted changes found"
  exit 1
fi

# Check 2: All tests pass
pytest tests/ -q || exit 1

# Check 3: No TODOs in src/
if grep -r "TODO" src/ --include="*.py"; then
  echo "STOP: TODOs remain in src/"
  exit 1
fi

# All checks passed
exit 0
```

**hooks.json entry:**
```json
{
  "event": "Stop",
  "type": "command",
  "command": "bash stop-gate.sh"
}
```

### Pitfall
⚠️ **Infinite loops:** Always check the `stop_hook_active` environment variable. If your Stop hook tries to fix the problem (e.g., by running git commit), and the check still fails, you create an infinite loop. Stop hooks should be read-only observers, or they should exit decisively without retriggering themselves.

### See also
For event sequencing and post-stop handling, see [hook-development/references/patterns.md](../../../hook-development/references/patterns.md).

---

## Pattern 5: Agent Identity Reload After Compaction [ADVANCED]

### When to use
When an autonomous agent needs to survive conversation compaction without losing critical context: invariant system instructions, role definitions, or long-lived state that must re-initialize the agent's identity post-compaction.

### Mechanism
- Hook: `PostCompact` (fires after context is summarized)
- Before the agent runs, you create a `.claude/agent-identity.md` file containing immutable invariants (role, constraints, key context)
- The PostCompact hook reads this file and re-injects its contents via `hookSpecificOutput.additionalContext` (limited to 10 KB)
- The re-injected context ensures the compacted agent session still "knows" the agent's identity

### Template

**.claude/agent-identity.md:**
```markdown
# Agent Identity — Preserved Across Compaction

## Role
Autonomous code reviewer. Mandate: find critical bugs in PRs, especially security and performance issues.

## Constraints
- Do NOT merge or approve PRs with failing tests.
- Do NOT approve any PR touching authentication without explicit security review.
- Timeout: fail-safe after 4 hours per review.

## Key State (do not lose)
- Current PR: #123 (github.com/example/repo)
- Assigned reviewer pool: [@alice, @bob]
- Escalation contact: @security-team
```

**PostCompact hook:**
```json
{
  "event": "PostCompact",
  "type": "command",
  "command": "cat .claude/agent-identity.md && echo '\n---\nIdentity restored post-compaction.' >&2 && exit 0"
}
```

### Pitfall
⚠️ **Full prompt re-injection:** Do NOT re-inject the complete system prompt or full agent definition. That defeats the purpose of compaction (saving tokens). Only re-inject the immutable, agent-specific invariants (role, key constraints, critical state). Everything else should be re-derived by the model.

### See also
For context management and lifecycle hooks, see [hook-development/references/patterns.md](../../../hook-development/references/patterns.md).

---

## Pattern 6: MCP Elicitation Auto-Handler for Headless Agents [ADVANCED]

### When to use
When a trusted MCP server requires user input (e.g., API keys, configuration details) and your agent is headless (running via `/background` or scheduled), but you want to auto-fill the input instead of blocking.

### Mechanism
- Hook: `Elicitation` with `type: "agent"` (subagent-backed hook)
- The hook spawns a minimal subagent with a prompt that fills the MCP schema from environment variables or config files
- The subagent returns the filled JSON schema
- The parent agent resumes with the elicitation resolved

### Template

**hooks.json entry:**
```json
{
  "event": "Elicitation",
  "type": "agent",
  "mcp_server_name": "github",
  "agent": {
    "model": "claude-sonnet-4-6",
    "prompt": "Fill this GitHub API schema from env vars: {{ schema_json }}. Use $GITHUB_TOKEN and $GITHUB_OWNER from environment."
  }
}
```

**Environment setup (before running headless agent):**
```bash
export GITHUB_TOKEN="ghp_..."
export GITHUB_OWNER="example-org"
```

### Pitfall
⚠️ **Trust boundary:** Only use agent-backed elicitation for trusted MCPs (GitHub, Slack, internal APIs you control). Never auto-fill credentials for untrusted external services. Allowlist by `mcp_server_name` to prevent schema injection.

### See also
For MCP integration patterns and advanced hook composition, see [hook-development/references/patterns.md](../../../hook-development/references/patterns.md).
