---
name: context-optimizer
description: "Diagnoses conversation bloat and prunes active context using token diagnostics, rolling summaries, and script-based compaction. Generates a flat key-value state summary file before executing the `/clear` command to reduce active token usage. Trigger on: 'optimize context', 'compress context', 'prune memory', 'reduce tokens', 'context size too large', 'out of tokens', 'compact context', 'clear history', 'cleanup context'. Also triggers when managing long development sessions, handling large file modifications, or resolving memory drift in nested subagent workflows. Always prefer this optimizer over running `/clear` directly when critical task progress and decisions need to be preserved."
disable-model-invocation: false
---

# context-optimizer

Optimize and prune active conversation context to prevent token limits and context drift. This skill provides systematic diagnostics to sniff context bloat (unignored directories, lockfiles, large source files) and pruning strategies (JSON compaction, traceback log filtering, and rolling summaries) to preserve agent reasoning efficiency in long developer sessions.

## Process Flow

```
Phase 1: Diagnose (Run scripts/diagnose_context_bloat.py and /context)
  -> Phase 2: Select Strategy (Choose KV compaction, log filtering, or rolling summary)
  -> Phase 3: Action (Run scripts/prune_context.py or specify StartLine/EndLine slices)
  -> Phase 4: Reset & Reload (Save summary, run /clear, reload summary)
```

## Step 1: Diagnose Bloat

1. Check for workspace dirtiness and large files:
   `python skills/context-optimizer/scripts/diagnose_context_bloat.py` _(Use `$CLAUDE_PLUGIN_ROOT/` prefix if required)_.
2. Run `/context` to inspect token usage.
3. Verify `CLAUDE.md` and `GEMINI.md` link to `AGENTS.md` instead of full rules text.

## Step 2: Apply Strategy

**MANDATORY PREREQUISITE:** Before executing Strategy A, B, or Step 3, you **MUST** read `references/context-pruning-guidelines.md` completely from start to finish. **NEVER** set range limits when reading this file.

Select ONE strategy based on diagnostics:

- **Strategy A: KV Compaction (JSON/Configs)**
  `python skills/context-optimizer/scripts/prune_context.py --to-kv < data.json`
- **Strategy B: Log Truncation (Test Failures/Traces)**
  `python skills/context-optimizer/scripts/prune_context.py --logs < test_output.log`
- **Strategy C: Line Slicing (Large Files)**
  Find target lines using `grep_search`, then read ONLY the required lines using `StartLine` and `EndLine`.
- **Strategy D: Subagent Isolation (Complex Tasks)**
  Delegate to a subagent to protect the main context.

## Step 3: Clear and Resume (For Bloated Sessions)

1. Write a flat Key-Value status:
   `python skills/context-optimizer/scripts/prune_context.py --summary --timestamp "$(date -Iseconds)" --done "completed items" --blocking "blockers" --next-step "next actions" --decisions "key decisions"`
2. Tell the user: "Clearing history. Please type 'resume'."
3. Run `/clear`.
4. Reload `.claude/rolling_summary.md` to continue.

## STRICT PROHIBITIONS

- **NEVER** read files larger than 300 lines without specifying `StartLine` and `EndLine`. Run `grep_search` first.
- **NEVER** run `/clear` without writing `.claude/rolling_summary.md` first. Progress will be lost.
- **NEVER** paste full JSON structures or verbose test/build stdout. Always use Strategy A or B to compact them.

**Next Skills:**

- `planning`: Trigger if context reveals major specification gaps.
- `using-agent-dev-skills`: Return to the main router once optimized.
