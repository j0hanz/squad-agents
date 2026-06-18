---
name: architecting
description: "Expert architecture review and system design for problems spanning multiple files or module boundaries — circular dependencies, God modules, or boundary violations (bleed). Not for single-file cleanup (see refactor). Trigger on: 'architecture review', 'restructure across modules', 'too coupled', 'design this system', 'where should this code live', 'God class', 'circular deps', 'dependency mapping', 'domain boundaries'."
disable-model-invocation: false
allowed-tools: Bash(node *), Bash(python *), AskUserQuestion
---

# architecting

```dot
digraph architecting {
  rankdir=TB;
  node [shape=box, style=rounded, fontname="Helvetica"];
  edge [fontname="Helvetica", fontsize=10];

  Trigger [label="Trigger: Review/Design Request", shape=diamond];
  ModeA [label="Mode A: DIAGNOSE\n(Existing Code)"];
  ModeB [label="Mode B: DESIGN\n(New Feature)"];

  // Mode A Flow
  ExploreA [label="1. Explore\n(Scripts/Manual)"];
  PresentA [label="2. Present\nOpportunities"];
  AlignA   [label="3. Align\n(Interview/Seam)"];
  ADRA     [label="4. Record ADR"];
  HandoffA [label="Handoff:\nrefactor/planning"];

  // Mode B Flow
  IdentifyB [label="1. Identify\nDomain vs Mechanism"];
  SelectB   [label="2. Select Pattern"];
  StressB   [label="3. Stress Test\n(Swap Test)"];
  ADRB      [label="4. Record ADR"];
  ScaffoldB [label="5. Scaffold\n(Brief/Scripts)"];

  Trigger -> ModeA [label="existing code"];
  Trigger -> ModeB [label="new module"];

  ModeA -> ExploreA -> PresentA -> AlignA -> ADRA -> HandoffA;
  ModeB -> IdentifyB -> SelectB -> StressB -> ADRB -> ScaffoldB;
}
```

**trigger:** Architecture review, design request, or structural issues (God modules, circular deps).

**action: Route & Confirm**
Route and confirm via `AskUserQuestion` (or 3-option markdown block):

1. ✅ **Recommended** — [Concrete Answer] based on [evidence: imports, size, churn].
2. **Alternative** — [Plausible Option] + condition for use.
3. **Other** — Custom response.

**routing:**
| Mode | Focus |
| :--- | :--- |
| **A: DIAGNOSE** | Existing code. God modules, bleed, git coupling, circular deps. |
| **B: DESIGN** | New feature/module. Boundary integrity, reversibility, patterns. |

**action: MODE A — DIAGNOSE**

1. **Explore**:
   - Detect tech stack.
   - Run `check_locality.py`, `detect_bleed.py`, `git_coupling.py`, `detect_hotspots.py`.
   - **Fallback**: Manually analyze imports, "God" modules (>500 lines/20+ exports), and history.
   - Dispatch `general-purpose` agent using `references/dispatch-template.md`.
2. **Present**: List 3-6 opportunities: [Name], [Files], [Bleed], [Deepening], [Impact], [Risk], [Mermaid].
3. **Align**:
   - Interview via `references/DOMAIN_INTERVIEW.md`.
   - Propose Seam: Interface definition, data flow, "Before vs After" Mermaid graph.
4. **Record ADR**: Write an ADR in `docs/adr/` using `references/ADR_TEMPLATE.md`.
5. **Brief & Handoff**: Write `architecture-brief.json` (see `references/brief-schema.json`). Handoff to `refactor` or `planning`.

**action: MODE B — DESIGN**

1. **Diagnose**: Identify Core Domain vs Mechanism.
2. **Select Pattern**: Use `references/architecture-patterns.md`.
3. **Stress Test**: Apply Swap Test (If [mechanism] changes, what breaks?).
4. **Record ADR**: Write an ADR in `docs/adr/` using `references/ADR_TEMPLATE.md`.
5. **Scaffold**: Write `architecture-brief.json` (see `references/brief-schema.json`). Run `scaffold_boundary.py` or manually create structure.

**heuristics:**

- **Deletion:** Would removal scatter complexity across callers?
- **Seam:** Is logic testable without I/O (DB/HTTP)?
- **Locality:** Can module be understood without reading 5+ dependents?
- **Stability:** UI/DB depends on Domain; never reverse.

**next skills:**

- `refactor`: To implement localized improvements found during diagnosis.
- `planning`: To create a formal spec for a new architectural design or major seam extraction.
- `multi-agent-development`: To execute the implementation of complex architectural changes.

**constraint:**

- Never use PubSub for direct coupling (use composition).
- Never use `utils/`, `common/`, or `shared/` (use domain-based grouping).
- Never extract base class if composition is possible.
- Never share DB schemas across bounded contexts.
