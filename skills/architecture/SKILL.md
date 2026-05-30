---
name: architecture
description: >-
  Software architecture — two modes. MODE A (DIAGNOSE existing codebase): circular dependencies,
  God modules, infra leaking into domain, "code is a mess", "hard to test", "one change touches
  5 files", "utils folder chaos", "can't test without a database", files 300+ lines, tangled
  dependencies, scattered logic. MODE B (DESIGN new systems or modules): how to organize a
  feature, where business logic should live, which architectural pattern to choose, how to design
  clear module boundaries, or evolving existing boundaries toward a better design.
disable-model-invocation: false
allowed-tools: Bash(node *)
---

# Architecture

## Before Routing

If the user's message provides no clear intent — a single word, a vague noun, no codebase context — ask one targeted question before selecting a mode:

> "Are you looking to diagnose an existing codebase, or design something new?"

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

Load these as needed during the 3-phase procedure.

### Core Heuristics

Claude, you already understand SOLID principles and cohesion. Do not regurgitate them. Instead, apply these battle-tested diagnostics for identifying poor boundaries:

- **The Deletion Test**: If removing a module would spread its complexity across N callers, it earns its keep. If callers wouldn't notice, it is shallow and should be collapsed.
- **The Seam Test**: Can business logic be tested without booting a database, making an HTTP call, or touching the filesystem? If no, the seam is drawn at the mechanism layer, not the domain layer.
- **The Locality Test**: Can a maintainer (or AI context window) understand a module without reading its dependents? Circular imports or 5+ file dependency chains for one feature indicate shattered locality.

### Anti-Patterns (What NOT to do)

Architectural refactoring fails when it adds indirection without adding depth. **NEVER** propose the following common AI-flavored refactoring mistakes:

- **NEVER propose an Event Bus/PubSub to solve direct coupling.** It does not decouple logic; it just makes the coupling implicit, destroying code navigation and trace-ability. Use explicit function passing or composition instead.
- **NEVER group files by technical role (e.g., `utils/`, `controllers/`, `types/`).** This destroys locality. Always group by domain concept (e.g., `billing/`, `auth/`). A `utils/` folder is a complexity graveyard.
- **NEVER extract a base class (Inheritance) when Composition is possible.** Inheritance chains hide state and make AI navigation harder. Propose wrapper classes, higher-order functions, or strategy interfaces.
- **NEVER propose variable renaming or formatting as an "architecture" fix.** If the interface boundary doesn't change, the depth hasn't changed.

### Three-Phase Procedure

#### Phase 1: Explore

Walk the codebase using the automated analysis scripts. Scripts gracefully skip inaccessible directories and unreadable files.

- **MANDATORY — RUN SCRIPT**: **Locality Check**: Run `node <skill-dir>/scripts/check-locality.mjs [dir]` to find circular dependencies and "God modules" (high fan-out). Example: `node <skill-dir>/scripts/check-locality.mjs src`
- **MANDATORY — RUN SCRIPT**: **Bleed Detection**: Run `node <skill-dir>/scripts/detect-bleed.mjs [domain_dir] [infra_packages]` to find infrastructure leaks (e.g., Express or Prisma in domain logic). Example: `node <skill-dir>/scripts/detect-bleed.mjs src/domain express,prisma,typeorm`

**After both scripts complete — spawn the `architecture-scanner` subagent** (`agents/architecture-scanner.md`):

```
Agent(
  description: "Architecture scan of [target_dir]",
  prompt: |
    target_dir: [the directory you scanned]
    locality_output: [paste full stdout of check-locality.mjs here]
    bleed_output: [paste full stdout of detect-bleed.mjs here]
)
```

The agent reads every flagged file, applies the Deletion/Seam/Locality tests, and returns a `candidates` JSON array ranked by impact. **Use that array as your Phase 2 input** — each element maps directly to the candidate format in Phase 2. Skip manual file reading in the main context when the agent is available.

**If no directory is available** (user pasted inline code without a path):
- Skip the scripts.
- Tell the user: "Running manual analysis on the provided code — if you have a project directory, share the path for automated scanning."
- Proceed with manual friction-signal identification below.

**Manual Exploration** (if scripts don't fit the project structure, or no directory is available):

Look for these friction signals:

1. **Scattered Logic**: A single feature change requires touching 3+ unrelated files.
2. **Infrastructure Bleed**: Domain logic modules import `express.Request`, database entity types, or UI frameworks (mechanism bleeding into policy).
3. **Size/Complexity**: Files exceed ~300 lines where intent is lost in boilerplate.
4. **Tangled Dependencies**: Modules form a web where you can't understand one without reading 5+ others.
5. **Testability Barriers**: You can't unit-test domain logic without mocking infrastructure (database, HTTP, filesystem).

#### Phase 2: Present Candidates

You must constrain yourself. Do NOT write implementation code — no function bodies, class implementations, or working logic. Typed interface signatures are acceptable when they clarify the proposed seam boundary, but keep them minimal. List **3–6 deepening opportunities**, ordered by impact. Use this exact format:

```markdown
**[Short Name of Opportunity]**

- **Files:** `src/foo.ts`, `src/bar.ts`
- **The Bleed:** [1 sentence: What mechanism is leaking, or what makes this shallow?]
- **The Deepening:** [Plain English: Where the new boundary goes and why it increases leverage.]
- **Impact:** [Locality | Testability | AI-Navigability]
```

**Refer to SEAMS_BY_EXAMPLE.md in references/ for 3 real examples of good and bad seams.**

**Example candidate**:

```markdown
**Extract Auth Domain from Scattered Files**

- **Files:** `src/auth.ts`, `src/middleware.ts`, `src/utils.ts`, `src/routes/login.ts`
- **The Bleed:** Password hashing is in utils, JWT generation is in middleware, user lookup is in routes. Each change requires touching 4 files. Testing requires a database.
- **The Deepening:** Consolidate password hashing, token generation, and credential validation into one `auth/` module. Routes and middleware become thin adapters that call auth, not the other way around. Tests can mock the user lookup, so no database needed.
- **Impact:** Locality (auth logic concentrated in one module) | Testability (test password and token logic in isolation) | AI-Navigability (one module to understand instead of four)
```

End your response exactly with:

> "Which of these candidates interests you most?"

#### Phase 3: Domain Interview & Handoff

Once the user picks a candidate, do NOT start writing code immediately.

1. **Align Terminology**: Conduct a brief interview (1 question at a time, see **DOMAIN_INTERVIEW.md** in references/) to establish Canonical Terms and resolve ambiguous concepts.

2. **Propose the Seam**: Only after the domain language is clear, propose the concrete refactoring — specifically, the _new interface shape_ using the agreed-upon glossary terms. Examples are in **INTERFACE_SHAPES.md** in references/. Show what callers will import and use; don't write implementation yet.

3. **Apply the Deletion Test aloud**: Ask the user: "If we deleted this module, where would the logic go?" If they say "it would duplicate across 5 callers," you've got a good deepening. If they say "it would just move to the caller," the module is shallow and needs rethinking.

4. Wait for user approval before modifying files.

5. **Handoff:** This skill diagnoses and proposes seams — it does not implement them. Once a seam is approved, execute it with the `refactor` skill for a behavior-preserving extraction, or hand the proposed seam to `create-plan` when the change spans multiple files or phases.

### When to Stop

Stop proposing candidates when:

- The remaining friction is purely cosmetic (variable renaming, moving files without changing imports/structure).
- The next refactor crosses a documented ADR boundary not worth reopening.
- The codebase is a throwaway script or proof-of-concept where leverage doesn't matter.

---

## MODE B — DESIGN: Design New Architecture

### Core Philosophy

Architecture is the set of decisions that are hard to change later. Your goal is to maximize **Reversibility** and **Boundary Integrity**. Do not just "clean the code"; design the system to survive the "Churn of Infrastructure" (frameworks, DBs, APIs).

### Three-Step Procedure

#### Step 1: Diagnose

Before proposing a structure, run this diagnosis:

1. **Identify the Core Domain**: What is the "Business Fact" this code exists to manage? Separate this from the "Mechanism" (how it's stored or delivered).
2. **Map the Change Drivers**: Ask "If X changes (e.g., swapping SQL for NoSQL, moving from Web to CLI), what code _must_ break?"
3. **Boundary Stress Test**: Mentally attempt to move a feature module to a separate repository. If the "seams" are bleeding implementation details, the boundary is wrong.
4. **Select Pattern**:
   - **MANDATORY**: If considering a specific pattern (Layered, Hexagonal, CQRS, etc.), you MUST read `references/architecture-patterns.md` to evaluate its failure modes before recommending.

#### Step 2: Propose

5. **Define the Public Surface**: Design the API (interfaces/types) of the module as if it were a third-party library. Show what callers will import — don't write implementation yet.

#### Step 3: Confirm

6. **Apply the Swap Test**: Ask the user: "If we swapped [the key mechanism — the database, the HTTP framework, the payment provider], what code changes?" If the answer is "only the adapter/infra layer," the boundary is right. If domain logic would change, redraw the seam.

### Expert Principles

- **Prefer Duplication over the Wrong Abstraction**: In early-stage features, allow two modules to have similar code rather than creating a `shared` module that couples them forever.
- **Dependencies Point Toward Stability**: Outer layers (UI, DB) depend on the Domain (Logic), never the reverse. The Domain should not know it's being saved to a database.
- **The "utils" Grave**: `utils`, `common`, and `shared` are where architectural integrity goes to die. If logic is shared, it usually belongs in a named domain concept or a specific infrastructure adapter.
- **Policy vs. Mechanism**: High-level policy (Business Rules) must be physically separated from low-level mechanism (HTTP status codes, SQL queries).

### Boundary Integrity Checks

- **No Framework Leakage**: Business logic should not import framework-specific decorators or types (e.g., `@nestjs/common`, `Express.Request`).
- **Explicit Seams**: Use Interfaces/Abstract classes at boundaries. The implementation (Adapter) lives in the Infrastructure layer; the Interface lives in the Domain layer (Dependency Inversion).
- **Narrow Public API**: Only export the minimum required. Keep internal helpers and state truly private within the module.

### When to Simplify (The YAGNI Threshold)

Do NOT escalate to architecture if:

- The code is a throwaway migration or one-off script.
- The feature has zero external dependencies and very low logic complexity.
- The user is asking for a "Proof of Concept" where speed of validation outweighs long-term maintenance.

### Expert NEVER List

- **NEVER** use "Generic" naming (`Manager`, `Processor`, `Service`) without a domain prefix that explains the _what_.
- **NEVER** allow the database schema to dictate the Domain Model. Use separate types for DB entities and Domain objects.
- **NEVER** use "Hidden Coupling" (Global state, Singletons that hold logic, implicit environment variable dependencies).
- **NEVER** implement CQRS or Event Sourcing just for "scalability" unless you can identify a specific read-model bottleneck that justifies the 5x increase in complexity.
- **NEVER** let a "Utility" module grow past 3 unrelated functions. Split it by domain responsibility immediately.
