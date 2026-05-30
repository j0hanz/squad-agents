---
name: diagrams
description: |
  Expert heuristics for architectural modeling and visual communication using Mermaid. Use when asked to design systems, untangle complex architectures, map out distributed workflows, or generate C4/DDD/ERD/Sequence diagrams. Triggers on phrases like 'visualize architecture', 'draw a diagram', 'C4 model', 'sequence flow', 'database schema', 'spot architectural coupling', 'simplify complex architecture', 'untangle microservice design', 'data model design'. Do NOT use for basic Mermaid syntax help.
disable-model-invocation: false
---

# Architectural Diagrams

This skill provides expert heuristics for architectural modeling and visual communication using Mermaid. It does NOT teach Mermaid syntax or define basic concepts. It provides decision frameworks for untangling complex architectures and ensuring diagrams serve as effective communication tools.

---

## PHASE 1: Anti-Pattern Validation (Do This First)

Before generating ANY diagram, perform these mandatory checks. If any check fails, address it before proceeding.

### Check 1: Component Count
**Count the number of distinct components/services/entities the user mentions.**

- **If count > 20**: MANDATORY split into L1 context diagram + multiple L2 component diagrams. Do NOT ask permission; splitting is mandatory.
- **If count unclear** (user says "lots", "many", "several"): Ask explicitly: "How many components total?"
- **If count <= 5**: Likely a single diagram is appropriate
- **If count 6-20**: Assess complexity; may need single container diagram or early split planning

**Action**: If count > 20, load BOTH `references/c4-diagrams.md` AND `references/advanced-features.md` immediately. Output: "I'll split this into a Context diagram (high-level overview) and Component diagrams (zoomed views of specific domains)."

### Check 2: Directional Flow Validation
**Check for bi-directional or ambiguous relationships the user proposes.**

- **If user explicitly asks for `<-->` (bidirectional arrows)**: REJECT. Explain why and propose unidirectional split.
  - "Bidirectional arrows hide architectural coupling and conceal race conditions. Let me decompose this into two separate flows (OrderService → PaymentService for charge, PaymentService → OrderService for async webhook)."
- **If relationship direction is ambiguous**: Ask: "Does A call B synchronously, or is B asynchronously notified by A?"

**Action**: Load `references/faq-antipatterns.md` to get detailed explanations. Propose unidirectional or sequence diagram alternative.

### Check 3: Communication Mode Clarity
**For distributed systems, clarify sync vs async before routing.**

- **If not explicit**: Ask: "Are these services sync-first (HTTP/gRPC blocking calls) or async-first (event-driven via Kafka/RabbitMQ)?"
- **Why**: Determines whether to use direct arrows or queue/broker participants.

**Action**: Use answer to route appropriately (sequence diagram for complex async flows, C4 for architecture decision).

### Check 4: Scope Clarification
**Understand what the user wants to communicate.**

- "Do you need to show failure paths and compensation logic, or just the happy path?"
- "Is this for stakeholders (simplified) or technical team (detailed)?"
- "Should this diagram show internal implementation or just external integrations?"

**Action**: This informs depth and detail level of output.

---

## The Routing Matrix

After passing all anti-pattern checks above, evaluate the architectural problem and load EXACTLY ONE reference file.

| When the user needs to...                                                 | Load this reference               |
| :------------------------------------------------------------------------ | :-------------------------------- |
| Map out system boundaries, integrations, or deployment topologies         | `references/c4-diagrams.md`       |
| Design bounded contexts, aggregate boundaries, or domain logic            | `references/class-diagrams.md`    |
| Untangle distributed transactions, event choreography, or race conditions | `references/sequence-diagrams.md` |
| Normalize schemas, resolve polymorphic relations, or design data access   | `references/erd-diagrams.md`      |
| Map complex state machines, deployment pipelines, or business rule trees  | `references/flowcharts.md`        |

**MANDATORY**: Embed this exact trigger in your workflow before proceeding:
`MANDATORY — READ ENTIRE FILE: references/<file>.md`

**Do NOT load** multiple reference files. Pick the one that solves the core architectural question.

**CONDITIONAL**: If the requested architecture spans >20 nodes (confirmed in Check 1), you MUST also load `references/advanced-features.md`.

---

## Expert Anti-Patterns (The "NEVER" List)

**All items below are MANDATORY. If a user asks for any of these, reject the request and propose an alternative.**

- **NEVER create a "God Diagram":** If a diagram requires >20 nodes, it fails as a communication tool. Split it immediately into a Level 1 context diagram and multiple zoomed-in sub-diagrams. Do not ask permission to split; it is mandatory.
  - *Why*: Large diagrams become visual spaghetti. Line crossings prevent readers from tracing flows.
  - *Alternative*: Create L1 context (Person + System + External System only), then L2 component diagrams for each domain.

- **NEVER use bi-directional arrows (`<-->`) in architecture diagrams:** They hide architectural coupling and race conditions. Resolve them into two distinct unidirectional flows, or abstract the relationship to a higher level.
  - *Why*: Bidirectional arrows suggest both systems call each other, which is rare and indicates coupling. They hide which direction is blocking vs async.
  - *Alternative*: Model as two separate arrows (A → B for sync, B → A for async callback/webhook), or use a sequence diagram to show temporal causality.

- **NEVER model data when the user asks for behavior:** If a user asks "how does checkout work?", do not generate an ERD or a static class diagram. Use a sequence diagram to model the temporal flow of the checkout transaction.
  - *Why*: Architecture questions are about FLOW and COMMUNICATION, not structure. Data models are separate concerns.
  - *Alternative*: Use sequence diagram for behavior, ERD for data model; create both if needed but keep them separate.

- **NEVER assume synchronous communication:** In modern distributed systems, assume asynchronous queues/buses unless explicitly told it is a blocking HTTP/gRPC call. You MUST use the correct asynchronous arrow syntax.
  - *Why*: Synchronous calls create blocking dependencies and cascading failures. Async decoupling is the modern default.
  - *Alternative*: Explicitly ask "Are these sync or async?" If unclear, assume async and model the message broker as an explicit participant.

- **NEVER use standard generic colors for status indicators:** The diagram must be accessible. If a node represents a failure or a specific state, label it with text (e.g., `[FAILED: Auth]`), do not just color it red.
  - *Why*: Color-only status indicators are inaccessible to colorblind readers. Text labels are clear to everyone.
  - *Alternative*: Use text labels like `[ERROR: Timeout]` or `[DECLINED: Insufficient Funds]`.

---

## Automation & Validation

You MUST validate your architectures using these scripts. **Show the command and results to the user.**

### Validation Step
```bash
node ${CLAUDE_SKILL_DIR}/scripts/lint_diagram.js <file.mmd>
```
**Action**: Run this on every generated Mermaid file. If errors appear, fix them inline and re-validate before presenting to user. Show the command and output in your response.

### Preview Step
```bash
node ${CLAUDE_SKILL_DIR}/scripts/preview_diagram.js <file.mmd>
```
**Action**: Run this to generate an HTML preview. Provide the user with the file path so they can view it in a browser.

### Scaffolding (Optional)
```bash
node ${CLAUDE_SKILL_DIR}/scripts/scaffold_c4.js <project-dir>
```
**Action**: Use this when the user asks to "diagram this existing repo" or "analyze this codebase's architecture". It auto-generates a C4 scaffold from file structure.
