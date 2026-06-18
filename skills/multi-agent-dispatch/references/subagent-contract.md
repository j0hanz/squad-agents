# Subagent Prompt Contract (Zero-Shot)

Canonical contract for any skill that dispatches a `general-purpose` subagent. Subagents start cold — they have no memory of the parent conversation. Every dispatch prompt MUST contain all five fields below.

- **SCOPE:** Validated paths (In/Out of bounds). For writer roles, list the exact files the agent may touch.
- **OBJECTIVE:** One concrete, verifiable/falsifiable outcome. Not "improve X" — state the exact done-condition.
- **CONTEXT:** Error text, versions, baseline commit, conventions — everything needed to start cold. Never assume the agent can infer project context.
- **CONSTRAINTS:** Tool restrictions and specific "Do Not" rules. State explicitly if the agent must be read-only (no Write/Edit) — and note that this is an instruction, not an enforced restriction, unless the harness supports passing a tool allowlist.
- **OUTPUT SCHEMA:** Instruct the subagent to return data in this format:

  ```text
  VERDICT: [outcome enum specific to this dispatch — e.g. SUCCESS | FAILURE | BLOCKED]
  FILES_TOUCHED: [list of paths, or "none" for read-only roles]
  SUMMARY: [concise — what was done or found]
  EVIDENCE: [test results, grep output, or file:line citations]
  ```

  The `VERDICT` enum is dispatch-specific (e.g. `multi-agent-development`'s implementer uses `DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`; its reviewers use `SPEC_PASS | SPEC_FAIL` and `QUALITY_PASS | CRITICAL | IMPORTANT | MINOR`). Define the enum for the specific role, but never omit the schema.

## Role Vocabulary

Use these role labels when configuring subagents so isolation and tool-restriction decisions are explicit, not implied by prose:

- **Investigator (Read-only):** Trace root cause, propose a fix as a code block. No edits.
- **Writer (Isolation: worktree):** Implement a spec, write tests, report changes. Needs its own worktree if it runs experiments or makes edits that could collide with sibling agents.
- **Researcher (Read-only):** Explore code/docs, report file paths and usages.

## Never Trust, Always Verify

A subagent's report describes what it intended to do, not necessarily what it did. The dispatching skill MUST independently verify load-bearing claims (run the test suite, check `git status`/`git diff`) rather than accepting `VERDICT: SUCCESS` at face value.
