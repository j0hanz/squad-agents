---
name: brainstorming
description: "Structured requirements discovery before implementation. Trigger on 'let's build', 'new feature', 'we need a new', 'I want to implement', 'add X to', 'create a Y', ambiguous design, or unclear terminology — even when the user says 'just build it'. Proactively offer before any implementation begins. Prevents rework by catching problems early."
---

## Routing

| Condition                                                                                                 | Action                                      |
| --------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| "let's build X", "new feature", "we need a new Y", "I want to implement Z", any new component or behavior | **Run** — even if user says "just build it" |
| Domain terminology ambiguous, foundational assumptions unvalidated                                        | **Run**                                     |
| User unsure how to approach a design problem                                                              | **Run**                                     |
| Bug fix with clearly defined problem and root cause                                                       | **Skip**                                    |
| Pure refactor with no behavior change                                                                     | **Skip**                                    |
| Documentation-only update                                                                                 | **Skip**                                    |
| Design already explicitly approved, implementation is the next step                                       | **Skip**                                    |

# Brainstorming

## Conversation Rhythm

**rhythm:** one question at a time — wait for each answer before asking the next.

**Fast Track (resistant users OR Scope S):**
If the user declines brainstorming, OR Phase 1 scan returns Scope S with no Key Unknowns and no ambiguous terminology:

1. Acknowledge the request for speed.
2. Dispatch a `general-purpose` subagent loaded with `references/codebase-scanner-prompt.md`.
3. Present a **single, grounded proposal** based on the scanner's report.
4. If approved, skip to Phase 5.

**Scope XL check:** If scanner returns Scope XL, pause before Phase 2. Ask: "This appears to span 10+ files or multiple modules. Should we split into phases and tackle one slice first?"

<constitutional_constraints>
<rule id="1" severity="HIGH">You MUST NOT ask leading questions — let the user define the domain.</rule>
<rule id="2" severity="HIGH">You MUST NOT assume two terms mean the same thing — inventory ALL contexts before drilling into any one.</rule>
<rule id="3" severity="HIGH">You MUST NOT capture implementation details during discovery — capture WHAT a concept IS, not HOW it is built.</rule>
<rule id="4" severity="CRITICAL">You MUST NOT write code or scaffolding before design is approved.</rule>
</constitutional_constraints>

## Red Flags

| Thought                              | Reality                                                   |
| ------------------------------------ | --------------------------------------------------------- |
| "The requirements are obvious"       | Assumptions cause rework. Clarify anyway.                 |
| "I'll start simple and iterate"      | Design approval comes first — see the gate below.         |
| "We can figure out edge cases later" | Edge cases belong in the spec, not the debugger.          |
| "This is too small to need design"   | Small features accumulate into large regrets.             |
| "The user said just build it"        | Offer a quick brainstorm first. User can decline.         |
| "Everyone knows what X means"        | Ambiguous terms corrupt specs. Capture them in Phase 2.   |
| "I'll define terms after we design"  | Terminology conflicts surface in specs at the worst time. |

**Design approval gate:** Do not write any code, scaffolding, or invoke any implementation skill until the user has explicitly approved a design in Phase 4.

## Dispatch Agents

Both dispatches below use `Agent(subagent_type: "general-purpose", ...)`. Load the referenced template, fill in the `[FIELD]` placeholders, then dispatch. Do not redo their work manually.

| Role             | Template                                | When to spawn                                  |
| ---------------- | --------------------------------------- | ---------------------------------------------- |
| Codebase scanner | `references/codebase-scanner-prompt.md` | Start of Phase 1, before asking any questions  |
| Design proposer  | `references/design-proposer-prompt.md`  | Start of Phase 4, before presenting approaches |

For parallel codebase scanning across multiple hypotheses, use the `multi-agent-dispatch` skill.

## Phase 1: Discovery (Read Before Asking)

**Stakeholder probe:** If who will use the feature is not evident from context, ask this one question while the scanner runs: "Who interacts with this feature most — end users, internal teams, or other systems?" This single answer changes Phase 4 design tradeoffs significantly.

Dispatch the codebase scanner (`references/codebase-scanner-prompt.md`) — pass the feature description exactly as stated. Wait for the Codebase Context Report.
**Timeout / Dead-Letter Fallback:** If the scan times out or fails (e.g. due to repository size), do not fail the workflow. Instead, automatically fall back to shallow regex heuristics: use `grep_search` and `glob` with strict depth limits to map the immediate domain, or explicitly request the user to limit the scope.

Summarize your understanding in one paragraph, drawing from the report: what was found, what constraints exist, what Key Unknowns were flagged, and what you don't know yet. Ask the user to confirm.

**Scope-adaptive routing after scan:**

| Scanner output                                | Route                                                          |
| --------------------------------------------- | -------------------------------------------------------------- |
| Scope S + no Key Unknowns + terminology clear | **Compressed Track** — skip Phase 2–3, go directly to Phase 4  |
| Scope XL                                      | **Phase split check** — offer to break into sub-features first |
| Key Unknowns flagged OR ambiguous terminology | **Full track** — run Phase 2 or Phase 3 as appropriate         |

**domain-trigger:** If scan reveals ambiguous or conflicting terminology, run Phase 2 before continuing.

### Phase 1 Example

**User says:** "We need to add search to our product."

**Your understanding statement:**
"I understand you need full-text search for your product so users can find data faster. Currently, I don't know: if you want real-time indexing, if search needs to be fuzzy, or if there are performance constraints. Do I have this right?"

## Phase 2: Domain Clarity (When Terminology is Ambiguous)

**Skip** if domain terminology is clear and consistent throughout code, docs, and user language.

**Definition is clear when:**

- User can explain WHAT the concept IS (not just what it does)
- User can explain how it differs from similar terms (Account vs Organization vs Customer)
- User can point to where it appears in code/docs/conversations

**Not clear if:** Definition relies on "everyone knows what this means" or varies by team.

**Invoke when:** same term has multiple meanings, team and code use different names for the same concept, user asks "what do we call X?", or docs are inconsistent.

**Fundamental disagreement:** If domain experts disagree on WHAT we're building, document both positions and escalate before proceeding to Phase 4.

For each ambiguous term:

1. Ask the user to define it in their own words — never lead with a definition.
2. Ask where it appears: code, docs, team discussions?
3. If two teams have valid reasons for different terms: document both with a boundary — don't force one side to abandon their mental model.

**3-turn rule:** If 3 questions fail to define a term clearly, mark it TBD with an owner and move on.

**Output format for captured terms:**

```
[Canonical Term]: [Definition]. Aliases: [alias1, alias2]
(TBD: [Question] — Owner: [Role/Person])
Conflict resolution: [how overlapping usages were resolved]
```

Offer to write findings to `glossary.md` or `CONTEXT.md` at Phase 5 transition.

## Phase 3: Expert Clarification (Surface the Unsaid)

Pick 1–2 techniques based on conversation signals. Do not run all as a script.

| Situation                                              | Use This          | Reason                                                  |
| ------------------------------------------------------ | ----------------- | ------------------------------------------------------- |
| User says "just build it" or requirements seem obvious | **Why**           | Uncovers hidden motivation                              |
| Large scope or complex dependencies                    | **Premortem**     | Surfaces organizational/technical risks                 |
| Success criteria vague ("just make it fast")           | **Success Logic** | Clarifies acceptance criteria                           |
| Feature creep risk or unclear boundaries               | **Anti-Scope**    | Defines what we're explicitly NOT building              |
| Feature handles sensitive data or user permissions     | **Trust Breach**  | Identifies security/privacy vulnerabilities             |
| Stuck in conventional thinking, options feel obvious   | **Analogy**       | Unlocks non-obvious solutions via cross-domain transfer |
| Scope or constraints feel fuzzy or contested           | **Inversion**     | Reveals constraints by imagining worst-case failure     |

**Depth check:** After 1–2 techniques, ask: "Are there other risks or unknowns that could derail this?"

- Yes → apply one more technique, then proceed regardless
- No → document TBD items and proceed to Phase 4

**Hard limit: 4 questions total within Phase 3.** Unresolved questions become TBD items with an owner.

1. **The "Why" (Five Whys):** "Why is this needed _now_? What fails if we don't do this?"
2. **The Premortem:** "Imagine we've implemented this and it's a disaster. What's the most likely thing that went wrong?"
3. **Success Logic:** "How will we know this is a success without using the word 'functional'? What behavior change should we see?"
4. **The "Anti-Scope":** "What's a related feature that we are _strictly_ choosing NOT to build today?"
5. **The Trust Breach:** "If a malicious actor wanted to abuse this feature, what would be their easiest path?"
6. **The Analogy:** "What does a non-digital version of this problem look like? How do people solve it without software?" _(Use when options feel narrow or conventional)_
7. **The Inversion:** "Describe the feature that would cause the most damage if built wrong. What does the safe inverse look like?" _(Use when scope or constraints feel fuzzy)_

## Creative Checkpoint

Before spawning design-proposer, spend 30 seconds on these three checks:

- Is there a zero-code or near-zero-code solution already in the codebase (config flag, existing extension point)?
- Has an adjacent feature already solved a structurally similar problem? (The scanner's Analogous Features section reveals this — e.g., an existing "export" flow when building "import".)
- What would the 10× simpler version look like? Is it good enough for the stated success criteria?

If any answer is "yes" or "possibly" — surface it to the user in one sentence before spawning design-proposer. Include the finding in the context packet as a candidate approach. This one check prevents the most common failure mode: over-engineering a problem that already has a 5-line solution.

### Phase 4: Design Proposal

**Note on resolution:** use the absolute path of the directory containing this `SKILL.md` file as `<skill-dir>` (or `$CLAUDE_PLUGIN_ROOT/skills/brainstorming` if available).

Compress the Codebase Context Report before spawning:

```bash
python <skill-dir>/scripts/compress_report.py <path-to-report.json>
# or pipe directly:
echo '<report-json>' | python <skill-dir>/scripts/compress_report.py
```

If the script fails, pass the raw report as-is.

Dispatch the design proposer (`references/design-proposer-prompt.md`) with a context packet containing:

- Feature description (confirmed in Phase 1)
- Stakeholder type (from Phase 1 probe, or "not specified")
- Codebase Context Report (compressed), including Analogous Features and Test Coverage
- Domain terms (from Phase 2, or "Phase 2 skipped")
- Risks and success criteria (from Phase 3, or "Phase 3 skipped")
- Creative Checkpoint findings (or "none identified")
- Any constraints the user stated explicitly

Present the design proposals in sections. Validate each section before continuing.

**Design approval gate:** Ask: "Which approach should we move forward with and why?"

Wait for explicit commitment:

- "We'll go with Approach B because..."
- "Let's do Option 1, here's why..."

Ambiguous responses ("sounds good") → clarify which specific approach they're choosing.

**If all approaches are rejected:**

1. Ask: "What felt most wrong — the complexity, the direction, or an unstated constraint?"
2. Extract the new constraint or direction from their answer.
3. Re-spawn `design-proposer` once with a "pivot context" addendum: original packet + rejection reason + new constraint.
4. If rejected again, hand design leadership back: "It sounds like you have a specific direction in mind — can you describe it and I'll document it as the Design Brief?"

## Phase 5: Transition

1. Summarize the approved approach in one short paragraph: chosen option and key tradeoffs.
2. If Phase 2 captured terms or Phase 3 captured risks: offer to write to `glossary.md` or `CONTEXT.md`. **If there are Open TBDs, offer to save them to `TODO.md` or a tracker.**
3. **MANDATORY**: Produce the Design Brief below and write a corresponding `design-brief.json` file to disk. This JSON file is the standardized handoff artifact for the `planning` skill. Stop — do not invoke `/plan` or write code automatically. Conclude: "You can now use `/plan` to generate a detailed implementation plan based on this brief. Would you like me to start that for you?"

**Required Markdown output format:**

```markdown
## Design Brief

**Chosen approach:** [Approach letter + name, e.g., "Approach B — Event-sourced queue"]
**Why:** [Key tradeoff in 1-2 sentences; what this gains and what it costs]

**Scope:** [Which system/component this touches; what is explicitly out of scope]
**Constraints:** [Timeline, existing systems, compliance, tech stack limitations]
**Interface:** [How users or systems interact with this — input and output]

**Architecture:**

- [Component 1: responsibility]
- [Component 2: responsibility]
- [Key data flow between them]

**Acceptance criteria:**

- Given [context], when [action], then [observable result]
- [1–3 BDD scenarios; omit this section if Phase 3 Success Logic was not run]

**Risk register:**

| Risk                                      | Likelihood | Mitigation          |
| ----------------------------------------- | ---------- | ------------------- |
| [identified risk from Phase 3 or scanner] | H / M / L  | [mitigation action] |

**First step:** [One concrete action to begin — a file to open, a test to write, an interface to define]
**Open TBDs:** [Unresolved items with owner and due date, or "None"]
```

**Required JSON output format (`design-brief.json`):**
Write this structure to `design-brief.json` to make inter-skill data extraction deterministic:

```json
{
  "chosen_approach": "Approach letter + name",
  "why": "Key tradeoff",
  "scope": "System/component touched",
  "constraints": ["Constraint 1", "Constraint 2"],
  "interface": "Input and output description",
  "architecture": ["Component 1: responsibility"],
  "acceptance_criteria": ["Given [context], when [action], then [observable result]"],
  "risks": [{ "risk": "Description", "likelihood": "H/M/L", "mitigation": "Action" }],
  "first_step": "Action",
  "open_tbds": ["Unresolved items"]
}
```

> **Downstream note:** The `planning` skill reads this brief directly. The **Scope**, **Constraints**, and **Interface** fields map to planning's intake fields of the same name — planning will skip its interview questions for any field already answered here.

## Command Usage & Troubleshooting

**When to use:**

- Scope or approach is unclear before starting a feature.
- Domain terminology is ambiguous (e.g., "task", "session", "context").
- Multiple implementation approaches exist and the right one isn't decided.
- A stakeholder description needs to become concrete requirements.

Prefer `planning` skill when requirements are clear. Prefer direct implementation when requirements and approach are both decided.

**Troubleshooting:**

- **Skill returns with no questions** — Input is too narrow. Add context about the feature goal and rerun.
- **Requirements feel incomplete** — Ask to explore edge cases, failure modes, or "what should NOT happen."
- **Brainstorm diverges from goal** — Add a constraint upfront (e.g., "only changes within the hook layer, no new agents").
- **Success Criteria** — All ambiguous terms defined, scope boundaries clear, key design decisions documented with rationale, no open questions remain.
