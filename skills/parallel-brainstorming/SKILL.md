---
name: parallel-brainstorming
description: "Multi-agent parallel brainstorming for discovery and solution design. Fans out independent ideator agents that generate candidate approaches simultaneously — not sequentially — to maximize diversity and defeat anchoring, groupthink, and dominant-voice bias, then converges them into 2-3 grounded approaches, runs parallel critique lanes (Skeptic, Constraint Guardian, User Advocate) plus an Arbiter, and writes a markdown-kv Design Brief in docs/design/. Trigger on: 'parallel brainstorming', 'brainstorm a solution', 'design a feature', 'add a feature', 'explore approaches', 'generate options', 'multi-agent design', 'write a design doc', 'requirements discovery', 'build a new feature'. Also triggers when requirements are vague, when you want many distinct options instead of one, or when a request hides unstated stakeholders or terminology. Prefer over request-plan or architecting when the solution space is still open and unproven. Not for bug fixes, typos, or one-line config changes with no design space."
---

# parallel-brainstorming

<HARD-GATE>
Do not propose code, file changes, or a concrete implementation plan for a new feature or ambiguous
request until Phase 6 produces an approved Design Brief. Sketching the approach in a doc is still
design work — it still needs Phase 1 Discovery first. Does not apply to bug fixes, typos, or one-line
config changes with no design space.
</HARD-GATE>

**"This is trivial to need discovery"** is the rationalization that defeats this skill most often:
a request that looks trivial can still hide unstated stakeholders, terminology conflicts, or existing
analogous code that Phase 1 would have surfaced. If a request truly has zero ambiguity and one obvious
implementation, say so explicitly and name which step (Stakeholder Probe, Codebase Scan, Understanding
Statement) is skipped and why — never skip silently.

**Operating principle:** _Creativity is distributed, then converged; critique is distributed, then
arbitrated._ The front half fans ideation out across independent agents so no single line of thinking
dominates (more diverse options); the back half fans critique out across scoped reviewers so no single
reviewer's bias decides. Convergence and arbitration gates exist to prevent **idea-swarm chaos** (N
agents, no synthesis) and **hallucinated consensus** (agents agreeing because they anchored on each
other, not because the design is sound).

**Agent roster.** Ideators (Phase 3, distributed creativity) · Synthesizer (Phase 4, convergence) ·
Skeptic / Constraint Guardian / User Advocate (Phase 5, distributed critique) · Arbiter (Phase 5,
resolution). Every dispatched agent is **read-only and scope-limited** — it may not exceed its mandate
(an Ideator does not critique; a reviewer does not redesign; the Arbiter does not invent objections).

Default subagent type for every dispatch below: `general-purpose`. Type is only called out where it
differs — for Researcher-role dispatches (codebase scans), prefer a more specific specialized agent
already in the user's roster per `../multi-agent-development/references/subagent-contract.md`'s Role
Vocabulary, falling back to `general-purpose` when none matches. Parallel fan-outs (Phases 3 and 5) run
through the sibling `multi-agent-dispatch` skill.

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

3. Parallel Divergent Ideation  (fan out N independent ideators)
  ------------------------------------------------------------> 4. Convergence & Synthesis

4. Convergence & Synthesis
  -- approved approach + flagged (L/XL, high risk, attack surface) --> 5. Parallel Critique
  -- approved approach + not flagged -------------------------------> 6. Design Brief

5. Parallel Critique  (Skeptic | Constraint Guardian | User Advocate) + Arbiter
  -- APPROVED -------------> 6. Design Brief
  -- REVISE ---------------> back to 4 (re-synthesize)
  -- REJECT ---------------> back to 3 (re-ideate)
```

## Phase 1: Framing & Discovery

- **Probe:** Identify target users. Ask clarifying questions if the request is ambiguous.
- **Scan:** Run `python scripts/scan_context.py -- '<nouns>' --cwd '<root>' | python scripts/compress_report.py` (fallback to `grep` if it fails).
- **Report:** Extract Related Files, Recent Changes, Terms, Interfaces, Constraints, Scope (S/M/L/XL), and Unknowns.
- **Zero-Code Check:** Stop and offer exit if existing code/config already solves this.
- **Understanding Lock:** Summarize the problem. **Require explicit user confirmation** before generating any ideas.
- **Routing:**
- Scope XL → Offer to break it down.
- Ambiguous → Go to Phase 2.
- High Risk / Scope L+ → Set Phase 5 Flag.

---

## Phase 2: Clarification

- **Sequential Questions:** Ask one question at a time. Use multiple-choice instead of open-ended when possible.
- **Glossary:** Batch max 4 ambiguous terms. Save definitions to `glossary.md` (never `CONTEXT.md`).
- **Visuals:** Offer a diagram _only_ if layout or data flow requires it. Wait for a reply.

---

## Creative Checkpoint (Pre-Ideation)

- **Evaluate:** Look for a 10x simpler or zero-code solution.
- **Seed:** If found, use this as "Approach A" (Minimalist lane) in Phase 3.

---

## Phase 3: Parallel Divergent Ideation

- **Parallel Dispatch:** Run 2-5 independent reasoning agents. **They must not see each other's output.**
- **Context:** Give all agents the exact same feature description and Context Report.
- **Lenses (Assign 1 per agent):**

1. _Conventional:_ Use existing codebase patterns.
2. _Radical:_ Best outcome, ignoring legacy constraints.
3. _Minimalist:_ Smallest working change (Seeded by Checkpoint).
4. _Constraint-First:_ Optimize for the hardest non-functional constraint (e.g., speed, scale).
5. _Analogous:_ Copy and adapt a similar existing feature.

- **Output (Per Agent):** Idea, core mechanism, winning factor, key risk, first step.

---

## Phase 4: Convergence & Synthesis

- **Synthesize:** Group similar ideas. Combine strong mechanisms with risk-mitigations from other lanes.
- **Distill:** Present 2-3 distinct approaches. Approach A must be Minimalist. For each, include: What, Gains, Costs, Fit, First Step.
- **Approval Lock:** Ask the user to choose one approach. **Await explicit user choice. Do not guess.**
- **Routing:** If Phase 5 flag is set → Phase 5. Otherwise → Phase 6.

---

## Phase 5: Parallel Critique

- **Trigger:** Phase 5 flag is set, or user requested a stress test.
- **Parallel Review:** Dispatch 3 blind, read-only agents:

1. _Skeptic:_ Finds edge cases and failure modes.
2. _Constraint Guardian:_ Enforces scale, performance, and security rules.
3. _User Advocate:_ Evaluates usability and cognitive load.

- **Severity Rating:** High (Blocks deployment), Med (Worse outcome), Low (Minor). Ignore styling/naming.
- **Resolution:** Record objections. You must "Accept & Revise" or "Reject with technical rationale" for all High/Med issues.
- **Arbiter Gate:** A final, independent agent reviews resolutions. Returns `APPROVED`, `REVISE`, or `REJECT`.

---

## Phase 6: Design Brief

- **Self-Review:** Fix any contradictions or scope creep in the chosen design before writing.
- **Format:** Write a strict `markdown-kv` brief containing: Approach, Why, Scope, Constraints, Interface, Architecture, Risks, First Step.
- **Save:** Present in chat, then write to `docs/design/YYYY-MM-DD-<topic>-design.md`.
- **Commit Guard:** Ask before running git commit. Default to NO.

---

## STRICT RULES (NEVER DO)

- **Skip Discovery:** Phase 1 is mandatory for every request.
- **Ideate Unconfirmed:** Never brainstorm before the user confirms the Understanding Lock.
- **Cross-Talk:** Phase 3 agents must remain blind to each other to prevent bias.
- **Ship Raw Ideas:** Phase 4 synthesis is mandatory. Never present raw swarm ideas as the final answer.
- **Self-Arbitrate:** You cannot review your own design in Phase 5.
- **Accept Empty Rejections:** Arbiter requires a technical reason for any rejected High-severity issue.
- **Re-dispatch:** Never re-run an agent whose output you already have.
