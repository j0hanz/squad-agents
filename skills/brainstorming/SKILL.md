---
name: brainstorming
description: |
  Use BEFORE implementing any new feature, component, or significant behavior change. Explores user intent, requirements, and design constraints through structured discovery. Also use when: domain terminology is ambiguous, terminology alignment is needed, or foundational assumptions need validation.

  SKIP brainstorming for: bug fixes (clear problem), refactors with no behavior change, documentation updates, or when design is already approved.
disable-model-invocation: true
---

# Brainstorming

## NEVER

- **Ask leading questions** (e.g., "So this is a caching layer, right?") because LLMs tend to confirm user bias rather than explore truth. Let the user define the domain.
- **Assume two terms mean the same thing** — inventory ALL contexts before drilling into any one.
- **Capture implementation details** (e.g., "Stored in Redis") during discovery. Capture WHAT a concept IS, not HOW it is built.
- **Write code or scaffolding** until the design is approved. Assumptions made in code are 10x more expensive to fix than those in a spec.

## Red Flags

| Thought                              | Reality                                                   |
| ------------------------------------ | --------------------------------------------------------- |
| "The requirements are obvious"       | Assumptions cause rework. Clarify anyway.                 |
| "I'll start simple and iterate"      | HARD-GATE applies. Get design approval first.             |
| "We can figure out edge cases later" | Edge cases belong in the spec, not the debugger.          |
| "This is too small to need design"   | Small features accumulate into large regrets.             |
| "The user said just build it"        | Offer a 10-minute brainstorm first. User can decline.     |
| "Everyone knows what X means"        | Ambiguous terms corrupt specs. Capture them in Phase 2.   |
| "I'll define terms after we design"  | Terminology conflicts surface in specs at the worst time. |

**HARD-GATE: Do NOT write any code, scaffolding, or invoke any implementation skill until the user has approved a design.**

## Time Allocation

Discovery + terminology clarification should take **15-30 minutes**.
- Phase 1 (Discovery): 5-10 minutes
- Phase 2 (Domain Clarity, if needed): 5-10 minutes
- Phase 3 (Expert Clarification): 5-10 minutes

If exceeding 45 minutes, document remaining unknowns as TBD with an owner and move to Phase 4. Perfect discovery is expensive; a good-enough design beats no design.

## Phase 1: Discovery (Read Before Asking)

**Discovery Checklist — Complete before asking questions:**
1. **Code patterns** — Find 3-5 files related to this area; grep for related functions/classes
2. **Recent history** — Check `git log --oneline -20` on affected files; what changed recently?
3. **Existing glossaries** — Search for `glossary.md`, `CONTEXT.md`, `docs/glossary/`, `docs/terminology/`
4. **Documentation** — Skim relevant README, ADR, or design docs for context
5. **Known constraints** — Note performance limits, API contracts, or technical debt mentioned in code

**Then, State Your Understanding:**
Summarize your understanding of the task in one paragraph and ask the user to confirm. Include what you've found and what you DON'T know yet.

**Scope Reality Check:** If discovery reveals the feature is >4x larger than initially expected, suggest splitting into phases. Example: "This dashboard includes 5 major areas. Should we start with user management and add reporting later?"

**Domain Trigger**: If steps 1–5 reveal ambiguous or conflicting terminology, run Phase 2 before continuing.

### Phase 1 Example

**User says:** "We need to add search to our product."

**Your understanding statement:**
"I understand you need full-text search for your product so users can find data faster. Currently, I don't know: if you want real-time indexing, if search needs to be fuzzy, or if there are performance constraints. Do I have this right?"

✓ This invites confirmation
✓ This surfaces unknowns without asking leading questions
✓ This summarizes in one paragraph

## Phase 2: Domain Clarity (When Terminology is Ambiguous)

**Skip this phase** if domain terminology is clear and consistent throughout code, docs, and user language.

**Definition is Clear When:**
- ✓ User can explain WHAT the concept IS (not just what it does)
- ✓ User can explain how it differs from similar terms (Account vs Organization vs Customer)
- ✓ User can point to where it appears in code/docs/conversations

**NOT clear if:** Definition relies on "everyone knows what this means" or varies by team

**Invoke when:** same term has multiple meanings, team and code use different names for the same concept, user says "what do we call X?", or docs are inconsistent.

**Fundamental Disagreement:** If discovery reveals domain experts disagree on WHAT we're building (not just terminology), document both positions and escalate decision to user before proceeding to Phase 4. Example: "The API team wants caching, the product team wants fresh data always. Which takes priority?"

**One question at a time — wait for each answer before asking the next.**

For each ambiguous term:

1. Ask the user to define it in their own words — never lead with a definition.
2. Ask where it appears: code, docs, team discussions?
3. If two teams have valid reasons for different terms (e.g., "Account" vs "Tenant"): document both with a boundary — where each is appropriate and how they map — don't force one side to abandon their mental model.

**Execution Rule:**

- **3-turn rule**: if 3 questions fail to define a term clearly, mark it TBD with an owner and move on.

**Output format for captured terms (document inline as you go):**

```
[Canonical Term]: [Definition]. Aliases: [alias1, alias2]
(TBD: [Question] — Owner: [Role/Person])
Conflict resolution: [how overlapping usages were resolved]
```

Offer to write findings to `glossary.md` or `CONTEXT.md` at Phase 5 transition.

## Phase 3: Expert Clarification (Surface the Unsaid)

**Technique Selection** — Use 1-2 based on what the conversation reveals:

| Situation | Use This | Reason |
|-----------|----------|--------|
| User says "just build it" or requirements seem obvious | **Why (Five Whys)** | Uncovers hidden motivation |
| Large scope or complex dependencies | **Premortem** | Surfaces organizational/technical risks |
| Success criteria vague ("just make it fast") | **Success Logic** | Clarifies acceptance criteria |
| Feature creep risk or unclear boundaries | **Anti-Scope** | Defines what we're explicitly NOT building |

Avoid the "checklist trap" — don't ask all four techniques as a script. Pick 1-2 based on signals from discovery. **Ask questions INDIVIDUALLY — wait for each answer before asking the next.**

**Depth Check:** After using 1-2 techniques, ask: "Are there other risks or unknowns that could derail this?"
- If yes → use another technique
- If no → document any TBD items and proceed to Phase 4

**Limit to 4 questions total across all techniques.** If critical questions remain unanswered after 4, document them as TBD and proceed to Phase 4.

1. **The "Why" (Five Whys)**: Drill down to the root problem. "Why is this needed _now_? What fails if we don't do this?"
2. **The Premortem**: Ask the user: "Imagine we've implemented this and it's a disaster. What's the most likely thing that went wrong?" (Surfaces hidden technical or organizational risks).
3. **Success Logic**: "How will we know this is a success without using the word 'functional'? What behavior change should we see in users or the system?"
4. **The "Anti-Scope"**: Instead of asking "what's out of scope," ask: "What's a related feature that we are _strictly_ choosing NOT to build today?"

## Phase 4: Design Proposal

Propose 2-3 approaches. For each:

- One-line name and description
- Key trade-offs (what it gains, what it costs)
- Your recommendation with reasoning

Apply YAGNI: remove any feature not justified by a stated requirement.

Present the design in sections. Validate each section before continuing to the next.

**Design Approval Gate:**
Before moving to Phase 5, ask the user explicitly: "Which approach should we move forward with and why?"

Wait for a clear commitment like:
- "We'll go with Approach B because..."
- "Let's do Option 1, here's why..."
- "The second option aligns best with..."

Ambiguous responses ("sounds good") → loop back and clarify which specific approach they're choosing.

## Phase 5: Transition

When the user approves a design:

1. Summarize the approved approach in one short paragraph including the chosen option and key tradeoffs.
2. If terminology was captured in Phase 2: offer to write findings to `glossary.md` or `CONTEXT.md` now (before moving on).
3. **DESIGN HANDOFF:** Document the approved design as your implementation brief with:
   - **The chosen approach** (which of the 2-3 options)
   - **Why this approach** (key tradeoffs and reasoning)
   - **Architecture summary** (key components, data flows)
   - **Success criteria** (how you'll know it worked)

   Pass this to `/plan` or your implementation team to move into detailed planning.

4. **TRANSITION GUARDS (post-approval, for the rest of this session):**
   - **Do NOT re-open discovery** once design is approved unless a fundamental technical blocker is found
   - **Do NOT backtrack** through requirements clarification — that costs more than accepting minor unknowns
   - **Do NOT write implementation code** in this session; hand off to planning/implementation

---

## Glossary

**YAGNI** (You Aren't Gonna Need It) — Don't add features, infrastructure, or complexity that isn't justified by stated requirements. Every feature you add has a maintenance cost.

**Premortem** — A technique where you imagine the feature shipped and failed catastrophically, then work backward to identify what went wrong. Surfaces hidden risks.

**Anti-Scope** — Explicitly defining what you are choosing NOT to build. Clarifies boundaries and prevents feature creep.

**Domain Clarity** — Having consistent terminology across team communication, code, and documentation. Prevents miscommunication bugs.

**Red Flags** — Thoughts that indicate you're rationalizing away discipline (e.g., "This is too small to need design," "Everyone knows what X means," "The requirements are obvious"). These signal time to slow down and follow the process.

**Hard-Gate** — A checkpoint that must be passed before proceeding. In brainstorming, the hard-gate is design approval before implementation.

**Transition Guard** — Rules to prevent backtracking once a design is approved. Respects that reopening discovery has a high cost in time and team energy.
