---
name: parallel-brainstorming
description: 'Use when requirements are vague or the solution space is open — before a plan exists and before touching code. Prefer over request-plan or project-audit when the problem is unproven and multiple distinct approaches need to be explored. Not for bug fixes or one-line changes with no design space.'
disable-model-invocation: false
allowed-tools: Agent(researcher), Skill(interview), Write, Bash(python *)
---

# parallel-brainstorming

<HARD-GATE>
Do not propose code, file changes, or a concrete implementation plan for a new feature or ambiguous
request until Phase 6 produces an approved Design Brief. Sketching the approach in a doc is still
design work — it still needs Phase 1 Discovery first. Does not apply to bug fixes, typos, or one-line
config changes with no design space.
</HARD-GATE>

**1. NEVER SKIP DISCOVERY SILENTLY**
Do not skip discovery just because a task looks easy. If a task needs zero discovery, you MUST name the exact step skipped (Stakeholder Probe, Codebase Scan, or Understanding Statement) and explain why.

**2. WORKFLOW RULES**

- **Internal Brainstorming:** Generate multiple divergent ideas in a single shot using structured internal thinking to simulate different perspectives.
- **Internal Critique:** Review ideas by adopting multiple personas (e.g., Skeptic, Guardian, Advocate) sequentially within the same context.
- **Synthesis:** Combine ideas and make final decisions yourself without needing to spawn subagents.

**3. STRICT ROLES (SIMULATED)**
Adopt these roles within your thought process:

- **Phase 3 Lenses:** Brainstorm from distinct angles (Minimalist, Conventional, Radical).
- **Phase 5 Reviewers (Skeptic, Guardian, Advocate):** Find flaws in the synthesized design.

**4. DISPATCH SETTINGS**

- **Code Scans:** Run the provided python scripts directly.
- **Parallel Work:** Do NOT use subagents. Use single-shot multi-lane ideation (generating multiple perspectives in one response) to save time and tokens.

## Process Flow

```
1. Framing & Discovery
  -- zero-code/config solves it --> STOP (offer exit)
  -- scope XL -------------> offer subsystem split, then continue
  -- ambiguous terms ------> 2. Clarification
  -- clear + scoped -------> Creative Checkpoint

2. Clarification ----------> Creative Checkpoint

Creative Checkpoint
  -- zero-code / analogous / 10x found -> seeds Minimalist lane -> 3
  -- none ---------------------------------------------------- -> 3

3. Multi-Lane Ideation (Single-shot, distinct perspectives)
  ------------------------------------------------------------> 4. Convergence & Synthesis

4. Convergence & Synthesis
  -- approved approach + flagged (L/XL, high risk, attack surface) --> 5. Persona Critique
  -- approved approach + not flagged -------------------------------> 6. Design Brief

5. Persona Critique (Skeptic | Constraint Guardian | User Advocate)
  -- APPROVED -------------> 6. Design Brief
  -- REVISE ---------------> back to 4 (re-synthesize)
  -- REJECT ---------------> back to 3 (re-ideate)
```

## Phase 1: Framing & Discovery

- **Probe:** Identify target users. Ask clarifying questions if the request is ambiguous.
- **Scan:** Run `python C:/agent-dev/skills/parallel-brainstorming/scripts/scan_context.py -- '<nouns>' --cwd '<root>' | python C:/agent-dev/skills/parallel-brainstorming/scripts/compress_report.py` (fallback to `grep_search` if it fails).
- **Report:** Extract Related Files, Recent Changes, Terms, Interfaces, Constraints, Scope (S/M/L/XL), and Unknowns.
- **Zero-Code Check:** Stop and offer exit if existing code/config already solves this.
- **Understanding Lock:** Summarize the problem and your understanding. Only invoke `interview` if you have genuine doubts. Otherwise, proceed directly to Phase 3.
- **Routing:**
- Scope XL → Offer to break it down.
- Ambiguous → Go to Phase 2.
- High Risk / Scope L+ → Set Phase 5 Flag.

## Phase 2: Clarification

- **Resolve via `interview`:** hand the ambiguous terms to `interview` (max 4 per batch) rather than hand-rolling a question loop — it already enforces one-at-a-time, two-option questioning.
- **Glossary:** Save the resolved definitions to `glossary.md` (never `CONTEXT.md`).
- **Visuals:** Offer a diagram _only_ if layout or data flow requires it. Wait for a reply.

## Creative Checkpoint (Pre-Ideation)

- **Evaluate:** Look for a 10x simpler or zero-code solution.
- **Seed:** If found, use this as "Approach A" (Minimalist lane) in Phase 3.

## Phase 3: Multi-Lane Divergent Ideation

- **Single-Shot Generation:** Generate 2-3 distinct approaches in one response. **Do not spawn subagents.**
- **Context:** Use the feature description and Context Report to inform all perspectives.
- **Lenses (Assign 1 per agent):**

1. _Conventional:_ Use existing codebase patterns.
2. _Radical:_ Best outcome, ignoring legacy constraints.
3. _Minimalist:_ Smallest working change (Seeded by Checkpoint).
4. _Constraint-First:_ Optimize for the hardest non-functional constraint (e.g., speed, scale).
5. _Analogous:_ Copy and adapt a similar existing feature.

- **Output (Per Agent):** Idea, core mechanism, winning factor, key risk, first step.

## Phase 4: Convergence & Synthesis

- **Synthesize:** Group similar ideas. Combine strong mechanisms with risk-mitigations from other lanes.
- **Distill:** Present 2-3 distinct approaches. Approach A must be Minimalist. For each, include: What, Gains, Costs, Fit, First Step.
- **Approval Lock:** Hand the 2-3 distilled approaches to `interview` to lock one — this is the hard-to-reverse decision that commits Phase 6's Design Brief. **Await its resolved decision. Do not guess.**
- **Routing:** If Phase 5 flag is set → Phase 5. Otherwise → Phase 6.

## Phase 5: Persona Critique

- **Trigger:** Phase 5 flag is set, or user requested a stress test.
- **Simulated Review:** Adopt 3 personas in your thought process to evaluate the chosen design:

1. _Skeptic:_ Finds edge cases and failure modes.
2. _Constraint Guardian:_ Enforces scale, performance, and security rules.
3. _User Advocate:_ Evaluates usability and cognitive load.

- **Severity Rating:** High (Blocks deployment), Med (Worse outcome), Low (Minor). Ignore styling/naming.
- **Resolution:** Record objections. You must "Accept & Revise" or "Reject with technical rationale" for all High/Med issues.
- **Self-Arbitration:** Resolve any debates yourself. Decide whether the design is `APPROVED`, needs `REVISE`, or is `REJECT`.

## Phase 6: Design Brief

- **Self-Review:** Fix any contradictions or scope creep in the chosen design before writing.
- **Format:** Write a strict `markdown-kv` brief containing: Approach, Why, Scope, Constraints, Interface, Architecture, Risks, First Step.
- **Save:** Present in chat, then write to `docs/design/YYYY-MM-DD-<topic>-design.md`.
- **Commit Guard:** Do not commit. If the user wants to commit, hand off to `pr-workflow` or let them do it manually.

## Worked Example

Request: "add a way for users to save and re-run searches."

1. **Phase 1:** Scan finds an existing `Filter` model and a one-off "recent searches" list already in `localStorage`. Scope: M. No flag (not high-risk, not L/XL).
2. **Creative Checkpoint:** Minimalist seed found — extend the existing `Filter` model with a `name` + `saved: boolean` column instead of a new table.
3. **Phase 3 (Multi-lane generation):** Conventional — new `SavedSearch` table + CRUD API, mirrors existing `Bookmark` feature. Minimalist — reuse `Filter` + 2 columns, no new endpoints (piggyback on existing filter-list endpoint). Constraint-First — same as Minimalist but adds a per-user cap (20 saved searches) to bound query cost.
4. **Phase 4:** Synthesize 2 approaches — Approach A (Minimalist + cap, cheapest) and Approach B (Conventional, more flexible but a new table + endpoints). User picks Approach A. Not flagged for L/XL or high risk → skip Phase 5.
5. **Phase 6:** Design Brief written to `docs/design/2026-06-29-saved-searches-design.md`: Approach (extend `Filter`), Why (reuses existing model, smallest diff), Scope (M), Constraints (cap 20/user), Interface (`Filter.saved`, `Filter.name`), Architecture (no new table), Risks (cap needs a migration default), First Step (`ALTER TABLE filters ADD COLUMN saved boolean DEFAULT false`).
6. Commit Guard: user declines auto-commit → brief left in chat + on disk; handoff to `request-plan` to formalize tasks.

## STRICT RULES (NEVER DO)

- **Blend Ideation:** Keep your generated Phase 3 perspectives distinct and avoid bleeding them into each other until Phase 4 synthesis.
- **Ship Raw Ideas:** Phase 4 synthesis is mandatory. Never present raw brainstormed ideas as the final answer.
- **Accept Empty Rejections:** Require a technical reason for any rejected High-severity issue during Phase 5 critique.
- **Use Subagents for Ideation:** Do not use `invoke_subagent` for Phase 3 or 5. Do it yourself to save tokens and time.
