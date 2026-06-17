# Design Proposer Subagent Prompt

**purpose:** Phase 4 design synthesis — turn accumulated context into 2-3 concrete design approaches.
**when:** Start of Phase 4, before presenting approaches to the user.
**subagent_type:** `general-purpose`

---

## Dispatch Template

```text
SCOPE: No tools needed beyond reasoning over the supplied context packet — do not Read, Write, Edit,
  or run Bash/PowerShell.
OBJECTIVE: Generate 2-3 concrete design approaches with tradeoffs, an evidence-based recommendation,
  and a first implementation step per approach. No questions. No code. No information not present in
  the context packet below.
CONTEXT (the full context packet):
  Feature description: [confirmed in Phase 1]
  Stakeholder type: [from Phase 1 probe, or "not specified"]
  Codebase Context Report (compressed), including Analogous Features and Test Coverage: [paste]
  Domain terms: [from Phase 2, or "Phase 2 skipped"]
  Risks and success criteria: [from Phase 3, or "Phase 3 skipped"]
  Creative Checkpoint findings: [zero-code/adjacent-pattern candidate, if any]

CONSTRAINTS:
  - Reference only information in the context packet — never invent facts.
  - Step 0: check the Codebase Context Report's Analogous Features section before mapping the design
    space — if a similar feature exists, note whether reuse or inversion is viable as an "Extend
    existing" / "Mirror existing pattern" option.
  - Step 1: map the design space across axes of meaningful variation (build vs extend vs buy, sync vs
    async, centralized vs distributed, new abstraction vs reuse, simple+fast vs robust+complex,
    conventional vs unconventional).
  - Approaches must differ on real axes, not naming or minor implementation details — 2 minimum, 3 max.
  - Novelty mandate: at least one approach must explore a non-obvious, counterintuitive, or
    unconventional solution. The "obvious default" is allowed but not sufficient alone. If the Creative
    Checkpoint identified a zero-code or adjacent-pattern candidate, it must be a mandatory option.
  - YAGNI check: remove components not justified by a stated requirement or discovered constraint;
    flag them as "Deferred" instead of silently dropping them.
  - Recommendation must cite a specific constraint from the Codebase Context Report and the success
    criterion from Phase 3 it satisfies most directly — never generic best practice. Reference
    stakeholder type if it affects the call (e.g. end-user features prioritize latency; internal tools
    tolerate complexity).

OUTPUT:
  ## Design Proposals

  ### Approach A — [Short Name]
  **What:** [one sentence: core runtime mechanism]
  **Gains:** [specific benefit, grounded in context]
  **Costs:** [specific drawback or risk]
  **Fit:** [alignment with constraints, success criteria, stakeholder type]
  **First step:** [one concrete action to begin]

  ### Approach B — [Short Name]
  [same fields]

  ### Approach C — [Short Name] (omit if only 2 meaningful approaches exist)
  [same fields]

  ### Recommendation
  **Approach [X] — [Name]**
  [2-3 sentences citing specific evidence: constraint handled, success criterion met, scope/risk
  signal, stakeholder fit]

  **Deferred (YAGNI):** [features removed as unjustified, or "None"]
```
