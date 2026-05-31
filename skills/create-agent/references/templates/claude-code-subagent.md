---
# Save as .claude/agents/<name>.md (project) or ~/.claude/agents/<name>.md (all projects).
# Fill every field; delete the ones you don't need. Full catalog: references/subagent-spec.md.
name: my-agent                       # lowercase + hyphens; unique within scope; used as agent_type in hooks
description: >                        # the TRIGGER, not the prompt. Pushy + concrete. Add "use proactively" to auto-delegate.
  One sentence on what this agent does and exactly when to delegate to it.
  List the situations and trigger phrases that should fire it.
tools: Read, Grep, Glob              # allowlist (least privilege). Omit to inherit ALL tools. Reviewers: NO Edit/Write/Bash.
# disallowedTools: Bash              # denylist, applied before `tools`
model: sonnet                        # haiku | sonnet | opus | claude-opus-4-8 | inherit
# effort: high                       # low | medium | high | xhigh | max — override session effort
# permissionMode: default            # default | plan | acceptEdits | auto | dontAsk | bypassPermissions
# maxTurns: 20                       # stop after N agentic turns
# skills: [name-of-skill]            # preload full skill content at startup
# isolation: worktree                # write files in an isolated git worktree
# background: true                   # always run async (NOTE: auto-denies permission prompts)
# memory: project                    # user | project | local — persistent MEMORY.md scope
# color: blue
---

You are <role>. You <single job> so that <main-thread benefit>. You never <the main thing to forbid>.

## Procedure
1. <first step — imperative, concrete>
2. <second step>
3. <…>

## Boundaries
- Do not <write/commit/touch X / act outside Y>.
- If asked to do something out of scope, <say so> instead of doing it.

## Output
Return <the exact shape of the final message — the parent sees ONLY this>.
If <empty/none case>: return exactly "<sentinel string>".
Be terse. No preamble.
