---
name: architecting
description: "Performs architecture review and system design for problems spanning multiple files or crossing module boundaries in the target repo's own code. Analyzes existing directories, dependencies, and imports to generate an Architecture Decision Record (ADR) in docs/adr/ and an architecture-brief.json schema. Trigger on: 'architecture review', 'restructure across modules', 'too coupled', 'design this system', 'where should this code live', 'God class', 'circular deps', 'dependency mapping', 'domain boundaries'. Also triggers when addressing boundary violations, structural bleed, or resolving high git coupling between files. Always prefer this skill over request-plan when designing multi-module interfaces or correcting structural coupling before writing detailed implementation steps."
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
- **Dispatch:** One read-only `general-purpose` agent (Read/Glob/Grep only, no edits). Give it `target_dir` and the four scripts' stdout (or "skipped"). Ask it to read every high-severity flagged file, apply all four Seam Tests — Deletion (would complexity scatter to callers if removed?), Seam (testable without DB/API/infra?), Locality (readable without understanding 5+ other modules?), Bounded Context (do modules share tables directly without APIs/interfaces?) — quote the exact file path + import/pattern per friction signal (no editorializing), never propose event buses/base classes/utils folders, and return JSON only: a `candidates` array ranked by impact, each `{seam_name, evidence, seam_test_results, visual_diagram}` with a Mermaid `graph LR`/`graph TD` contrasting current tangled dependencies vs. the proposed clean boundary.

- **Phase_2_Present:** List 3-6 targets: [Name], [Files], [Bleed], [Deepening], [Impact], [Risk], [Mermaid]. Prompt: "Which of these candidates interests you most?"
- **Phase_3_Align:** - Load `references/DOMAIN_INTERVIEW.md` strictly upon interview start.
- Load `references/INTERFACE_SHAPES.md` & `references/SEAMS_BY_EXAMPLE.md` before proposing seams.

- **Phase_4_ADR:** Generate ADR in `docs/adr/` using `references/ADR_TEMPLATE.md`.
- **Phase_5_Handoff:** Generate `architecture-brief.json` (`references/brief-schema.json`). Read `references/MIGRATION_STRATEGIES.md` for gradual cutover. Handoff to `request-plan`.

- **Mode_B_Design:**
- **Constraint_Context:** NEVER load diagnostic templates (`references/DOMAIN_INTERVIEW.md`, `references/SEAMS_BY_EXAMPLE.md`).
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

- **Next_Skills:**
- **request-plan:** Formalize specs for new designs or major seam extractions.
- **multi-agent-development:** Execute complex architectural changes.
- **diagnose:** Isolate live bugs surfaced during Mode A exploration.

- **Constraints_Strict:**
- **No_PubSub_Coupling:** Ban pub/sub for synchronous logic. Use direct composition/dependency injection.
- **No_Utility_Bins:** Ban `utils/`, `common/`, or `shared/` directories. Group by domain/feature.
- **No_Base_Classes:** Ban inheritance if composition works. Use interface delegation.
- **No_Shared_Schemas:** Ban DB schema sharing across bounded contexts. Expose data via APIs/events strictly.
