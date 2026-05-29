# Hook Development Best Practices

This reference covers deep thinking frameworks, decision criteria, and critical anti-patterns for Claude Code hooks.

## The Cost-Benefit Decision Tree

Before adding ANY hook, use this ROI calculator:

```text
Is the validation DETERMINISTIC and FAST? (< 5ms)
├─ YES → Use command hook (worth the latency)
│
├─ NO → Is the validation SEMANTIC and WORTH 100-200ms?
│       ├─ YES → Use prompt hook (tradeoff justified)
│       │
│       ├─ NO → Can you validate IN-TOOL instead?
│               ├─ YES → Don't hook, let tool handle it
│               │
│               ├─ NO → Is this preventing 5+ errors per session?
│                       ├─ YES → Use hook (ROI justified)
│                       ├─ NO → Don't hook (not worth latency tax)
```

**Key principle:** Hooks cost latency. Only add them when the benefit (risk reduction or automation value) exceeds the cost (user wait time).

## Decision: PreToolUse vs PostToolUse

Ask: **Can the operation be undone or fixed naturally after execution?**

```text
Is the operation DESTRUCTIVE (can't be undone)?
├─ YES (rm -rf, delete DB row, chmod 000)
│   └─ Use PreToolUse (prevent before execution)
├─ NO → Can the ERROR be CAUGHT IN-TOOL and FIXED?
        ├─ YES (syntax errors, type errors, validation errors)
        │   └─ Use PostToolUse (let tool catch and Claude fixes)
        ├─ NO (operation succeeds but wrong, no error signal)
        │   └─ Use PreToolUse (no other way to prevent)
```

## Decision: Command vs Prompt Hook

Ask: **Can I express the validation as simple rules?**

```text
Can you express the validation as SIMPLE RULES?
├─ YES (path patterns, file extensions, command regex)
│   └─ Is it < 5ms to evaluate?
│       ├─ YES → Use command hook (worth the latency)
│       ├─ NO → Need semantic analysis?
│           ├─ YES → Use prompt hook (accept 100–200ms)
│           ├─ NO → Make the rule simpler
├─ NO (requires reasoning, context, judgment)
    └─ Use prompt hook (accept 100–200ms latency)
```

---

## Critical Anti-Patterns (The NEVER List)

### NEVER: add PreToolUse validation you can do in-tool

**Example:** Hooking file writes to validate JSON syntax.
**Why:** Hook runs before Claude acts. If you reject valid code, Claude retries, hook rejects again, causing a loop. Meanwhile you've added 100ms latency to every write.
**Fix:** Use `PostToolUse` for feedback or let the tool error out. Claude is excellent at fixing errors it sees in-tool.

### NEVER: assume hooks see each other's output

**Why:** Hooks run in **parallel**. If Hook A denies and Hook B approves, they don't coordinate.
**Fix:** Merge interdependent logic into a single hook. If they must be separate, use the filesystem (temp files with `$$` PID) to share state.

### NEVER: use `eval` or `exec` on tool inputs in hooks

**Why:** You are passing untrusted Claude output (which might be manipulated by a prompt injection) into a shell.
**Fix:** Use `jq` to parse JSON and strictly validate variable contents using regex before use.

### NEVER: forget hooks are loaded at session start

**Symptom:** "I fixed the `hooks.json`, but it's still denying everything."
**Why:** Claude Code caches hook configuration at startup.
**Fix:** Exit (`ctrl+c`) and restart Claude Code to load changes.

### NEVER: use hardcoded absolute paths

**Why:** Plugins move between machines. `/Users/admin/scripts` won't exist on a CI server or a teammate's machine.
**Fix:** Always use `${CLAUDE_PLUGIN_ROOT}` for scripts and `${CLAUDE_PROJECT_DIR}` for project files.

### NEVER: run long-running operations in hooks

**Why:** Default timeouts are ~30s. If a hook takes longer, the tool call fails or hangs.
**Fix:** Use background scripts or move long-running tasks to `PostToolUse` where they don't block the critical path.

### NEVER: rely on hook execution order

**Why:** Parallel execution is non-deterministic. "Hook 1 runs then Hook 2" is a race condition.
**Fix:** Design for independence or use a single "Orchestrator" hook that calls sub-scripts sequentially.

### NEVER: assume Claude will fix malformed JSON from your hook

**Why:** Claude Code parses hook output strictly. Invalid JSON results in a silent failure or a crash.
**Fix:** Always pipe output to `jq .` during development to verify format.
