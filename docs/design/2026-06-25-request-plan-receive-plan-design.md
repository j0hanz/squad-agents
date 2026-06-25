Approach: Replace `skills/planning` (deleted entirely, no code/templates/scripts reused) with two new skills — `request-plan` (generates) and `receive-plan` (verifies) — mirroring the codebase's existing `request-code-review`/`receive-code-review` naming pattern.

Why: User-directed pivot after 5-lens ideation converged on a single-skill fork of `parallel-brainstorming`; user rejected that shape outright and specified the two-skill split themselves, correctly observing it matches a pattern already proven in this codebase (one skill produces, one skill verifies-any-origin-input) and avoids anchoring on deprecated `planning` code. Phase 5 parallel critique (Skeptic / Constraint Guardian / User Advocate) + an independent Arbiter gate (verdict: REVISE, then 3 named gaps fixed below) stress-tested this shape before write-up.

Scope: L — two new skill directories, an orchestrator routing rework (`using-agent-sdlc-skills` Gate 1/Gate 3), no changes required to `multi-agent-development`/`multi-agent-dispatch`/`test-driven-development` (artifact contract preserved).

Constraints:

- Artifact contract preserved verbatim: `plan/NAME.specs.md` + `plan/NAME.plan.md`, Task Block Schema unchanged (`Depends on`/`Files`/`Symbols`/`Satisfies`/`Action`/`Validate`/`Expected result`) — zero downstream skill changes needed.
- No Python validation scripts anywhere (`cli.py scaffold/validate/sync/pipeline` is gone) — all checking is agent-driven.
- No code/templates/scripts copied from old `planning` — fresh implementation; only conventions (untrusted-context wrapping, review artifacts) may be reused as ideas, not as files.
- Every agent dispatch follows the five-field contract (SCOPE/OBJECTIVE/CONTEXT/CONSTRAINTS/OUTPUT SCHEMA) per `multi-agent-development/references/subagent-contract.md`; fan-out mechanics reuse `multi-agent-dispatch`'s GROUP→MATRIX→LAUNCH→INTEGRATE, not new dispatch logic.

Interface:

- `request-plan(feature_description, depth?)` → writes `plan/NAME.specs.md` + `plan/NAME.plan.md` marked `Status: DRAFT`, unconditionally hands off to `receive-plan`.
- `receive-plan(plan_path)` → accepts a plan/specs pair of ANY origin (from `request-plan`, hand-written, or from `architecting`'s brief) → returns APPROVED (flips `Status: DRAFT`→`Status: APPROVED`, writes `plan/NAME.review.md`) or REVISE (itemized file:line/REQ-id/TASK-id findings) or escalates to user after 2 round-trips.
- Orchestrator (`using-agent-sdlc-skills`) Gate 1 gains a third branch: "idea only" → `request-plan`; "plan/spec exists, unverified" → `receive-plan` directly; "verified" → Gate 2 (unchanged). Gate 3 escalations (spec ambiguous / TDD stuck) → `request-plan`.

Architecture:

- `request-plan`: Phase 1 Discovery (fresh codebase scan) → depth-gated blind Ideators (sketch=1 drafter, contract=3 lenses, blueprint=5 lenses), each drafts a full candidate specs.md+plan.md → one Synthesizer merges into one draft pair, emitting a kept/discarded rationale per candidate (prevents disguised "pick one, discard rest" passing as synthesis), and runs its own lightweight advisory-only reference cross-check (non-blocking — `receive-plan` is the sole gate) → Step 0 `AskUserQuestion` confirms depth before drafting starts, disclosing approx. agent-call count, default = `contract` unless the request itself signals "rough idea" (→ sketch) or "prod rollout/migration" (→ blueprint) — this single default-depth rule is referenced by name from both Step 0 and the orchestrator's Gate 1, not stated twice.
- `receive-plan`: blind critique panel (Spec-Correctness, Dependency-Correctness, Scope-Risk — skipped entirely at `sketch` depth) + a dedicated **Traceability Auditor** seat with real grep/file-read tool access running a mechanical-only checklist (REQ/TASK reference resolution, acyclic deps, required fields present, file/symbol paths exist) — always runs, every depth. Auditor's report header states `N_checked / N_total` per check category; the Arbiter's rule is purely mechanical — `N_checked < N_total` is an automatic REVISE regardless of transcript content. Raw grep/file-read transcripts are appended to the report as a human-inspectable audit trail in `plan/NAME.review.md`, not something the Arbiter itself re-parses. Arbiter requires Auditor zero-findings (and complete counts) as a hard gate, separate from the other seats' qualitative High/Med/Low calls. Capped at 2 REVISE round-trips (matches `multi-agent-development`'s existing 2-try precedent), then escalates to the user with the unresolved-findings diff.
- Untrusted input handling: Traceability Auditor reads/greps only, never executes any `Validate:` command string. Any plan content from outside this session (hand-written, externally sourced) is wrapped in `<untrusted_context>` tags — including the headless fallback where an externally-sourced REVISE plan is routed through the Synthesizer as one additional candidate; that injected candidate is wrapped in `<untrusted_context>` too, same as the Auditor's handling, so the Synthesizer's merge contract doesn't silently become mixed-trust.

Risks:

- Synthesizer merge quality at blueprint depth (5 candidates) is bounded by single-pass context handling — mitigated by the kept/discarded rationale requirement, not eliminated.
- Traceability Auditor is the sole reliability backstop now that scripts are gone — mitigated by the count-based mechanical gate, not made deterministic; residual risk accepted per explicit user direction (agents-only, no scripts).
- Two-skill split adds one more name for users to learn — mitigated by `receive-plan` carrying its own standalone trigger phrases ("check my plan", "is this plan ready") independent of orchestrator routing.
- REVISE re-merge preserves original depth/lens-count unless the user explicitly requests escalation (one-line behavior note, not a design risk).
- Repo-wide grep for existing `Status:` field usage: run, no collisions found — `Status: DRAFT`/`Status: APPROVED` only appear in `skills/request-plan/SKILL.md` and `skills/receive-plan/SKILL.md`. Closed.
- Manual edits to an `APPROVED` plan invalidate the `Status: APPROVED` marker — documented behavior, not enforced in code.

First step: Scaffold `skills/request-plan/SKILL.md` and `skills/receive-plan/SKILL.md` from scratch (no copy from `skills/planning`), starting with `request-plan`'s Phase 1 Discovery + Step 0 confirmation gate, since every later phase depends on that contract being right first.
