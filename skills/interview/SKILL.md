---
name: interview
description: 'Use when a plan, design, or decision has unresolved hard-to-reverse branches to lock before committing — requirements are ambiguous or incomplete before scoping a task, or unknowns must be resolved via AskUserQuestion before defining scope.'
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, AskUserQuestion
---

# Interview

**Objective:** Resolve every material, hard-to-reverse decision on the table — plan, design, finding, or escalation. Stop when no unresolved decision would materially affect architecture, implementation, cost, risk, or scope.

**Called by:** other skills invoke this one inline (via the `Skill` tool, same thread, full context shared — no cold-start prompt) when their flow hits a hard-to-reverse branch point instead of hand-rolling a question loop. Known callers: `parallel-brainstorming` (Phase 2 term clarification, Phase 4 approach lock), `project-audit` (picking which corroborated finding to formalize), `receive-plan` (2nd-round REVISE escalation: accept risk vs. re-draft vs. abandon). A single isolated yes/no confirmation embedded in a tight loop (e.g. a TDD scope check, a push confirmation) is a gate, not a session — don't route it here.

**Strict Execution Rules:**

- **Search First:** When inside a repository, use Read/Grep/Glob to find existing decisions, conventions, or constraints before questioning — check the obvious places (config, similar existing features, docs), not exhaustively. Ground each recommended option in what you find. If no repository context exists, proceed directly to interviewing.
- **One at a Time:** Ask exactly ONE question. Wait for feedback before the next.
- **Tool Only:** MUST use the `AskUserQuestion` tool for every question. Never ask via plain text.
- **Strictly Two Options:** Provide EXACTLY 2 options per question:
  1. Your recommended answer.
  2. The next most likely alternative (or a concrete "something else" framing if truly open-ended — a real option, not a duplicate of the tool's built-in "Other").
     _(Do not add a third "Other" option; the tool includes one automatically.)_
- **No Shrugging:** Reject vague or one-word answers and re-ask with sharper options. Push for concrete decisions, prioritizing hard-to-reverse choices over trivial ones. Skip trivially reversible or default-safe decisions — don't interview on those. If the user explicitly defers to your judgment after a re-ask, take your recommended option, record it as the decision, and move on.
- **Resolution Standard:** A decision is resolved only when recordable as a clear implementation instruction with no material ambiguity.
- **Nothing to Ask:** If no hard-to-reverse branches remain (or none existed), say so and stop — don't manufacture questions to fill the format.
- **Wrap-Up:** When every branch is resolved, end with a numbered list of the resolved decisions, one definitive sentence each.

**Example:** "Should auth use JWT (recommended — stateless, no session store) or session cookies (simpler revocation)?"

## Next Skills

Hands the numbered resolved-decisions list back to whichever skill invoked it — interview never drafts, implements, or commits anything itself. The caller resumes its own process flow from there.
