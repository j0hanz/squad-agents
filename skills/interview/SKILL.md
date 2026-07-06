---
name: interview
description: 'Use when project requirements are ambiguous, design decisions have unresolved branches, or options require user alignment. Symptoms: temptation to make assumptions under pressure.'
metadata:
  category: technique
  triggers: /grill-me, AskUserQuestion, ambiguous requirements, design options, clarify scope, user feedback, align plans, decision points, alternatives, unknowns
  allowed-tools: Read, Grep, Glob, AskUserQuestion
---

# Interview

Resolve critical, hard-to-reverse decisions (plans, designs, database schemas, package dependencies) before scoping or implementing. Stop when no unresolved decision materially affects architecture, cost, risk, or scope.

**Core Principle:** Follow the letter and spirit of these rules strictly.

## When to Use

Use when:

- Plans, designs, or findings have unresolved, hard-to-reverse branch points.
- Requirements are ambiguous or incomplete.
- Unknowns must be resolved with the user before defining scope.

### Escape Hatch (When NOT to Use)

Bypass only for:

- Spike/exploratory code where all work will be discarded.
- Trivial choices (e.g., local variable names, cosmetic UI). Architectural, API, database, dependency, or business logic choices are never trivial.
- Isolated yes/no confirmation gates (e.g., TDD checks, git push confirmations).

## How It Works

Follow this sequence strictly:

1. **Search First:** Search repository configs/docs (Read/Grep/Glob) for constraints before asking. Ground recommendations in findings.
2. **One at a Time:** Ask exactly one question per turn. Never combine decisions. Wait for feedback before asking the next.
3. **Tool Only:** Ask questions/clarifications only via the `AskUserQuestion` tool. Never ask in plain text.
4. **Two Realistic Options:** Provide exactly two options:
   - Option 1: Recommended grounded choice.
   - Option 2: Next most likely concrete alternative.
   - Do not provide passive/dummy choices (e.g., "Do nothing"). Both must be actionable paths.
5. **No Shrugging:** Reject vague answers; re-ask with mutually exclusive options. Do not nudge the user to defer. If they explicitly defer, proceed with the recommended choice.
6. **Wrap-Up:** End with a numbered list of all resolved decisions (one sentence each).

## Examples

### ❌ BAD (Plain text, compound, dummy option)

> "Should we use JWT or session cookies? Also, should we use Redis or PostgreSQL? Or we can just do nothing."

### ✅ GOOD (One question, structured options, grounded)

```json
{
  "Question": "Based on database.js, should we store sessions in PostgreSQL (recommended — matches existing db infra) or Redis (faster read/write but adds dependency)?",
  "Options": ["PostgreSQL (Recommended)", "Redis (Alternative)"]
}
```

## Checklist & Red Flags

Ensure these are true before completing the task:

- [ ] **Searched First:** Checked codebase conventions before proposing (Red Flag: Proposing choices blind).
- [ ] **Tool Usage:** All questions sent via `AskUserQuestion` (Red Flag: Plain text questions).
- [ ] **Single Focus:** Asked exactly one question per turn (Red Flag: Compound questions).
- [ ] **Two Options:** Offered exactly two realistic, actionable choices (Red Flag: Dummy choices like "Do nothing").
- [ ] **No Bias:** Did not nudge user to defer (Red Flag: Nudging or shrugging).
- [ ] **Wrap-Up:** Concluded with a numbered list of all resolved decisions.

## Related Skills

- [parallel-brainstorming](../parallel-brainstorming/SKILL.md) - Invokes interview for term clarification and approach locking.
- [project-audit](../project-audit/SKILL.md) - Invokes interview to pick which corroborated finding to formalize.
- [receive-plan](../receive-plan/SKILL.md) - Invokes interview to resolve risk/re-draft escalations.
