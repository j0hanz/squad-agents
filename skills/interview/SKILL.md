---
name: interview
description: 'Called inline by other skills to stress-test a plan, design, or decision before committing to it.'
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, AskUserQuestion
---

# Interview

**Objective:** Resolve every material, hard-to-reverse decision in whatever is on the table — plan, design, finding, or escalation. Stop when no unresolved decision would meaningfully affect architecture, implementation, cost, risk, or scope.

**Called by:** other skills invoke this one inline (via the `Skill` tool, same thread, full context already shared — no cold-start prompt needed) whenever their own flow reaches a hard-to-reverse branch point instead of hand-rolling a question loop. Known callers: `parallel-brainstorming` (Phase 2 term clarification, Phase 4 approach lock), `project-audit` (picking which corroborated finding to formalize), `receive-plan` (2nd-round REVISE escalation: accept risk vs. re-draft vs. abandon). A skill with only a single, isolated yes/no confirmation embedded in a tight loop (e.g. a TDD scope check, a push confirmation) is not this skill's job — that's a gate, not a session; don't route it here.

**Strict Execution Rules:**

- **Search First:** When working inside a repository, use Read/Grep/Glob to find existing decisions, conventions, or constraints relevant to the plan before questioning — stop once you've checked the obvious places (config, similar existing features, docs), not exhaustively. Use what you find to ground your recommended option in each question. If no repository context exists, proceed directly to interviewing.
- **One at a Time:** Ask exactly ONE question. Wait for my feedback before asking the next.
- **Tool Only:** You MUST use the `AskUserQuestion` tool for every question. Never ask via plain text.
- **Strictly Two Options:** Provide EXACTLY 2 options per question:
  1. Your recommended answer.
  2. The next most likely alternative (or a concrete "something else" framing if truly open-ended — still a real option, not a duplicate of the tool's built-in "Other").
     _(Do not add a third "Other" option; the tool includes one automatically)._
- **No Shrugging:** Reject vague or one-word answers and re-ask via `AskUserQuestion` with sharper options. Push for concrete decisions, prioritizing hard-to-reverse choices over trivial ones. Skip decisions that are trivially reversible or default-safe — don't interview on those. If the user explicitly defers to your judgment after a re-ask, take your recommended option, record it as the decision, and move on.
- **Resolution Standard:** A decision is resolved only when it can be recorded as a clear implementation instruction with no material ambiguity.
- **Nothing to Ask:** If the plan has no hard-to-reverse branches left (or none to begin with), say so and stop — don't manufacture questions to fill the format.
- **Wrap-Up:** When every branch is resolved, end with a numbered list of the resolved decisions, one definitive sentence each.

**Example:** "Should auth use JWT (recommended — stateless, no session store) or session cookies (simpler revocation)?"

## Next Skills

Hands the numbered resolved-decisions list back to whichever skill invoked it — interview never drafts, implements, or commits anything itself. The caller resumes its own process flow from there.
