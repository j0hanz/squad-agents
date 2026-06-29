---
name: architecting
description: 'Use when the codebase has structural problems crossing module boundaries — God classes, circular dependencies, boundary violations, or high git coupling — or when designing a new module and deciding where code lives. Prefer over request-plan when the problem is structural rather than a missing feature.'
disable-model-invocation: false
allowed-tools: Bash(python *), Bash(python3 *), AskUserQuestion
---

# architecting

```
Trigger: Review/Design Request
  -- existing code --> Mode A: DIAGNOSE
                          -> 1. Explore (scripts/manual)
                          -> 2. Present opportunities
                          -> 3. Align (interview/seam)
                          -> 4. Record ADR
                          -> Handoff: request-plan
  -- new module ----> Mode B: DESIGN
                          -> 1. Identify domain vs mechanism
                          -> 2. Select pattern
                          -> 3. Stress test (swap test)
                          -> 4. Record ADR
                          -> 5. Scaffold (brief/scripts)
```

- **Trigger:** Architecture review, design request, or structural issues (God modules, circular dependencies).
- **Action_Route:** Confirm via `AskUserQuestion` (2-option markdown, no manual "Other"):
- **1_Recommended:** [Mode A or B] based on [evidence: imports, size, churn, existing vs. new].
- **2_Alternative:** [Other Mode] + applicability condition.

- **Mode_A_Focus:** DIAGNOSE (Existing code: God modules, bleed, git coupling, circular deps).
- **Mode_B_Focus:** DESIGN (New feature/module: Boundary integrity, reversibility, patterns).
- **Mode_A_Diagnose:**
- **Constraint_Context:** NEVER load `references/architecture-patterns.md`.
- **Phase_1_Explore:** - Detect tech stack.
- Run `scripts/` (default args shown):
- `python scripts/check_locality.py [dir=src]`
- `python scripts/detect_bleed.py [dir=src/domain] [infra=express,typeorm,prisma,fs,path,react,mongoose]`
- `python scripts/git_coupling.py [dir=.] [--min-count 3] [--since "6 months ago"] [--top-n 20]`
- `python scripts/detect_hotspots.py [dir=src] [infra=...] [--since "6 months ago"]`

- **Fallback:** Manually analyze imports, God modules (>500 lines/20+ exports), and history.
- **Dispatch:** Dispatch the named `researcher` subagent (`agents/researcher.md`) to run in read-only mode. Give it `target_dir` and the four scripts' stdout (or "skipped"). Ask it to read every high-severity flagged file, apply all four Seam Tests — Deletion (would complexity scatter to callers if removed?), Seam (testable without DB/API/infra?), Locality (readable without understanding 5+ other modules?), Bounded Context (do modules share tables directly without APIs/interfaces?) — quote the exact file path + import/pattern per friction signal (no editorializing), never propose event buses/base classes/utils folders, and return JSON only: a `candidates` array ranked by impact, each `{seam_name, evidence, seam_test_results, visual_diagram}` with a Mermaid `graph LR`/`graph TD` contrasting current tangled dependencies vs. the proposed clean boundary.

- **Phase_2_Present:** List 3-6 targets: [Name], [Files], [Bleed], [Deepening], [Impact], [Risk], [Mermaid]. Prompt: "Which of these candidates interests you most?"
- **Phase_3_Align:** - Load `references/DOMAIN_INTERVIEW.md` strictly upon interview start.
- Load `references/INTERFACE_SHAPES.md` before proposing seams.

- **Phase_4_ADR:** Generate ADR in `docs/adr/` using `references/ADR_TEMPLATE.md`.
- **Phase_5_Handoff:** Generate `architecture-brief.json` (`references/brief-schema.json`). Read `references/MIGRATION_STRATEGIES.md` for gradual cutover. Handoff to `request-plan`.

- **Mode_B_Design:**
- **Constraint_Context:** NEVER load diagnostic templates (`references/DOMAIN_INTERVIEW.md`, `references/INTERFACE_SHAPES.md`).
- **Step_1_Diagnose:** Isolate Core Domain vs. Mechanism.
- **Step_2_Pattern:** Read `references/architecture-patterns.md`; select optimal pattern.
- **Step_3_Stress_Test:** Apply Swap Test (If [mechanism] changes, what breaks?).
- **Step_4_ADR:** Generate ADR in `docs/adr/` using `references/ADR_TEMPLATE.md`.
- **Step_5_Scaffold:** - Generate `architecture-brief.json` (`references/brief-schema.json`).
- Read `references/MIGRATION_STRATEGIES.md` for integration cutovers.
- Run `python scripts/scaffold_boundary.py <domain> [pattern] [output_dir=src] [--force]`. _(Valid patterns: hexagonal, vertical-slice, layered, clean-architecture, cqrs. Others require manual creation)._

- **Heuristics:**
- **Deletion:** Removal must not scatter complexity across callers.
- **Seam:** Logic must be testable strictly without I/O (DB/HTTP).
- **Locality:** Module must be comprehensible without tracing 5+ dependents.
- **Stability:** UI/DB depends on Domain. Never reverse.
- **Scale (YAGNI):** Skip formal patterns for <1,000 lines, throwaways, or single-dev setups.

- **Worked_Example (Mode_A):**
- Trigger: "checkout module is a God class, 1800 lines, touches billing/inventory/email directly."
- Phase_1: `detect_bleed.py dir=src/checkout infra=stripe,pg,nodemailer` flags 14 direct infra imports inside `src/checkout/Checkout.ts`; `git_coupling.py` shows `Checkout.ts` and `InventoryService.ts` co-change in 11/14 commits despite no declared dependency.
- Phase_2: Present candidate — `[Checkout/Inventory seam], [Checkout.ts, InventoryService.ts], [Checkout calls InventoryService internals directly, no interface], [explains the 11/14 git-coupling], [Impact: high — blocks independent billing changes], [Risk: med], [Mermaid: tangled vs. clean]`.
- Phase_3: User picks the seam → `INTERFACE_SHAPES.md` proposes an `InventoryPort` interface; `DOMAIN_INTERVIEW.md` confirms inventory reservation is a distinct bounded context.
- Phase_4: ADR-0007 recorded: "Extract InventoryPort interface between Checkout and Inventory."
- Phase_5: `architecture-brief.json` written; handoff to `request-plan` with the brief attached as context.
- **Next_Skills:**
- **request-plan:** Formalize specs for new designs or major seam extractions.
- **multi-agent-development:** Execute complex architectural changes.
- **diagnose:** Isolate live bugs surfaced during Mode A exploration.

- **Constraints_Strict:**
- **No_PubSub_Coupling:** Ban pub/sub for synchronous logic. Use direct composition/dependency injection.
- **No_Utility_Bins:** Ban `utils/`, `common/`, or `shared/` directories. Group by domain/feature.
- **No_Base_Classes:** Ban inheritance if composition works. Use interface delegation.
- **No_Shared_Schemas:** Ban DB schema sharing across bounded contexts. Expose data via APIs/events strictly.
