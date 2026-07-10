---
name: interview
description: 'Use when project requirements are ambiguous, design decisions have unresolved branches, or options require user alignment. Symptoms: temptation to make assumptions under pressure.'
metadata:
  category: technique
  triggers: ambiguous requirements, design options, clarify scope, user feedback, align plans, decision points, alternatives, unknowns
  allowed-tools: Read, Grep, Glob, AskUserQuestion
---

# Interview

Resolve critical, hard-to-reverse decisions (plans, designs, database schemas, package dependencies) before scoping or implementing. Stop when no unresolved decision materially affects architecture, cost, risk, or scope.

## When to Use

- Plans, designs, or findings have unresolved, hard-to-reverse branch points.
- Requirements are ambiguous or incomplete.
- Unknowns must be resolved with the user before defining scope.

### Escape Hatch (When NOT to Use)

Bypass only for:

- Spike/exploratory code where all work will be discarded.
- Trivial choices (e.g., local variable names, cosmetic UI). Architectural, API, database, dependency, or business logic choices are never trivial.
- Isolated yes/no confirmation gates (e.g., TDD checks, git push confirmations).

## How It Works

1. **Search First:** Search repository configs/docs (Read/Grep/Glob) for constraints before asking. Ground recommendations in findings.
   - _Gate: every option cited to a codebase finding. Red Flag: proposing choices blind._
2. **One at a Time:** Ask exactly one question per turn. Never combine decisions. Wait for feedback before asking the next.
   - _Gate: one decision per turn. Red Flag: compound questions._
3. **Tool Only:** Ask questions/clarifications only via the `AskUserQuestion` tool. Never ask in plain text.
   - _Gate: all questions sent via `AskUserQuestion`. Red Flag: plain text questions._
4. **Two Realistic Options:** Provide exactly two options — a binary prevents deferral. Option 1 is the recommended grounded choice; Option 2 is the next most likely concrete alternative. Both must be actionable paths; no passive/dummy choices (e.g., "Do nothing").
   - _Gate: exactly two realistic, actionable choices. Red Flag: dummy choices._
5. **No Shrugging:** Reject vague answers; re-ask with mutually exclusive options. Do not nudge the user to defer. If they explicitly defer, proceed with the recommended choice.
   - _Gate: a concrete choice locked, or recommended choice taken on explicit defer. Red Flag: nudging or shrugging._
6. **Wrap-Up:** End with a numbered list of all resolved decisions (one sentence each).
   - _Gate: every resolved decision listed. Red Flag: closing without the list._

## Examples

### ❌ BAD (Plain text, compound, dummy option)

> "Should we use JWT or session cookies? Also, should we use Redis or PostgreSQL? Or we can just do nothing."

### ✅ GOOD (One question, structured options, grounded)

```json
{
  "questions": [
    {
      "question": "Based on database.js, should we store sessions in PostgreSQL or Redis?",
      "options": ["PostgreSQL (Recommended)", "Redis (Alternative)"]
    }
  ]
}
```

## Related Skills

- [parallel-brainstorming](../parallel-brainstorming/SKILL.md) - Invokes interview for term clarification and approach locking.
- [project-audit](../project-audit/SKILL.md) - Invokes interview to pick which corroborated finding to formalize.
- [receive-plan](../receive-plan/SKILL.md) - Invokes interview to resolve risk/re-draft escalations.
