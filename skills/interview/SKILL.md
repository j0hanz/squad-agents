---
name: interview
description: 'Use when project requirements are ambiguous, design decisions have unresolved branches, or options require user alignment. Symptoms: temptation to make assumptions under pressure.'
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, AskUserQuestion
---

# Interview

Resolve critical, hard-to-reverse decisions (plans, designs, database schemas, package dependencies) before scoping or implementing. Stop when no unresolved decision materially affects architecture, cost, risk, or scope.

## How It Works

1. **Search First:** Search repository configs/docs (Read/Grep/Glob) for constraints before asking. Ground recommendations in findings.
   - **Done when:** every option is cited to a specific codebase finding or config file. (Red Flag: proposing choices blind).
2. **One at a Time:** Ask exactly one question per turn. Never combine decisions. Wait for feedback before asking the next.
   - **Done when:** exactly one decision point is presented in the current interaction. (Red Flag: compound questions).
3. **Tool Only:** Ask questions/clarifications only via the `AskUserQuestion` tool. Never ask in plain text.
   - **Done when:** the question is sent using the AskUserQuestion tool. (Red Flag: plain text questions).
4. **Two Realistic Options:** Provide exactly two options — a binary prevents deferral. Option 1 is the recommended grounded choice; Option 2 is the next most likely concrete alternative. Both must be actionable paths; no passive/dummy choices (e.g., "Do nothing").
   - **Done when:** exactly two realistic, actionable choices (Recommended and Alternative) are presented. (Red Flag: dummy choices).
5. **No Shrugging:** Reject vague answers; re-ask with mutually exclusive options. Do not nudge the user to defer. If they explicitly defer, proceed with the recommended choice.
   - **Done when:** a concrete path is locked or the recommended path is chosen after explicit user deferral. (Red Flag: nudging or shrugging).
6. **Wrap-Up:** End with a numbered list of all resolved decisions (one sentence each).
   - **Done when:** a numbered, single-sentence summary of all resolved decisions is output. (Red Flag: closing without the list).

## Examples

### BAD: Plain text, compound, dummy option

> "Should we use JWT or session cookies? Also, should we use Redis or PostgreSQL? Or we can just do nothing."

### GOOD: One question, structured options, grounded

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

| Skill                                                        | Description                                                       |
| :----------------------------------------------------------- | :---------------------------------------------------------------- |
| [parallel-brainstorming](../parallel-brainstorming/SKILL.md) | Invokes interview for term clarification and approach locking     |
| [project-audit](../project-audit/SKILL.md)                   | Invokes interview to pick which corroborated finding to formalize |
| [receive-plan](../receive-plan/SKILL.md)                     | Invokes interview to resolve risk/re-draft escalations            |
