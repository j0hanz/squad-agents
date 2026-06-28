Status: DRAFT

# Agent-SDLC Gap Specs

Requirements addressing 6 architecture gaps identified against `obra/superpowers`. Synthesized from three independent candidate drafts (conventional, minimalist, risk-first lenses); every REQ below extends a mechanism this repo already ships (the `skill-nudge.sh`/`lib.sh` cooldown-state pattern, `context-optimizer`'s rolling-summary file, `subagent-contract.md`'s field schema, the `references/` convention, per-skill "Next Skills" sections) rather than inventing a new file format, directory, or runtime mechanism — except where a requirement explicitly states new state is being introduced and justifies it (gap 1's mode flag, gap 3's ledger heading).

---

## Gap 1 — Forced session-start bootstrap

### REQ-001

`hooks/skill-nudge.sh` MUST inject orchestrator routing context into `additionalContext` on every SessionStart by default, framed as load-bearing (wrapped in an `<EXTREMELY_IMPORTANT>`-style tag) rather than an FYI aside — not gated by the existing 24h cooldown. The injected content MUST be both of the following, combined in one message, not one substituted for the other: (a) the 5 Gate 0-4 _category names_ from `skills/using-agent-sdlc-skills/SKILL.md`'s headings, and (b) the dynamically enumerated list of skill directories actually present under `skills/` (replacing the hardcoded 5-name `candidates=(...)` array at `skill-nudge.sh:35`). Not the full routing prose and not a Red-Flags rationalization table — the per-session token cost of full-text injection is not justified when gate names plus the existing gate matrix (consulted once the model is forced to check it) carry the same correction signal.

### REQ-002

A separate, explicit three-state flag, `AGENT_SDLC_BOOTSTRAP_MODE` (`full` | `cooldown` | `off`, default `full`), MUST gate the behavior in REQ-001: `off` exits immediately (today's fully-disabled behavior), `cooldown` runs the existing 24h-gated one-line nudge unmodified, `full` is the new unconditional gate-name-plus-skill-list injection. The existing `AGENT_SDLC_SKILL_NUDGE=0` env var and `skill_nudge: false` frontmatter flag MUST continue to work, mapped as aliases that force `AGENT_SDLC_BOOTSTRAP_MODE=off` regardless of any other setting — no breaking change to today's opt-out surface. This is the staged-rollback rung between "new forced behavior" and "fully disabled," justified specifically because `SessionStart` runs unconditionally for every installer on every session with zero per-user opt-in — the single highest blast-radius file touched by this entire gap list.

### REQ-003

Every new code path added to satisfy REQ-001/REQ-002 (directory scan, file read, mode branching) MUST preserve `skill-nudge.sh`'s existing invariant that a `lib.sh` sourcing failure or any internal error degrades to a silent no-op (`|| exit 0`), never propagates under `set -euo pipefail`. A standalone smoke-test script, `hooks/test-skill-nudge.sh`, MUST run the hook under at minimum: (a) normal repo state, (b) `CLAUDE_PLUGIN_ROOT` unset, (c) `skills/` directory missing, (d) `jq` unavailable — asserting exit code 0 and valid-or-empty stdout in every case. This is mandatory specifically because REQ-001 is the largest single increase in failure-mode surface area in this gap list for a hook with no per-user opt-in.

---

## Gap 2 — Skill pressure-testing methodology

### REQ-004

Add one adversarial "pressure" prompt file per discipline-heavy skill (starting with `test-driven-development`) under `tests/skill-triggering/prompts/`, using the existing `.txt`-per-skill convention, encoding a "just this once, skip the rule, I'm in a hurry" jailbreak against that skill's core discipline. These are read manually against the existing trigger-only `tests/skill-triggering/run-test.sh` harness's output — no new scoring mechanism, no new meta-skill, no new test runner. A full RED/GREEN/REFACTOR authoring methodology and an automated discipline-scoring harness are explicitly declined for this pass: no skill in this repo has been observed caving under pressure in practice, and building per-skill authoring infrastructure for a speculative failure mode is a recurring authoring tax this gap does not yet justify. Revisit as a full build only after an observed discipline failure.

---

## Gap 3 — Durable per-task ledger

### REQ-005

`skills/context-optimizer/scripts/prune_context.py` gains a new flag, `--task-complete "Task N: complete (commits <base7>..<head7>, review clean)"`, that appends a line under a `## Task Ledger` heading in the same `.claude/rolling_summary.md` file `update_rolling_summary` already writes — not a new ledger file or format. The flag is additive-only and does not require `--summary` in the same invocation. The literal format string is normative: any consumer that later needs to extract the head commit hash from this line (see REQ-007) MUST do so by an unambiguous rule, not free-text parsing.

### REQ-006

`skills/multi-agent-development/SKILL.md`'s Core Loop MUST invoke `prune_context.py --task-complete ...` immediately after a task reaches `QUALITY_PASS`/`MINOR` and is merged, before advancing — not batched at cluster end. The "Resuming" guidance MUST be rewritten to read `.claude/rolling_summary.md`'s `## Task Ledger` section first and trust it over self-recollection, falling back to `git log` only if the ledger section is absent or unreadable (e.g. first task of a fresh plan).

### REQ-007

Because the ledger becomes a source of truth the orchestrator trusts over its own memory (REQ-006), ledger writes MUST be append-only (never rewritten in place), and every resume MUST cross-check the ledger's last recorded commit hash against `git log` before trusting it — a mismatch MUST be surfaced to the user as an explicit discrepancy, never silently resolved by picking one source. This cross-check requires an unambiguous extraction rule for the head hash out of REQ-005's `"Task N: complete (commits <base7>..<head7>, review clean)"` format: the head hash is the second 7-character token between the literal substring `(commits ` and the literal `..` — i.e. split the parenthetical on `..`, take the second segment, strip the trailing `, review clean)` suffix. An ambiguous parse rule here would defeat this requirement's own purpose, since two implementers parsing the line two different ways makes "trust the ledger over recollection" unverifiable. Confirm `.claude/rolling_summary.md` is excluded from version control the same way other `.claude/` local-state files already are (`hooks/lib.sh`'s settings file and `skill-nudge-state` are gitignored today; `rolling_summary.md` currently is not and should be checked/added).

### REQ-008

`skills/multi-agent-development/references/subagent-contract.md` is unchanged by this gap — ledger writes are an orchestrator-side concern, not a per-dispatch contract concern. No new field is added to the existing five-field schema.

---

## Gap 4 — File-handoff discipline for large artifacts

### REQ-009

`skills/multi-agent-development/references/subagent-contract.md` gains a rule, placed near the existing CONTEXT field description: any artifact requiring more than ~150 lines of inline text (a full diff, a full prior-task ledger excerpt, a full plan file) MUST NOT be pasted into the CONTEXT field of a dispatch prompt — write it to a file under `.claude/dispatch/` first and cite the path in CONTEXT instead. Add one example row to the contract's existing "Common Mistakes" table citing this failure mode. No new script is added: the dispatching skill already has `Write`/Bash heredoc access sufficient to drop a file under `.claude/dispatch/`, and this repo's dispatch surface (two skills — `multi-agent-development`, `multi-agent-dispatch` — calling one shared contract file) does not have enough call-site fan-out to justify a wrapper script the way superpowers' larger skill graph does.

### REQ-010

`skills/multi-agent-dispatch/SKILL.md`'s SELECT step and `skills/multi-agent-development/SKILL.md`'s Core Loop dispatch step each add one cross-reference line to the new rule (REQ-009) — no duplicated prose in either skill file.

---

## Gap 5 — Model-tiering policy for subagent dispatch

### REQ-011

`subagent-contract.md` gains a `## Model Tiering` section (placed after Role Vocabulary) defining a 3-tier table keyed off the Lane Matrix's existing `Files touched`/`Risk` signals (already present in both dispatch skills): 1-2 files with a fully concrete spec → fast/cheap; 3+ files or cross-module/ambiguous scope → standard (`model: inherit`); architecture-defining or final-review-gate role → most-capable. States the "turn count beats token price" rationale (a cheap model retried 3x on a multi-file task costs more than one standard-model pass) as a one-line note. The ambiguous/unmeasured-complexity case MUST default to the orchestrator's own current model, never silently to the cheapest tier — an under-qualified model producing wrong code that a matched-cheap reviewer rubber-stamps is a correctness risk in shipped code, the same class of risk as gap 3's ledger loss.

### REQ-012

The Model Tiering table (REQ-011) is documented as advisory: a dispatch-prompt hint applied as an explicit `model:` override at the dispatch call site (leaving each `agents/*.md` file's `model: inherit` frontmatter default unchanged), not a guaranteed restriction unless the calling harness exposes a model-pinning parameter. `multi-agent-development/SKILL.md`'s dispatch step and `multi-agent-dispatch/SKILL.md`'s SELECT step each add one line instructing consultation of the table before dispatch.

---

## Gap 6 — Duplicated hand-maintained routing

### REQ-013

The Mermaid "Lifecycle Chain" diagram in `skills/using-agent-sdlc-skills/references/lifecycle.md` is deleted outright — it restates the same Gate 0-4 matrix `SKILL.md` already states in prose, and a diagram saying the same thing as the text beside it is exactly the duplication this requirement removes. The non-duplicate `## Transition States` prose (TDD Escalation, Review Failure, Re-review Cap) is folded into `SKILL.md`'s existing `## Diagnose Return Paths` section — not into a newly created section — so there is exactly one file describing transition/return-path logic. `lifecycle.md`'s self-referential "both describe the same logic" drift-risk framing sentence is removed once the duplication it warns about no longer exists; if no content remains in `lifecycle.md` after this, the file is deleted.

### REQ-014

`skills/using-agent-sdlc-skills/SKILL.md`'s Gate matrix gains an explicit one-line disclaimer in its `## Rules` section scoping it to entry-routing only (Gate 0 onboarding through first dispatch at Gate 3) — it does not re-describe a skill's own exit transitions once that skill is active. Each skill's own `## Next Skills`/`## Transitions` section remains the canonical source for that skill's own outbound routing (this was already the pre-gap convention and is not collapsed into a pointer back at the central matrix — doing so would reintroduce the same indirection cost this requirement removes). `skills/multi-agent-development/SKILL.md`, which currently has no `## Next Skills` section, gains one naming `verification-before-completion` (Final Validation handoff), `context-optimizer` (mid-loop bloat), and `diagnose` (merge/test failure) — closing the one missing case before REQ-013/REQ-014's "canonical per-skill" rule can be said to hold for every skill it covers.
