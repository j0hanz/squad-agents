# Subagent Prompt Contract (Zero-Shot)

Canonical contract for any skill that dispatches a `general-purpose` subagent — shared by `multi-agent-development` and `multi-agent-dispatch`. Subagents start cold — they have no memory of the parent conversation. Every dispatch prompt MUST contain all five fields below.

This plugin's `agents/` directory ships four named agents covering fixed roles: `implementer` (Writer — used by both `multi-agent-development`'s Phase 1 and `multi-agent-dispatch`'s Writer lanes), `spec-reviewer` and `quality-reviewer` (`multi-agent-development`'s Phase 2/Phase 3 gates), and `diff-reviewer` (`request-code-review`'s dispatch target). Each has its own fixed output schema described in its own file and no longer needs the generic fallback below. The generic schema remains the fallback for any role without a matching named agent — Investigator/Researcher lanes in `multi-agent-dispatch`, and any specialist category in the "Routing a lane to a specialist" table below.

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

Use these role labels when configuring subagents so isolation and tool-restriction decisions are explicit, not implied by prose. For a read-only Investigator/Researcher lane, prefer a more specific `subagent_type` already present in the user's installed agent roster over generic `general-purpose` when one matches the lane's task domain; fall back to `general-purpose` when none matches. This plugin's own `agents/` directory covers four fixed roles by name — `implementer` (Writer), `spec-reviewer` and `quality-reviewer` (the two Reviewer gates below), and `diff-reviewer` (used by `request-code-review`) — so those roles are named directly rather than left generic. The categories in the table below (architecture review, language-specific quality, error-handling auditing, root-cause debugging, docs sync) have no matching named agent in this plugin, so for those, fall back to scanning the user's installed roster as described, then `general-purpose` if nothing matches.

- **Investigator (Read-only):** Trace root cause, propose a fix as a code block. No edits. No named agent matches this role — dispatch `general-purpose` with the generic VERDICT/FILES_TOUCHED/SUMMARY/EVIDENCE schema below.
- **Writer (Isolation: worktree):** Implement a spec, write tests, report changes. Dispatch the named `implementer` agent (`agents/implementer.md`) for this role — it already requires `isolation: worktree` and returns its own schema (`VERDICT: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]` + SUMMARY/FILES_CHANGED/COMMIT/CONCERNS/BLOCKER/QUESTION), not the generic schema below. Both `multi-agent-development` (Phase 1) and `multi-agent-dispatch` (Step 3 Writer lanes) dispatch it this way.
- **Researcher (Read-only):** Explore code/docs, report file paths and usages. No named agent matches this role — dispatch `general-purpose` with the generic schema below.
- **Reviewer (Read-only):** Verify a Writer's diff against a spec or quality bar — never the Writer's own summary. `multi-agent-development` dispatches the named `spec-reviewer` (Phase 2) and `quality-reviewer` (Phase 3) agents for this role; `request-code-review` dispatches the named `diff-reviewer` agent. Each has its own fixed output schema rather than the generic schema below.

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
