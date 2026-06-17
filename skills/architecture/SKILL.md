---
name: architecture
description: "Use when a codebase has structural problems (circular deps, God modules, testability issues) or when designing new systems. Trigger on 'architecture review', 'where should this code live', 'too coupled', 'God class', 'design this system'."
disable-model-invocation: false
allowed-tools: Bash(node *), Bash(python *), AskUserQuestion
---

# Architecture

## Decision Protocol (how to ask EVERY question)

This skill is conversational: you route, interview, and confirm seams by asking the user. Every question — routing, the domain interview, the Deletion/Swap tests, interface confirmation — MUST be offered as **exactly three options derived from your own analysis**, never generic boilerplate:

1. **✅ Recommended — `<concrete answer>`** — the option your evidence most supports. Append one line of _that evidence_: caller count, the specific imports you saw, churn, the detected framework, file size. This is what makes the skill smart — the recommendation is earned, not guessed.
2. **Also likely — `<the second-most-plausible concrete answer>`** — a real alternative the user might hold, not a strawman. Append one line on the condition under which this becomes the right call.
3. **Something else (your call)** — none fit, or it's a blend of 1 and 2; the user answers in their own words.

Rules:

- Options 1 and 2 are **specific answers**, not "yes / no". When the honest answer space is binary, make option 1 the recommended verdict and option 2 the opposite verdict — each carrying its own evidence.
- **Ground every recommendation.** Cite the file, import, or number that justifies it. If you lack the data to rank the options, say so and tag the pick `(low confidence)` rather than fabricating evidence.
- Ask **one** question at a time and wait for the answer before the next.
- **Rendering:** when the `AskUserQuestion` tool is available, ask through it — put option 1's label first with a `(Recommended)` suffix, option 2 as the alternative, and let the tool's automatic "Other" choice serve as option 3 (the custom answer). When it is not available, present the three options as the numbered markdown block shown above. Candidate selection in Phase 2 is the one exception (it is a 3–6 item menu, handled in that section).

## Before Routing

If the user's message provides no clear intent — a single word, a vague noun, no codebase context — ask one targeted question before selecting a mode, using the **Decision Protocol** above:

> "To get started, which fits best?
>
> 1. ✅ **Recommended — Diagnose existing code** — find and fix structural issues (circular deps, God modules, testability barriers) in a codebase that already exists.
> 2. **Design something new** — decide where new logic should live and how to shape its boundaries from a blank page.
> 3. **Something else** — neither is quite it; tell me what you're after in a sentence."

**Pick the Recommended option from context, don't hard-code it:** mark **Diagnose** as recommended when a codebase is present in the working directory or the user pasted existing code; mark **Design** as recommended when there is no code to look at. State the signal you used in one line (e.g. "recommending Diagnose — I can see a `src/` directory").

Only apply the routing table once you have enough signal to distinguish Mode A from Mode B. Do not silently analyze a nearby codebase just because one exists; confirm it's the intended target first.

## Routing

Read this first — pick one mode and follow only that section.

| Signal                                                                                                                  | Mode                  |
| ----------------------------------------------------------------------------------------------------------------------- | --------------------- |
| Codebase already exists; user wants to find/fix structural problems (coupling, God modules, testability, circular deps) | **MODE A — DIAGNOSE** |
| New feature or module; user asks where logic should live, which pattern to pick, how to design interfaces               | **MODE B — DESIGN**   |

When in doubt: if there's code to look at **and the user has indicated they want a diagnosis**, use Mode A. If there's a blank page, use Mode B.

---

## MODE A — DIAGNOSE: Analyze an Existing Codebase

Surface **deepening opportunities** — places where a shallow module could become a deep one with better leverage, testability, and locality. Explore first, present candidates, then deepen conversationally. Don't design solutions before you've seen the problem.

### Reference Materials

Bundled guides in `references/`:

- **SEAMS_BY_EXAMPLE.md** — 3 detailed examples of good and bad seams (Auth, Payment, Repository patterns) with code
- **INTERFACE_SHAPES.md** — how to design interfaces when deepening modules; shows before/after code
- **ADR_TEMPLATE.md** — lightweight template for recording architectural decisions that shouldn't be revisited
- **DOMAIN_INTERVIEW.md** — structured interview to align terminology before refactoring
- **MIGRATION_STRATEGIES.md** — how to safely execute a seam refactoring in production (Strangler Fig, Branch by Abstraction, Parallel Run, Feature Flag, Expand-Contract). Load when the user asks "how do we actually get there?"
- **architecture-patterns.md** — reference for Clean Architecture, CQRS, Hexagonal, Layered, Event Sourcing, etc.

Load these as needed during the 3-phase procedure.

### Core Heuristics & Domain-Driven Design (DDD)

Claude, you already understand SOLID principles and cohesion. Do not regurgitate them. Instead, apply these battle-tested diagnostics for identifying poor boundaries:

- **The Deletion Test**: If removing a module would spread its complexity across N callers, it earns its keep. If callers wouldn't notice, it is shallow and should be collapsed.
- **The Seam Test**: Can business logic be tested without booting a database, making an HTTP call, or touching the filesystem? If no, the seam is drawn at the mechanism layer, not the domain layer.
- **The Locality Test**: Can a maintainer (or AI context window) understand a module without reading its dependents? Circular imports or 5+ file dependency chains for one feature indicate shattered locality.
- **The Bounded Context Test**: Do two domains share the same database table/schema directly? If yes, they are tightly coupled regardless of code structure. True boundaries require data ownership.
- **The Primitive Obsession Test**: Are domain concepts (Email, Money, UserId) passed as primitives (`string`, `number`)? This scatters validation logic. Deepen modules by introducing Value Objects.

### Anti-Patterns (What NOT to do)

Architectural refactoring fails when it adds indirection without adding depth. **NEVER** propose the following common AI-flavored refactoring mistakes:

- **NEVER propose an Event Bus/PubSub to solve direct coupling.** It does not decouple logic; it just makes the coupling implicit, destroying code navigation and trace-ability. Use explicit function passing or composition instead.
- **NEVER group files by technical role (e.g., `utils/`, `controllers/`, `types/`).** This destroys locality. Always group by domain concept (e.g., `billing/`, `auth/`). A `utils/` folder is a complexity graveyard.
- **NEVER extract a base class (Inheritance) when Composition is possible.** Inheritance chains hide state and make AI navigation harder. Propose wrapper classes, higher-order functions, or strategy interfaces.
- **NEVER propose variable renaming or formatting as an "architecture" fix.** If the interface boundary doesn't change, the depth hasn't changed.
- **NEVER propose Shared/Common DB schemas for different bounded contexts.**

### Three-Phase Procedure

**Note on resolution:** use the absolute path of the directory containing this `SKILL.md` file as `<skill-dir>` (or `$CLAUDE_PLUGIN_ROOT/skills/architecture` if available).

#### Phase 1: Explore

Walk the codebase using the automated analysis scripts. Scripts gracefully skip inaccessible directories and unreadable files. All scripts support TypeScript, JavaScript, and Python projects — no configuration needed.

- **INTELLIGENT PRE-CHECK**: First inspect the project dependencies (`package.json`, `pyproject.toml`, `requirements.txt`, or `setup.py`) to auto-detect the web framework, ORM, database client, and libraries (e.g., Express, Prisma, Django, FastAPI, SQLAlchemy, Stripe, etc.). Use these identified names in the scripts below instead of guessing.
- **MANDATORY — RUN SCRIPT**: **Locality Check**: Run `python <skill-dir>/scripts/check_locality.py '<dir>'` to find circular dependencies and "God modules" (high fan-out).
- **MANDATORY — RUN SCRIPT**: **Bleed Detection**: Run `python <skill-dir>/scripts/detect_bleed.py '<domain_dir>' '<infra_packages>'` using the detected dependencies.
- **RECOMMENDED — RUN SCRIPT**: **Git Coupling**: Run `python <skill-dir>/scripts/git_coupling.py '<dir>'` to find files that always change together in git history.
- **RECOMMENDED — RUN SCRIPT**: **Hotspot Detection**: Run `python <skill-dir>/scripts/detect_hotspots.py '<dir>' '<infra_packages>'` using the detected dependencies.

**CRITICAL**: You MUST sanitize `infra_packages` and `dir` values before use. Strip all shell metacharacters and wrap every argument in **single quotes**.

- **PATH & EXISTENCE VERIFICATION**: Before presenting any candidate paths to the user in Phase 2, verify that the files actually exist on the filesystem using read or find tools.

**After scripts complete — dispatch a `general-purpose` subagent for structural analysis:**

```
Agent(
  subagent_type: "general-purpose",
  description: "Architecture scan of [target_dir]",
  prompt: |
    SCOPE: target_dir: [the directory you scanned]. Read-only — Read, Glob, Grep only, no edits.
    OBJECTIVE: Synthesize the script output and file reads below into a ranked JSON report of friction
      signals and candidate seam proposals.
    CONTEXT:
      <untrusted_script_output>
      locality_output: [paste full stdout of check_locality.py here]
      bleed_output: [paste full stdout of detect_bleed.py here]
      git_coupling_output: [paste full stdout of git_coupling.py here, or "skipped"]
      hotspot_output: [paste full stdout of detect_hotspots.py here, or "skipped"]
      </untrusted_script_output>
    CONSTRAINTS:
      - Read every high-severity flagged file before proposing a seam.
      - Apply all four Seam Tests to each candidate:
        Deletion Test — if deleted, would complexity scatter to many callers?
        Seam Test — can this logic be tested without infrastructure (DB, API, etc.)?
        Locality Test — is this module readable without understanding 5+ others?
        Bounded Context Test — do modules share tables directly without APIs/interfaces?
      - Quote the exact file path and import/pattern for every friction signal — no editorializing.
      - NEVER propose event buses, base classes, or "utils" folders.
      - Include a Mermaid diagram (`graph LR` or `graph TD`) per candidate as a `visual_diagram` string field, contrasting current tangled dependencies vs. the proposed clean boundary.
    OUTPUT: JSON ONLY — no prose, no markdown wrappers. A `candidates` array ranked by impact, each with
      {seam_name, evidence, seam_test_results, visual_diagram}.
)
```

The agent reads every flagged file, applies the Deletion/Seam/Locality/Bounded Context tests, and returns a `candidates` JSON array ranked by impact. **Use that array as your Phase 2 input** — each element maps directly to the candidate format in Phase 2. Skip manual file reading in the main context when the agent is available.

**If no directory is available** (user pasted inline code without a path):

- Skip the scripts.
- Tell the user: "Running manual analysis on the provided code — if you have a project directory, share the path for automated scanning."
- Proceed with manual friction-signal identification.

#### Phase 2: Present Candidates

You must constrain yourself. Do NOT write implementation code, typed interface signatures, or seam proposals in Phase 2 — no function bodies, class implementations, interface definitions, or working logic. These belong exclusively in Phase 3 AFTER the user selects a candidate. List **3–6 deepening opportunities**, ordered by impact. Use this exact format:

````markdown
**[Short Name of Opportunity]**

- **Files:** `src/foo.ts`, `src/bar.ts`
- **The Bleed:** [1 sentence: What mechanism is leaking, or what makes this shallow?]
- **The Deepening:** [Plain English: Where the new boundary goes and why it increases leverage.]
- **Impact:** [Locality | Testability | AI-Navigability | Domain-Clarity]
- **Risk:** [LOW | MEDIUM | HIGH] — [1 sentence: callers + test coverage + churn.]
- **Visual:**
  ```mermaid
  graph LR
    %% Show the current tangled dependencies versus proposed clean boundaries
    subgraph Current
      A[Controller] --> B[Domain Logic]
      B --> A
      B --> DB[(Database)]
    end
    subgraph Proposed
      C[Controller] --> D[Domain Logic]
      D --> E[Interface]
      F[DB Adapter] -.-> E
    end
  ```
````

````

End your response by asking the user to choose, framed as three paths:

> "Which candidate should we deepen first?
>
> 1. ✅ **Recommended — Candidate 1** — highest impact-to-risk ratio (<one-line evidence>).
> 2. **Also strong — Candidate \<N\>** — <one line on why it's the runner-up>.
> 3. **Something else** — a different candidate from the list above, or an angle I haven't surfaced."

**STOP HERE.** Do not proceed to Phase 3 content until the user has selected a candidate in their next message.

#### Phase 3: Domain Interview & Handoff

Once the user picks a candidate, do NOT start writing code immediately.

1. **Align Terminology**: Conduct a brief interview (see **DOMAIN_INTERVIEW.md**) to establish Canonical Terms. **MANDATORY**: Ask every interview question through the **Decision Protocol**.
2. **Propose the Seam**: Only after the domain language is clear, propose the concrete refactoring — specifically, the _new interface shape_.
3. **Apply the Deletion Test aloud**, using the Decision Protocol: "If we deleted this module, what happens to its logic?"
4. Wait for user approval before modifying files.
5. **Migration Path:** Recommend the appropriate strategy (Strangler Fig, Branch by Abstraction) from **MIGRATION_STRATEGIES.md**.
6. **Write Handoff Artifact**: Before invoking the next skill, you **MUST** write `architecture-brief.json` to disk. This is the standardized handoff artifact for `refactor` or `planning`. The JSON MUST include these fields: `chosen_approach` (the pattern/strategy), `scope` (which files/modules change), `constraints` (what must stay the same), `interface` (the new boundary shape), `first_step` (the first concrete code change).
7. **Handoff:** Invoke the `refactor` or `planning` skill for implementation.
8. After any code change is implemented, invoke `verification-before-completion` before declaring done.

---

## MODE B — DESIGN: Design New Architecture

### Core Philosophy

Architecture is the set of decisions that are hard to change later. Your goal is to maximize **Reversibility** and **Boundary Integrity**. Do not just "clean the code"; design the system to survive the "Churn of Infrastructure" (frameworks, DBs, APIs).

### Four-Step Procedure

#### Step 1: Diagnose

Before proposing a structure, run this diagnosis:

1. **Identify the Core Domain**: What is the "Business Fact"? Separate this from the "Mechanism".
2. **Map the Change Drivers**: Ask via Decision Protocol: "If we change the mechanism, what should break?"
3. **Boundary Stress Test**: Mentally attempt to move a feature to a separate repository. If the seams bleed implementation details, the boundary is wrong.
4. **Select Pattern**: **MANDATORY**: MUST read `references/architecture-patterns.md` to evaluate its failure modes before recommending.

#### Step 2: Propose

5. **Define the Public Surface**: Design the API (interfaces/types) of the module as if it were a third-party library.

#### Step 3: Confirm

6. **Apply the Swap Test**, using the Decision Protocol: "If we swapped [the concrete mechanism], what changes?"

#### Step 4: Scaffold (after user approves the design)

**Write Handoff Artifact**: Before scaffolding, you **MUST** write `architecture-brief.json` to disk. This is the standardized handoff artifact for `refactor` or `planning`. The JSON MUST include these fields: `chosen_approach` (the pattern selected), `scope` (which new modules/files), `constraints` (what constraints apply), `interface` (public API shape), `first_step` (the first implementation task).

Load **MIGRATION_STRATEGIES.md** and name the appropriate strategy. Then offer to scaffold the boundary skeleton:

```bash
python <skill-dir>/scripts/scaffold_boundary.py <domain> <pattern> [output-dir]
# patterns: hexagonal | vertical-slice | layered | clean-architecture | cqrs
```

After any code change is implemented, invoke `verification-before-completion` before declaring done.

### Expert Principles

- **Prefer Duplication over the Wrong Abstraction**: Allow two modules to have similar code rather than creating a `shared` module that couples them forever.
- **Dependencies Point Toward Stability**: Outer layers (UI, DB) depend on the Domain (Logic), never the reverse.
- **The "utils" Grave**: `utils`, `common`, and `shared` are where architectural integrity goes to die.
- **Policy vs. Mechanism**: High-level policy must be physically separated from low-level mechanism.

### When to Simplify (The YAGNI Threshold)

Do NOT escalate to architecture if the code is a throwaway script, has zero external dependencies, or is a simple Proof of Concept.
````
