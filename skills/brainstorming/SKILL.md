---
name: brainstorming
description: Structured requirements discovery before implementation. Trigger on feature building, ambiguous design, or unclear terminology. Prevents rework by catching problems early.
---

## When to Apply

Use this whenever the user says "let's build X", "add a feature", "we need a new Y", "I want to implement Z", or describes a new component or behavior — even if they don't explicitly ask for brainstorming or say "just build it". Proactively offer a quick brainstorm before any implementation begins.

Also use when: domain terminology is ambiguous, foundational assumptions need validation, or the user is unsure how to approach a design problem.

Skip only for: bug fixes with a clearly defined problem, pure refactors with no behavior change, documentation-only updates, or when a design has already been explicitly approved and implementation is the next step.

# Brainstorming

## Conversation Rhythm

Ask **one question at a time** throughout all phases — wait for each answer before asking the next. This prevents the user from feeling interrogated and gives you better signal per question.

## Do Not

- **Ask leading questions** (e.g., "So this is a caching layer, right?") — LLMs tend to confirm user bias. Let the user define the domain.
- **Assume two terms mean the same thing** — inventory ALL contexts before drilling into any one.
- **Capture implementation details** (e.g., "Stored in Redis") during discovery — capture WHAT a concept IS, not HOW it is built. Implementation locked in prematurely becomes expensive to unwind.
- **Write code or scaffolding before design is approved** — assumptions embedded in code are 10x more expensive to fix than those in a spec. Keep all decisions in plain language until the user commits to an approach.

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

## Phase 1: Discovery (Read Before Asking)

**Discovery checklist — complete before asking questions:**
1. **Code patterns** — Find 3-5 files related to this area; grep for related functions/classes
2. **Recent history** — Check `git log --oneline -20` on affected files; what changed recently?
3. **Existing glossaries** — Search for `glossary.md`, `CONTEXT.md`, `docs/glossary/`, `docs/terminology/`
4. **Documentation** — Skim relevant README, ADR, or design docs for context
5. **Known constraints** — Note performance limits, API contracts, or technical debt mentioned in code

**Then, state your understanding:**
Summarize your understanding of the task in one paragraph and ask the user to confirm. Include what you've found and what you DON'T know yet.

**Scope reality check:** If discovery reveals the feature is >4x larger than initially expected, suggest splitting into phases. Example: "This dashboard includes 5 major areas. Should we start with user management and add reporting later?"

**Domain trigger:** If steps 1–5 reveal ambiguous or conflicting terminology, run Phase 2 before continuing.

### Phase 1 Example

**User says:** "We need to add search to our product."

**Your understanding statement:**
"I understand you need full-text search for your product so users can find data faster. Currently, I don't know: if you want real-time indexing, if search needs to be fuzzy, or if there are performance constraints. Do I have this right?"

✓ This invites confirmation
✓ This surfaces unknowns without asking leading questions
✓ This summarizes in one paragraph

## Phase 2: Domain Clarity (When Terminology is Ambiguous)

**Skip this phase** if domain terminology is clear and consistent throughout code, docs, and user language.

**Definition is clear when:**
- ✓ User can explain WHAT the concept IS (not just what it does)
- ✓ User can explain how it differs from similar terms (Account vs Organization vs Customer)
- ✓ User can point to where it appears in code/docs/conversations

**Not clear if:** Definition relies on "everyone knows what this means" or varies by team.

**Invoke when:** same term has multiple meanings, team and code use different names for the same concept, user asks "what do we call X?", or docs are inconsistent.

**Fundamental disagreement:** If discovery reveals domain experts disagree on WHAT we're building (not just terminology), document both positions and escalate to the user before proceeding to Phase 4. Example: "The API team wants caching, the product team wants fresh data always. Which takes priority?"

For each ambiguous term:

1. Ask the user to define it in their own words — never lead with a definition.
2. Ask where it appears: code, docs, team discussions?
3. If two teams have valid reasons for different terms (e.g., "Account" vs "Tenant"): document both with a boundary — where each is appropriate and how they map — don't force one side to abandon their mental model.

**3-turn rule:** If 3 questions fail to define a term clearly, mark it TBD with an owner and move on.

**Output format for captured terms (document inline as you go):**

```
[Canonical Term]: [Definition]. Aliases: [alias1, alias2]
(TBD: [Question] — Owner: [Role/Person])
Conflict resolution: [how overlapping usages were resolved]
```

Offer to write findings to `glossary.md` or `CONTEXT.md` at Phase 5 transition.

## Phase 3: Expert Clarification (Surface the Unsaid)

**Technique selection** — use 1-2 based on what the conversation reveals:

| Situation | Use This | Reason |
|-----------|----------|--------|
| User says "just build it" or requirements seem obvious | **Why (Five Whys)** | Uncovers hidden motivation |
| Large scope or complex dependencies | **Premortem** | Surfaces organizational/technical risks |
| Success criteria vague ("just make it fast") | **Success Logic** | Clarifies acceptance criteria |
| Feature creep risk or unclear boundaries | **Anti-Scope** | Defines what we're explicitly NOT building |

Avoid the "checklist trap" — don't run all four techniques as a script. Pick 1-2 based on signals from discovery.

**Depth check:** After 1-2 techniques, ask: "Are there other risks or unknowns that could derail this?"
- Yes → apply one more technique, then move on regardless
- No → document TBD items and proceed to Phase 4

**Hard limit: 4 questions total within Phase 3** across all techniques. Unresolved questions become TBD items with an owner — don't loop indefinitely.

1. **The "Why" (Five Whys):** Drill down to the root problem. "Why is this needed *now*? What fails if we don't do this?"
2. **The Premortem:** "Imagine we've implemented this and it's a disaster. What's the most likely thing that went wrong?" (Surfaces hidden technical or organizational risks.)
3. **Success Logic:** "How will we know this is a success without using the word 'functional'? What behavior change should we see in users or the system?"
4. **The "Anti-Scope":** Instead of asking "what's out of scope," ask: "What's a related feature that we are *strictly* choosing NOT to build today?"

## Phase 4: Design Proposal

Propose 2-3 approaches. For each:

- One-line name and description
- Key trade-offs (what it gains, what it costs)
- Your recommendation with reasoning

Apply YAGNI: remove any feature not justified by a stated requirement.

Present the design in sections. Validate each section before continuing to the next.

**Design approval gate:**
Before moving to Phase 5, ask explicitly: "Which approach should we move forward with and why?"

Wait for a clear commitment like:
- "We'll go with Approach B because..."
- "Let's do Option 1, here's why..."
- "The second option aligns best with..."

Ambiguous responses ("sounds good") → loop back and clarify which specific approach they're choosing.

## Phase 5: Transition

When the user approves a design:

1. Summarize the approved approach in one short paragraph including the chosen option and key tradeoffs.
2. If terminology was captured in Phase 2: offer to write findings to `glossary.md` or `CONTEXT.md` now (before moving on).
3. **Design handoff:** Document the approved design as your implementation brief with:
   - **The chosen approach** (which of the 2-3 options)
   - **Why this approach** (key tradeoffs and reasoning)
   - **Architecture summary** (key components, data flows)
   - **Success criteria** (how you'll know it worked)

   Produce this brief as your final output and stop — do not invoke `/plan` or write any code automatically. The user decides what to do next. If they want to proceed to planning, they can invoke `/plan` themselves or ask you to do so explicitly.
