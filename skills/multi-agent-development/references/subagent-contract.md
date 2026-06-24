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

## Common Mistakes (fix these before dispatching)

A prompt that violates the five-field contract wastes a whole agent run. Most failures are one of these:

| Mistake                                                | Better                                                                                        |
| :----------------------------------------------------- | :-------------------------------------------------------------------------------------------- |
| "Fix all the failing tests" (unbounded scope)          | "Fix `src/auth/jwt.test.ts` only; do not edit other files" (one file, explicit out-of-bounds) |
| "Fix the race condition" (no context)                  | Paste the error text + failing test name + baseline commit                                    |
| No CONSTRAINTS — agent edits files a sibling lane owns | "Read-only. Touch nothing under `src/api/`."                                                  |
| No OUTPUT SCHEMA — reply is freeform prose             | Require `VERDICT/FILES_TOUCHED/SUMMARY/EVIDENCE` verbatim                                     |
| "Improve the code" (unfalsifiable objective)           | "All 6 tests in the file pass, 0 skipped" (a checkable done-condition)                        |

## Role Vocabulary

Use these role labels when configuring subagents so isolation and tool-restriction decisions are explicit, not implied by prose. For a read-only Investigator/Researcher lane, prefer a more specific `subagent_type` already present in the user's installed agent roster over generic `general-purpose` when one matches the lane's task domain; fall back to `general-purpose` when none matches. Name no specific third-party agent here — this plugin ships no `agents/` directory of its own, so any named example would be environment-specific.

- **Investigator (Read-only):** Trace root cause, propose a fix as a code block. No edits.
- **Writer (Isolation: worktree):** Implement a spec, write tests, report changes. Needs its own worktree if it runs experiments or makes edits that could collide with sibling agents.
- **Researcher (Read-only):** Explore code/docs, report file paths and usages.

### Routing a lane to a specialist

A generalist runs every lane competently; a domain specialist runs its own lane
_better_. Before defaulting to `general-purpose`, match the lane's domain to an
installed agent. Match by **category** below, not by name — rosters differ per
environment, so look up what's actually installed and fall back to
`general-purpose` when nothing matches.

| Lane domain                         | Look for an installed agent that does…         | Fallback          |
| :---------------------------------- | :--------------------------------------------- | :---------------- |
| Architecture / cross-module design  | architecture or system-design review           | `general-purpose` |
| Language-specific code quality      | a reviewer for that language (e.g. Python, TS) | `general-purpose` |
| Error handling / swallowed failures | silent-failure / error-path auditing           | `general-purpose` |
| Root-cause debugging                | a debugging / detective specialist             | `general-purpose` |
| Docs sync after a change            | a documentation specialist                     | `general-purpose` |

The contract is unchanged whichever agent runs the lane: all five fields still
required, and the report is still independently verified (see below).

## Never Trust, Always Verify

A subagent's report describes what it intended to do, not necessarily what it did. The dispatching skill MUST independently verify load-bearing claims (run the test suite, check `git status`/`git diff`) rather than accepting `VERDICT: SUCCESS` at face value.
