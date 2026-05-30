---
name: create-specs
description: |
  Use this skill whenever the user needs a clear, AI-ready technical specification. Always use it when the user mentions specs, requirements, contracts, interfaces, or asks 'what should we build?' before jumping to implementation. Use even if the spec is incomplete — this skill guides you through gathering what's needed. Applies to features, components, APIs, integrations, migrations, infrastructure changes, or any work that benefits from a written contract before coding starts. Seamlessly hands off to the `create-plan` skill. This is a required sub-skill of `spec-driven-development` — if the user is running the full SDD workflow, this skill is invoked at Step 2 (Specification Gate).
disable-model-invocation: true
---

# Create Specs

> **SDD Sub-Skill**: This skill is Step 2 of the `spec-driven-development` workflow. If you arrived here from that skill, complete this skill fully (including `validate_spec.py` and the self-check), then return to the SDD workflow at Step 3 (Planning Gate) and invoke `create-plan`.

## What This Skill Does

Produces a structured, unambiguous specification that documents:

- **What** must be built (requirements + constraints)
- **How** the solution connects to other systems (interfaces)
- **Why** these choices matter (context + risks)
- **When** it's done (acceptance criteria + validation)

The output is directly usable by AI agents or engineers to implement the solution, and feeds cleanly into the `create-plan` skill for step-by-step execution.

## When to Use This Skill

Always use this skill when:

- The user asks "what should we build?" or "can you write a spec?" before they want implementation steps
- Requirements or constraints exist but aren't yet written down
- You need to clarify vague requests (e.g., "add auth" → "what type of auth, where, with what tokens?")
- A feature needs a contract (API, data schema, CLI interface, or infrastructure) before coding
- The spec will be reviewed or shared with non-engineers

Skip this skill if: the user is asking a quick question, debugging existing code, or wants to learn a concept without building anything.

**Guardrails — edge cases during spec creation:**

- **User says "just build it"**: Pause and offer a 2-minute Sketch spec. If they decline, proceed without spec.
- **Conflicting requirements**: Document both sides with a `CONFLICT: [description]` note inline. Flag in Notes & Risks. Do not resolve conflicts by guessing.
- **User can't provide goal or scope**: Use the Spec Interview questions (see below) to extract one sentence. If still unclear, produce a Sketch with heavy `UNKNOWN` labels.
- **Requirements grow mid-spec**: Add them inline. Add a `NOTE: added during spec creation` comment. Do not restart the spec.
- **User rejects a section**: Mark it `SKIPPED: [user's reason]` in the spec. Do not omit it silently.

## Spec Maturity Levels

Specs come in three flavors — match the user's need:

| Level         | When                                 | Scope                                                              | Effort     |
| ------------- | ------------------------------------ | ------------------------------------------------------------------ | ---------- |
| **Sketch**    | Early idea, exploratory              | One or two key interfaces; fuzzy requirements                      | 15–30 min  |
| **Contract**  | Feature-ready, moderate complexity   | All interfaces, requirements, constraints, validation              | 30–60 min  |
| **Blueprint** | Production-critical, high complexity | Same as Contract + detailed error cases, migration steps, rollback | 60–120 min |

Ask the user: "Is this exploratory (sketch), ready to build (contract), or mission-critical (blueprint)?" Default to **Contract** unless they say otherwise.

**What each level requires from the template:**

| Level         | Required sections                                                                                                 | Optional sections                                          |
| ------------- | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| **Sketch**    | Goal, top 3–5 Requirements, rough Interfaces                                                                      | Constraints, Context, Acceptance Criteria, Examples, Notes |
| **Contract**  | All 8 sections; interface errors mandatory                                                                        | —                                                          |
| **Blueprint** | All 8 sections + detailed error cases, rollback strategy, migration steps, and a Mermaid diagram in Notes & Risks | —                                                          |

## Required Inputs

Before writing the spec, gather (or ask the user for):

- **Goal**: One sentence — what capability or outcome?
- **Scope**: Which system/component/API/file? What's in scope, what's out?
- **Constraints**: Budget, timeline, existing systems, team skill, compliance, security?
- **Interfaces**: What inputs does the user provide? What does the system return? Format?
- **Context**: Existing code, architecture, or platform conventions?

If the user can't answer everything, that's OK — document unknowns as `UNKNOWN` and move forward.

## Specification Template

Produce a markdown document with these 8 sections (in order):

### 1. Goal

- One sentence: what capability or outcome?
- One measurable completion signal (e.g., "Users can log in with their email").

### 2. Requirements

Use prefixed numbered statements. One obligation per requirement.

- `REQ-###`: Functional requirement (what the system must do)
- `SEC-###`: Security or privacy requirement
- `PERF-###`: Performance requirement (latency, throughput, memory)
- `COMP-###`: Compatibility, platform, or dependency requirement

**Example:**

- `REQ-001: The system MUST accept valid JSON payloads and return a deterministic response.`
- `REQ-002: The system MUST reject payloads missing required fields.`
- `SEC-001: All API requests MUST include a valid Bearer token in the Authorization header.`

### 3. Constraints

Define limits and non-goals — what the solution explicitly does NOT do.

- `CON-###`: State the limit or exclusion clearly.

**Example:**

- `CON-001: The solution MUST NOT create new database tables.`
- `CON-002: The response payload MUST NOT exceed 64 KB.`
- `CON-003: Authentication tokens MUST NOT be cached on the client.`

### 4. Interfaces

Define every public contract (API endpoint, function signature, data schema, CLI command, etc.).

For each interface:

- Name and method (if applicable)
- Input: parameters, schema, or shape
- Output: response, return value, or side effects
- Errors: status codes, error messages, exceptional cases

**Example:**

```
## POST /api/orders

**Input:** JSON object
- `customerId` (string, required): UUID of the customer
- `items` (array, required): List of items to order, each with `productId` (string) and `quantity` (integer > 0)

**Output:** JSON object
- `orderId` (string): Unique order identifier
- `status` (string): "pending" or "confirmed"
- `createdAt` (ISO 8601 timestamp)

**Errors:**
- `400 Bad Request`: Missing required fields or invalid schema
- `401 Unauthorized`: No valid Bearer token
- `503 Service Unavailable`: Downstream service failure
```

### 5. Context

Existing relevant code, architecture, or conventions.

- **Files**: Reference existing files that define current behavior (e.g., "See [src/auth/jwt.ts](src/auth/jwt.ts)")
- **Current behavior**: What exists today, what's missing
- **Conventions**: Naming, patterns, or standards this project follows
- **Platform/constraints**: Tech stack, dependency versions, deployment environment

### 6. Acceptance Criteria & Validation

Observable, testable signals that the implementation is complete.

**Acceptance Criteria** (what the user will see):

- `AC-001: Users can submit a valid order request and receive a 200 response with an orderId.`
- `AC-002: Invalid requests (missing fields) return a 400 response with a clear error message.`

**Validation Steps** (how you'll verify):

- `VAL-001: Run automated tests: `npm test -- orders.test.ts` (expect 0 failures).`
- `VAL-002: Manually submit an invalid request; confirm the API returns 400 with error details.`
- `VAL-003: Load test with 100 concurrent requests; confirm latency stays under 200ms.`

### 7. Examples & Edge Cases

Concrete input/output pairs and boundary cases.

**Positive Example:**

```
Input:  POST /api/orders with { customerId: "usr-123", items: [{ productId: "prod-456", quantity: 2 }] }
Output: { orderId: "ord-789", status: "pending", createdAt: "2026-05-18T14:30:00Z" }
```

**Edge Cases:**

- Quantity of 0 or negative numbers → 400 Bad Request
- Missing Authorization header → 401 Unauthorized
- Duplicate request with same body within 5 seconds → idempotent (return same orderId)
- Downstream service timeout (>5s) → 503 Service Unavailable

### 8. Notes & Risks (Optional)

Implementation risks, dependency updates, or rollout notes.

- `RISK-001: If the downstream order service is slow, implement request timeouts (currently unbounded).`
- `NOTE-001: Consider adding an audit log for all order creation attempts for compliance.`

## Spec Interview: Gathering Missing Requirements

If the user's request is vague or incomplete, ask these questions in order:

1. **Goal**: "What outcome or capability are you trying to enable? One sentence."
2. **Scope**: "What system or component does this touch? What's explicitly out of scope?"
3. **Constraints**: "Are there limitations: timeline, budget, existing systems, compliance, or tech stack?"
4. **Interface**: "How will users/other systems interact with this? What input do they provide, and what do they get back?"
5. **Success**: "How will you know it's done? What does the user see or do to verify it works?"

Document answers as you gather them. If the user can't answer something, mark it `UNKNOWN: [what and why]` and continue.

## Anti-Patterns (NEVERs)

- **NEVER use unmeasured adjectives or metaphors** ("lightweight", "robust", "fast"). They signal a lack of technical definition and lead to implementation drift. Use measurable thresholds instead.
- **NEVER include multiple obligations in one REQ.** If a requirement uses "AND" to join two distinct actions, split it. One obligation = one testable assertion.
- **NEVER skip error cases in interfaces.** The happy path is easy; specs exist to define how the system fails. Always define invalid inputs, auth failures, and timeouts.
- **NEVER resolve stakeholder conflicts by guessing.** If requirements contradict, document both with a `CONFLICT:` tag and escalate.
- **NEVER mix requirements and design.** Requirements dictate _what_ must happen; design dictates _how_. Move architectural decisions to the Context or Notes & Risks sections.

## Best Practices

**Keep constraints separate**: Requirements are "must do"; constraints are "must not do" or "must avoid". Don't mix them.

**No hidden assumptions**: If implementation detail or design decision isn't explicitly stated in the spec, don't assume it. Either write it down or leave it for planning.

**Use active voice**: "The system MUST validate…" not "Validation MUST be performed…". Active voice binds the obligation to a clear subject.

**Define acronyms**: First use "JWT (JSON Web Token)", then you can say "JWT" later.

**Label unknowns**: If something is genuinely unknown, write `UNKNOWN: [what and why]`. Don't guess.

## Available Scripts

Use these scripts to automate spec creation and validation:

- **`python ${CLAUDE_SKILL_DIR}/scripts/scaffold_spec.py [--level sketch|contract|blueprint] [--domain api|cli] [--goal "Goal sentence"]`**: Generates a standardized spec template with smart defaults.
- **`python ${CLAUDE_SKILL_DIR}/scripts/validate_spec.py <spec.md>`**: Validates structural integrity, requirement atomicity, active voice, and traceability (REQ -> AC -> VAL).

## Workflow: From Spec to Plan

1. **Scaffold the spec** using `${CLAUDE_SKILL_DIR}/scripts/scaffold_spec.py` to get the correct structure and domain snippets.
2. **Write the spec** following the generated template.
3. **MANDATORY - VALIDATE**: Run `python ${CLAUDE_SKILL_DIR}/scripts/validate_spec.py <your_spec.md>`.
   > **GATEKEEPER**: Implementation planning MUST NOT begin until `validate_spec.py` returns 0 errors. You MUST resolve all **ERRORS** before proceeding. Address **WARNINGS** where possible to improve quality.
   >
   > **Parser note**: The validator requires at least one line of body text directly under each `##` section heading before any `###` sub-headings. If `## 4. Interfaces` is followed immediately by `### POST /endpoint` with no intervening text, the parser will report a false "Missing mandatory section: Interfaces" error. Fix by adding one introductory sentence (e.g., "The system exposes the following endpoints:") before the first sub-heading.
4. **MANDATORY - READ ENTIRE FILE**: Run through `references/self-check.md` for a final manual quality pass.
5. **Review with stakeholder** (if applicable).
6. **Export as a file** (e.g., `spec-auth-jwt.md`).
7. **Use the `create-plan` skill** — pass the validated spec file as primary input. Highlight any `UNKNOWN:` items and `CONFLICT:` items that remain unresolved; create-plan will produce a task list keyed to the spec's REQ-### identifiers and will stall on any unresolved ambiguities.

The spec + plan together form a complete work package: spec says _what_ and _why_, plan says _how_ and _in what order_.

## Common Pitfalls

| Pitfall                                             | What happens                           | How to fix                                                                                         |
| --------------------------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Too vague (e.g., "REQ-001: Support authentication") | Implementations diverge; no clear test | Expand: "REQ-001: Support JWT-based authentication via Bearer tokens in Authorization header"      |
| Mixing requirements + design                        | Overconstrains implementation          | Separate: Requirement = "API must return 200 on success"; Design = how to structure the code       |
| Forgetting edge cases                               | Implementation handles only happy path | Always include: null/empty inputs, timeouts, permission errors, concurrent requests                |
| No clear success signal                             | Ambiguity in "done"                    | Write: "AC-001: User can log in with valid email/password and receive a JWT token in the response" |
| Spec not actionable for planning                    | `create-plan` stalls on ambiguity      | Ask: "Can I write a clear task list from this?" If not, add detail or mark gaps as UNKNOWN         |

## Domain-Specific Examples

See `references/domain-examples.md` for complete worked examples in these domains:

- **REST API specification** — Order creation API with full interfaces, error handling, and edge cases
- **Database schema specification** — User authentication schema with table definitions and constraints
- **CLI tool specification** — Migration management tool with command interfaces
- **Blueprint (distributed system)** — High-throughput event pipeline with Mermaid diagram, rollback, and migration steps
- **Template** — Blank structure you can copy for your own domain

**Blueprint Mermaid diagrams**: For the canonical format, see Example 4 in `references/domain-examples.md`. Use `graph TD` for data-flow diagrams (webhook → processor → database); use `sequenceDiagram` for request/response interaction flows. The diagram goes in the Notes & Risks section.

Use these as reference when writing specs for similar systems in your domain.

---

## Known Limitations

- Does not generate code or implementation artifacts — handoff to `create-plan` for that.
- Idempotency and concurrency edge cases in interfaces require domain knowledge; the skill prompts for them but cannot infer them from the problem statement alone.
- Blueprint specs for distributed systems may need supplemental architecture diagrams not produced by this skill.
