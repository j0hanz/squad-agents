---
name: brainstorming
description: 'MANDATORY before initiating any creative work, including building features, adding functionality, or altering behavior. This skill should be used when the user asks to "design a feature", "add functionality", "write a design doc", or "brainstorm a new solution".'
---

# brainstorming

<HARD-GATE>
Do not propose code, file changes, or a concrete implementation plan for a new feature or ambiguous
request until Phase 6 produces an approved Design Brief. Sketching the approach in a doc is still
Phase 4 — it still needs Phase 1 Discovery first. Does not apply to bug fixes, typos, or one-line
config changes with no design space.
</HARD-GATE>

**"This is trivial to need discovery"** is the rationalization that defeats this skill most often:
a request that looks trivial can still hide unstated stakeholders, terminology conflicts, or existing
analogous code that Phase 1 would have surfaced. If a request truly has zero ambiguity and one obvious
implementation, say so explicitly and name which step (Stakeholder Probe, Codebase Scan, Understanding
Statement) is skipped and why — never skip silently.

Default subagent type for every dispatch below: `general-purpose`. Type is only called out where it differs.

## Process Flow

```
0. Resume Check
  -- no match -------> 1. Discovery
  -- resume at 2 -----> 2. Domain Clarity
  -- resume at 3 -----> 3. Expert Clarification
  -- resume at 4 -----> 4. Design Proposal
  -- resume at 5 -----> 5. Structured Review

1. Discovery
  -- ambiguous terms -------> 2. Domain Clarity
  -- needs clarification ---> 3. Expert Clarification
  -- scope S, no unknowns ---> 4. Design Proposal

2. Domain Clarity -> 3. Expert Clarification -> 4. Design Proposal

4. Design Proposal
  -- flagged: scope L/XL, high risk, or attack surface --> 5. Structured Review
  -- not flagged -----------------------------------------> 6. Design Brief

5. Structured Review
  -- approved -----> 6. Design Brief
  -- rejected -----> back to 4. Design Proposal
  -- revise (loop) -> back to 5. Structured Review
```

## Phase 0: Resume Check

- **Pre-Check:** Glob `.brainstorm/*.memlog.md` matching `topic:`. No match → Phase 1.
- **Match Found:** Read file. Reconstruct phase, Understanding Statement, glossary, Phase 5 flag/reason, approach, pending log rows, and pending reviewers.
- **User Prompt:** "Resuming '[topic]'. Left off at [phase], with [state]." Options: Continue, Restart, Abandon.
- **Action Continue:** Resume at first incomplete phase. Re-dispatch ONLY pending reviewers.
- **Action Restart:** Rename old log to `.bak-<timestamp>`. Start Phase 1.
- **Action Abandon:** Update frontmatter `status: abandoned`. Stop.
- **Log Discipline:** Create `.brainstorm/<topic-slug>.memlog.md` post-Phase 1. Append entries and update `phase`/`status`/`updated` frontmatter upon phase completion. Log Phase 5 reviewers individually upon return. Set `status: done` post-Phase 6.

---

## Phase 1: Discovery

- **Stakeholder Probe:** Identify users. Trigger `AskUserQuestion` (1. Recommended, 2. Alternative). Skip if unambiguous.
- **Scanner Subagent:** **MANDATORY - READ ENTIRE FILE**: Before dispatching, you MUST read [codebase-scanner-prompt.md](file:///C:/agent-dev/skills/brainstorming/references/codebase-scanner-prompt.md) completely. NEVER set range limits on reading this file. Do NOT load other reference files for this phase. Dispatch subagent (`scan_context.py` → `compress_report.py`). Fallback to regex on failure.
- **Extraction:** Interface Shapes, Technical Constraints, Analogous Features, Key Unknowns.
- **Zero-Code Exit:** Offer exit if scan finds existing satisfying feature/config.
- **Understanding Statement:** Summarize extraction. Require user confirmation.
- **Adaptive Routing:**
- Scope S + No Unknowns → Phase 4
- Scope XL → Offer sub-feature split
- Ambiguous Terms → Phase 2
- Scope L/XL or High Blast Radius → Set Phase 5 flag. Confirm with user.

- **Log Entry:** Append scope, stakeholder, statement, and Phase 5 flag.

---

## Phase 2: Domain Clarity

- **Action Define Term:** Batch max 4 ambiguous terms via `AskUserQuestion`. Supply Recommended vs Alternative definitions.
- **Persistence:** Append to `glossary.md` at root (create if missing). Do not use `CONTEXT.md` for terms.
- **Log Entry:** Append resolved terms and definitions.

---

## Phase 3: Expert Clarification

- **Action Techniques:** Select 1-2 techniques (max 4 questions): 5-Whys, Premortem, Success Logic, Anti-Scope, Trust Breach.
- **Trust Breach Result:** Finding concrete attack surface → Set Phase 5 flag.
- **Log Entry:** Append techniques and key answers.

---

## Creative Checkpoint (Pre-Design)

- **Evaluation:** Check for zero-code, analogous features, or a 10x simpler solution.
- **Proactive Filter:** Present zero-code/analogous solutions as "Approach A" in Phase 4.
- **Log Entry:** Append finding (or "none").

---

## Phase 4: Design Proposal

- **Designer Subagent:** **MANDATORY - READ ENTIRE FILE**: Before dispatching, you MUST read [design-proposer-prompt.md](file:///C:/agent-dev/skills/brainstorming/references/design-proposer-prompt.md) completely. NEVER set range limits on reading this file. Do NOT load other reference files for this phase. Dispatch subagent with compressed scan report + discovery findings.
- **Presentation:** 2-3 approaches with grounded tradeoffs.
- **Approval Gate:** Await explicit user commitment to one approach. Do not guess.
- **Review Check:** Phase 5 flag set → Phase 5. Not set → Phase 6.
- **Log Entry:** Append approaches and user choice.

---

## Phase 5: Structured Review

- **Trigger:** Phase 5 flag set OR explicit user request to stress test.
- **Parallel Dispatch:** **MANDATORY - READ ENTIRE FILE**: Before dispatching reviewers, you MUST read [structured-review-prompt.md](file:///C:/agent-dev/skills/brainstorming/references/structured-review-prompt.md) completely. NEVER set range limits on reading this file. Spawn Skeptic, Constraint Guardian, User Advocate concurrently.
- **Consolidation:** Create Response Log (Objection | Source | Severity | Designer Response | Resolution). Discard style/wording objections.
- **Resolution:** Accept & Revise (update design) OR Reject (provide technical rationale). No open rows allowed.
- **Arbiter Gate:** Dispatch Arbiter with original design, revised design, Response Log. Yields `APPROVED`, `REVISE`, or `REJECT`.
- **Exit Condition:** All reviewers invoked, Response Log complete, Arbiter `APPROVED`.
- **Log Entry:** Append reviewer objections (upon individual return), resolved rows, Arbiter disposition, and rationale.

---

## Phase 6: Transition

- **Brief Format:** `markdown-kv` containing: Chosen Approach, Why, Scope, Success Criteria, Constraints, Interface, Architecture, Risk Register, Review Disposition, First Step.
- **Persistence:** Write to `docs/design/YYYY-MM-DD-<topic>-design.md`. Present in chat first.
- **Commit Guard:** Ask before git commit. Default to NO. Skip if not a git repository.
- **Next Skills:** `planning`, `architecting`.
- **Log Entry:** Append final brief. Update frontmatter `status: done`.

---

## NEVER Do

- **Skip Discovery:** Execute Phase 1 regardless of "simple" or "just" descriptors.
- **Assume Terminology:** Always execute Phase 2 for ambiguities.
- **Capture HOW before WHAT:** Never skip Discovery before Design.
- **Self-Arbitrate:** Designer cannot evaluate its own design in Phase 5.
- **Accept Empty Rejections:** Arbiter requires rationale for rejected High-severity objections.
- **Ignore Constraints:** Phase 4 architecture must explicitly cite which Phase 1 constraints it satisfies.
- **Reviewer Redesign:** Phase 5 reviewers only identify flaws; Phase 4 handles redesign.
- **Re-dispatch Reviewers:** Never re-run a Phase 5 reviewer if objections are already logged in the session log.

---

## Additional Resources

### Reference Files

Consult these files for subagent prompt templates:

- **[codebase-scanner-prompt.md](file:///C:/agent-dev/skills/brainstorming/references/codebase-scanner-prompt.md)** - Prompts for scanning codebase and extracting domain context.
- **[design-proposer-prompt.md](file:///C:/agent-dev/skills/brainstorming/references/design-proposer-prompt.md)** - Prompts for creating 2-3 design approaches.
- **[structured-review-prompt.md](file:///C:/agent-dev/skills/brainstorming/references/structured-review-prompt.md)** - Prompts for Adversarial Review and Arbiter Gate.
