# Skill Routing Guide

This guide is the authoritative reference for finding and using the skills, agents, and slash commands shipped with the `agent-dev` plugin.

---

## Instruction Priority

1. **User's explicit instructions** (CLAUDE.md, AGENTS.md, direct requests) — highest priority
2. **Agent-dev skills** — override default behavior where they conflict
3. **Default system prompt** — lowest priority

---

## Process-First Rule (Skill-First)

**Invoke process skills (brainstorming, planning) before implementation skills (refactor, code-review) and before any direct action.** Process skills tell you HOW to approach a task; implementation skills tell you HOW to execute it.

```
User message → Might any skill apply? → YES → Invoke Skill tool → Follow skill
                                       → DEFINITELY NOT → Respond directly
```

### Skill Priority Order

1. **Process skills first** (brainstorming, planning, diagnose) — determine HOW to approach
2. **Implementation skills second** (refactor, code-review, test-driven-development) — guide execution

- "Let's build X" → `brainstorming` first, then implementation skills.
- "Fix this bug" → `diagnose` first, then domain skills.

**When to skip skill invocation**: If none of the skills in the Skill Routing Map applies, respond directly. If the task is a single-word search, a clarifying question, or retrieving a file path — no skill is needed.

---

## Skill Routing Map

The remaining 13 skills are organized by category:

### Process / Methodology Skills

| Skill                            | Invoke when…                                                                                     | Output                               |
| -------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------ |
| `brainstorming`                  | Starting any new feature, component, agent, skill, or hook. **Required before design approval.** | Design table + approval              |
| `planning`                       | Writing formal specs AND an atomic implementation plan together.                                 | `<name>.specs.md` + `<name>.plan.md` |
| `test-driven-development`        | Implementing logic using the red-green-refactor discipline.                                      | Unit tests + passing code            |
| `skill-builder`                  | Creating, testing, improving, or evaluating a skill.                                             | `SKILL.md` + evals                   |
| `create-agent`                   | Designing a new managed agent (system prompt, tools, model).                                     | Agent definition                     |
| `create-hook`                    | Designing or implementing a lifecycle hook handler.                                              | Hook handler + tests                 |
| `verification-before-completion` | **MANDATORY** before any done claim. Runs verification checks.                                   | Verified test results                |
| `architecture`                   | Checking code locality, coupling, or module boundary decisions.                                  | Dependency scan results              |

### Domain / Execution Skills

| Skill         | Invoke when…                                                           | Output              |
| ------------- | ---------------------------------------------------------------------- | ------------------- |
| `code-review` | Reviewing a diff or PR for correctness, security, or API hygiene.      | Review findings     |
| `refactor`    | Cleaning up code without behavior change (e.g., poor naming, nesting). | Refactored code     |
| `diagnose`    | Debugging a failure, tracing a runtime error, or reproducing bugs.     | Root-cause analysis |

### Lifecycle / Ops Skills

| Skill               | Invoke when…                                                      | Output                    |
| ------------------- | ----------------------------------------------------------------- | ------------------------- |
| `agents-maintainer` | Keeping AGENTS.md and CLAUDE.md in sync after structural changes. | Updated instruction files |

---

## Managed Agents

Delegate to agents for isolated, autonomous work. Each runs in its own context — give it everything it needs in the prompt, because it has no access to the parent session.

- **Explorer:** Read-only code search and repository mapping (Sonnet model, low cost).
- **Coder:** Autonomous code execution and implementation (writes to separate git worktrees).
- **Detective:** Root-cause analysis of runtime bugs, failures, and compile errors.
- **Documenter:** Auditing, writing, and updating documentation files, READMEs, and ADRs.

---

## Slash Commands

| Command       | Invokes               | When to Use                                             | Output                         |
| ------------- | --------------------- | ------------------------------------------------------- | ------------------------------ |
| `/brainstorm` | `brainstorming` skill | Start any new feature, component, agent, skill, or hook | Design table + approval        |
| `/coder`      | `coder` agent         | Autonomous code execution for multi-file tasks          | Worktree branch with changes   |
| `/detective`  | `detective` agent     | Root-cause analysis of bugs or failures                 | Structured bug report          |
| `/explore`    | `explorer` agent      | Read-only code search and symbol lookups                | Search results                 |
| `/fix`        | `diagnose` skill      | Debug a runtime failure or logic bug                    | Root cause analysis with diffs |
| `/hook`       | `create-hook` skill   | Design or implement a lifecycle hook                    | Hook handler code + test cases |
| `/pr`         | `code-review` skill   | Review a diff or PR for quality issues                  | Review findings                |

---

## Output Style: Phase Discipline

Every work session follows four phases. **Do not skip phases or merge them.**

### 1. Design Phase

- State the component type, trigger condition, and approach in a table **before writing any code**.
- Get explicit design approval from the user before proceeding.
- Governed by the `brainstorming` skill.

### 2. Build Phase

- One-line intent, then act — no preamble.
- Every claim about existing code includes a `file:line` citation.
- Sequential file edits only — one edit per turn per file.

### 3. Validate Phase

- Report as `PASS` or `FAIL`.
- Each failure is a triple: **component → rule violated → specific fix**.
- Run `npm validate` and `npm test` before marking complete.

### 4. Ship Phase

- List artifacts produced and what the next session can build on.
- Commits assisted by AI must include the required attribution trailer.

---

## Commit Attribution — Required on Every AI Commit

Every commit made with AI assistance MUST include this trailer:

```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## If You're Stuck

- **Can't find a skill?** Use the Quick Lookup table in the Skill Routing Map or browse by category.
- **Skill output confusing?** Check the skill's `SKILL.md` file for examples and guidance.
- **Phase discipline unclear?** See the worked example in the Phase Discipline section of the documentation.
- **Error occurred?** Check compile logs, test errors, or verify lint rules manually.
