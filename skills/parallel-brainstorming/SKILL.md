---
name: parallel-brainstorming
description: 'Use when requirements are vague or the solution space is open — before a plan exists and before touching code. Prefer over request-plan or project-audit when the problem is unproven and multiple distinct approaches need to be explored. Not for bug fixes or one-line changes with no design space.'
disable-model-invocation: false
allowed-tools: Skill(interview), Write, Bash(python *), Read, Grep, Glob
---

# parallel-brainstorming

<HARD-GATE>
Do not propose code, file changes, or a concrete implementation plan for a new feature or ambiguous
request until Phase 6 produces an approved Design Brief. Sketching the approach in a doc is still
design work — it still needs Phase 1 Discovery first. Does not apply to bug fixes, typos, or one-line
config changes with no design space.
</HARD-GATE>

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

- **No Silent Skips:** If a task needs zero discovery, name the exact step skipped (Probe, Scan, or Understanding Lock) and explain why — never skip silently.
- **Probe:** Identify target users; ask clarifying questions if the request is ambiguous.
- **Scan:** Run `python ${CLAUDE_SKILL_DIR}/scripts/scan_context.py '<nouns>' --cwd '<root>' | python ${CLAUDE_SKILL_DIR}/scripts/compress_report.py` (fallback to `Grep` if it fails).
- **Report:** Extract Related Files (with recent commits and test coverage), Interface Shapes, Design Docs, Analogous Features, Constraints, Scope (S/M/L/XL) with reasoning, and Unknowns.
- **Zero-Code Check:** Stop and offer exit if existing code/config already solves this.
- **Understanding Lock:** Summarize the problem and your understanding. Only invoke `interview` if you have genuine doubts; otherwise proceed directly to Phase 3.
- **Routing:**
- Scope XL → Offer to break it down.
- Ambiguous → Go to Phase 2.
- High Risk / Scope L+ → Set Phase 5 Flag.

**Done when:** a Context Report lists Related Files, Interface Shapes, Design Docs, Analogous Features, Constraints, Scope (S/M/L/XL), and Unknowns, and the zero-code check has been answered.

## Phase 2: Clarification

- **Resolve via `interview`:** hand the ambiguous terms to `interview` (max 4 per batch) — it already enforces one-at-a-time, two-option questioning, so do not hand-roll a question loop.
- **Glossary:** Save resolved definitions to `glossary.md` (never `CONTEXT.md`).
- **Visuals:** Offer a diagram only if layout or data flow requires it. Wait for a reply.

**Done when:** ambiguous terms are resolved via `interview` (max 4 per batch) and saved to `glossary.md`.

## Creative Checkpoint (Pre-Ideation)

- **Evaluate:** Look for a 10x simpler or zero-code solution.
- **Seed:** If found, use it as "Approach A" (Minimalist lane) in Phase 3.

**Done when:** a 10x/zero-code candidate is seeded as Approach A, or you've confirmed none exists and are proceeding to Phase 3 unseeded.

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

**Done when:** 2-3 distinct approaches are generated in one response, each with idea, core mechanism, winning factor, key risk, and first step.

## Phase 4: Convergence & Synthesis

- **Synthesize:** Group similar ideas. Combine strong mechanisms with risk-mitigations from other lanes.
- **Distill:** Present 2-3 distinct approaches. Approach A must be Minimalist. For each: What, Gains, Costs, Fit, First Step.
- **Approval Lock:** Hand the 2-3 distilled approaches to `interview` to lock one — this is the hard-to-reverse decision that commits Phase 6's Design Brief. **Await its resolved decision. Do not guess.**
- **Routing:** If Phase 5 flag is set → Phase 5. Otherwise → Phase 6.

**Done when:** `interview` returns a resolved decision locking one of the 2-3 distilled approaches (not guessed).

## Phase 5: Persona Critique

- **Trigger:** Phase 5 flag is set, or user requested a stress test.
- **Simulated Review:** Adopt 3 personas in your thought process to evaluate the chosen design:

1. _Skeptic:_ Finds edge cases and failure modes.
2. _Constraint Guardian:_ Enforces scale, performance, and security rules.
3. _User Advocate:_ Evaluates usability and cognitive load.

- **Severity Rating:** High (Blocks deployment), Med (Worse outcome), Low (Minor). Ignore styling/naming.
- **Resolution:** Record objections. For all High/Med issues, you must "Accept & Revise" or "Reject with technical rationale."
- **Self-Arbitration:** Resolve any debates yourself. Mark the design `APPROVED`, `REVISE`, or `REJECT`.

**Done when:** every High/Med objection is "Accept & Revise" or "Reject with technical rationale", and the design is marked `APPROVED`, `REVISE`, or `REJECT`.

## Phase 6: Design Brief

- **Self-Review:** Fix any contradictions or scope creep in the chosen design before writing.
- **Format:** Write a strict `markdown-kv` brief containing: Approach, Why, Scope, Constraints, Interface, Architecture, Risks, First Step.
- **Save:** Present in chat, then write to `docs/design/YYYY-MM-DD-<topic>-design.md`.
- **Commit Guard:** Do not commit. If the user wants to commit only (no push), hand off to `write-commit`. If the user wants to commit, push, and open a PR, hand off to `pr-workflow`.

**Done when:** the markdown-kv Design Brief (Approach, Why, Scope, Constraints, Interface, Architecture, Risks, First Step) is written to `docs/design/YYYY-MM-DD-<topic>-design.md`.

## Worked Example

Request: "add a way for users to save and re-run searches."

1. **Phase 1:** Scan finds an existing `Filter` model and a one-off "recent searches" list in `localStorage`. Scope: M. No flag (not high-risk, not L/XL).
2. **Creative Checkpoint:** Minimalist seed found — extend `Filter` with a `name` + `saved: boolean` column instead of a new table.
3. **Phase 3 (Multi-lane generation):** Conventional — new `SavedSearch` table + CRUD API, mirrors `Bookmark` feature. Minimalist — reuse `Filter` + 2 columns, no new endpoints (piggyback on existing filter-list endpoint). Constraint-First — same as Minimalist but adds a per-user cap (20 saved searches) to bound query cost.
4. **Phase 4:** Synthesize 2 approaches — Approach A (Minimalist + cap, cheapest) and Approach B (Conventional, more flexible but a new table + endpoints). User picks A. Not flagged → skip Phase 5.
5. **Phase 6:** Design Brief written to `docs/design/2026-06-29-saved-searches-design.md`: Approach (extend `Filter`), Why (reuses existing model, smallest diff), Scope (M), Constraints (cap 20/user), Interface (`Filter.saved`, `Filter.name`), Architecture (no new table), Risks (cap needs a migration default), First Step (`ALTER TABLE filters ADD COLUMN saved boolean DEFAULT false`).
6. Commit Guard: user declines auto-commit → brief left in chat + on disk; handoff to `request-plan` to formalize tasks.

## STRICT RULES (NEVER DO)

- **Blend Ideation:** Keep Phase 3 perspectives distinct; do not bleed them into each other until Phase 4 synthesis.
- **Ship Raw Ideas:** Phase 4 synthesis is mandatory. Never present raw brainstormed ideas as the final answer.
- **Accept Empty Rejections:** Require a technical reason for any rejected High-severity issue during Phase 5 critique.
- **Use Subagents for Ideation:** Do not use `invoke_subagent` for Phase 3 or 5. Do it yourself to save tokens and time.

## Next Skills

- `write-commit`: commit the Design Brief only (no push).
- `pr-workflow`: commit, push, and open a PR for the Design Brief.
- `request-plan`: formalize the Design Brief into a task plan when auto-commit is declined.
- `dispatch-agents`: execute the resulting plan once tasks are formalized.
