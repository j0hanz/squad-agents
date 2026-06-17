---
name: agents-maintainer
description: "Create, audit, refactor, or trim AGENTS.md, CLAUDE.md, GEMINI.md, and onboarding guides. Trigger on 'agent docs', 'instructions', 'onboard me', 'understand this repo', 'setup AGENTS.md', 'this file is too long', 'trim CLAUDE.md', 'improve agent instructions', 'add conventions', 'update instructions file', or when the user shares an existing AGENTS.md/CLAUDE.md and asks to improve, review, or clean it up."
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash(python *) Bash(python3 *)
---

# agents-maintainer

Produces a lean, high-signal `AGENTS.md` (and symlinked `CLAUDE.md`/`GEMINI.md`) grounded in the _actual_ project — package manager, scripts, layout, conventions — not generic boilerplate.

The file is read into every agent's context on every turn. Every line costs tokens and attention. Treat it like a hot config file, not human documentation.

## Mental model

This file runs in every agent context, every turn.
Every token competes with the user's actual request.
Design for a reader who is skimming at 200 words per second.

## Workflow

This is a three-phase process. Do not skip phases.

> **Resolving `<skill-dir>`:** Every script command below uses `<skill-dir>` as a placeholder for the absolute path to this skill's directory. In Claude Code, resolve it as `$CLAUDE_PLUGIN_ROOT/skills/agents-maintainer` or use the path returned by the skill loader. Example: `python /home/user/.claude/skills/agents-maintainer/scripts/run.py analyze-env .`

### Express Mode (Skip Phases)

Use Express Mode only when ALL of the following are true:

- The tech stack is explicitly named and standard (e.g., "Next.js 15 + pnpm + Vitest")
- The project layout matches the named stack's defaults (no custom structure)
- The user confirms they want a quick draft

If any condition is uncertain, run the full 3-phase workflow.

**Express Mode steps:**

1. Ask the user to confirm: package manager, test runner, any non-standard conventions.
2. Draft `AGENTS.md` directly using the appropriate template.
3. Run automated validation (Pass 1).
4. Finalize and wire (Phase 3).

_Do not skip Phase 1 and assume a stack without confirmation — AGENTS.md built on wrong assumptions silently misleads every agent that loads it._

### Phase 1 — Environment Discovery

Run these analysis subcommands against the project root to discover its structure, tooling, and conventions:

```bash
python <skill-dir>/scripts/run.py analyze-env .
python <skill-dir>/scripts/run.py find-dependencies .
python <skill-dir>/scripts/run.py scan-structure . --max-depth 2
```

Or run all three at once:

```bash
python <skill-dir>/scripts/run.py analyze-all . --max-depth 2
```

**What each subcommand does:**

- `run.py analyze-env [dir]` — Detects package manager, test runner, linter, monorepo structure
- `run.py find-dependencies [dir]` — Locates installed dependency directories with sizes (silent if none found)
- `run.py scan-structure [dir] [--max-depth N]` — Outputs directory tree while respecting .gitignore rules
- `run.py analyze-all [dir] [--max-depth N]` — Runs all three above sequentially

If a project signal is missing or ambiguous, ask the user before guessing. NEVER hallucinate test runners or linters.

If any command fails to run, fall back to manual inspection using these parallel checks:

1. **Package manifests**: `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`, `pom.xml`, `build.gradle`, `Gemfile`, `composer.json`, `mix.exs`, `pubspec.yaml`
2. **Framework fingerprinting**: `next.config.*`, `nuxt.config.*`, `angular.json`, `vite.config.*`, django settings, flask app factory, fastapi main, rails config
3. **Entry points**: `main.*`, `index.*`, `app.*`, `server.*`, `cmd/`, `src/main/`
4. **Config & tooling**: `.eslintrc*`, `.prettierrc*`, `tsconfig.json`, `Makefile`, `Dockerfile`, `docker-compose*`, `.github/workflows/`, CI configs
5. **Test structure**: `tests/`, `test/`, `__tests__/`, `*_test.go`, `*.spec.ts`, `*.test.js`, `pytest.ini`, `jest.config.*`, `vitest.config.*`

### Phase 1.5 — Architecture & Convention Mapping

**MANDATORY — READ ENTIRE FILE**: `references/phase-1.5-architecture.md` — architecture pattern detection, tech stack extraction, and template selection decision tree. Do NOT skip this phase.

### Phase 2 — Draft AGENTS.md

**MANDATORY — READ Section 1 of `references/guide.md`** before composing your draft.

You now have Phase 1.5 findings. Use the decision tree below to select the right template, then compose only the sections your project needs.

#### Choose Your Template

Use the template selected in Phase 1.5 (`references/phase-1.5-architecture.md`), then customize:

1. Keep all **required sections** (see table in "Required sections" below)
2. Include **optional sections** that apply (API Patterns, CLI Commands, etc.)
3. Delete optional sections that don't apply
4. Add **project-specific conventions** (3-7 bullets; see "Key Conventions" examples in guide.md)

**Core principles:**

- **Headers + bullets + tables + code blocks.** No paragraphs of prose. Agents skim, not read.
- **Reference, don't embed.** "See `CONTRIBUTING.md` for setup" beats restating setup. The agent will read the linked file if needed.
- **Document storage locations.** Explicitly state where dependencies and virtual environments live (e.g., "Dependencies are in `.venv`"). This helps agents understand the workspace environment and avoid accidental deletion or re-installation.
- **Don't restate linter configs.** If `.eslintrc` says no `console.log`, that's the linter's job. Lint output will surface it.
- **NEVER list auto-discovered tools.** Do NOT document the number of MCP tools, resources, or prompts. The agent already knows its capabilities via the system prompt.
- **Prefer file-scoped commands.** `pnpm tsc --noEmit src/foo.ts` is 10× cheaper than `pnpm build`. Always include the per-file versions when the toolchain supports them.
- **Progressive disclosure.** Move language rules, framework conventions, and detailed guidelines to referenced files (`docs/TESTING.md`, `docs/TYPESCRIPT.md`). Root AGENTS.md references them with a one-liner: _"For TypeScript conventions, see `docs/TYPESCRIPT.md`"_. Rules load only when relevant — other tasks pay no token cost.
- **Capabilities over structure.** Describe what modules _do_, not where files _live_. File trees go stale and agents can `ls`. Point at 2-3 critical files to read — not a directory listing.
- **Instruction budget.** Frontier models follow ~150-200 instructions reliably. Every line competes with actual task instructions. When in doubt, cut or link.
- **Human Onboarding Guide (Optional):** If the user explicitly asks for help understanding the codebase ("onboard me", "explain this repo"), generate an **Onboarding Guide** in chat before finalizing AGENTS.md. It should cover: Overview, Tech Stack, Directory Map, Request Lifecycle, and Conventions. Keep it scannable.

### Phase 3 — Validate & Wire

Validation happens in **two passes**: automated checks, then manual review.

#### Pass 1: Automated Linter (Quick)

Run this first:

```bash
python <skill-dir>/scripts/run.py lint-agents-md <path/to/AGENTS.md>
```

The linter checks:

- ✓ File length (≤ 100 lines)
- ✓ H1 header present
- ✓ One-sentence project description after header
- ✓ No filler text ("Welcome to…", "This document…")
- ✓ No auto-discovery references (tool counts, MCP servers)
- ✓ No generic advice ("test thoroughly", "be careful", "remember to")
- ✓ `Co-Authored-By:` attribution present

**If linter fails:** Fix issues and rerun. Don't proceed to Pass 2 until PASS.

**After Pass 1 PASS — dispatch a `general-purpose` subagent for semantic review:**

```
Agent(
  subagent_type: "general-purpose",
  description: "Semantic quality review of AGENTS.md",
  prompt: |
    SCOPE: Read [absolute path to the AGENTS.md file] in full. Read [project root, if available] only to verify claims.
    OBJECTIVE: Score the file on five quality dimensions and return ranked improvement suggestions with direct quotes.
    CONTEXT:
      1. Signal Density — does every line tell the agent something not derivable from code?
      2. Convention Specificity — does each bullet answer WHAT/WHERE/WHY with concrete patterns?
      3. Command Completeness — are typecheck/lint/test commands runnable verbatim?
      4. Progressive Disclosure — is the file focused and under 100 lines (linking out for depth)?
      5. Anti-pattern Freedom — free of filler, auto-discovery refs, linter-restating?
    CONSTRAINTS:
      - PASS on any dimension requires direct observable evidence in the file — not intent or inference.
      - Propose the concrete rewrite for every suggestion — never just "improve this".
    OUTPUT: JSON ONLY — no prose, no markdown wrappers. Fields: scores (0-10 per dimension), strengths[], improvement_suggestions[] each with {priority: high|medium|low, quote, rewrite}.
)
```

Review the returned `improvement_suggestions` sorted by `priority`. **Address all `high`-priority suggestions before Pass 2.** The `strengths` array confirms what to keep.

#### Pass 2: Manual Checklist (Thorough)

Even after linter PASS, work through this checklist manually:

- [ ] **No section duplication** — Does any section restate something the agent will read anyway (config files, README)?
- [ ] **Commands verified** — Did you actually run each command in your environment to confirm it works?
- [ ] **File-scoped variants present** — For tools that support it (tsc, eslint, pytest), are per-file versions included? (Omit rows if toolchain doesn't support)
- [ ] **Conventions are specific** — Each bullet is actionable, not vague. "Imports sorted by stdlib → third-party → local" ✓, "Keep imports clean" ✗
- [ ] **Prose-free** — Only headers, bullets, tables, code blocks. No multi-line paragraphs.
- [ ] **No orphaned links** — Every reference (e.g., "See `CONTRIBUTING.md`") actually exists in the repo.

If any checklist item fails, go back to Phase 2 and refine.

**MANDATORY — READ ENTIRE FILE:** `references/guide.md` to finish wiring.

Use the `wire-agents` subcommand to wire `AGENTS.md` to agent-specific files. It attempts symlink first, then hardlink, then file copy:

```bash
python <skill-dir>/scripts/run.py wire-agents AGENTS.md CLAUDE.md GEMINI.md
```

As a final gut-check: would any section be embarrassing on a code review for being obvious or vague? If yes, cut it.

## Required sections

Every AGENTS.md MUST have these. Skip anything else unless it earns its place.

| Section                            | Rule                                                                                                                                                                          |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Top-Level Header**               | MUST begin with `# Agent Instructions` or `# <ProjectName> Agent Instructions`.                                                                                               |
| **Project description**            | One sentence immediately following the header. Anchors every agent decision. No paragraphs.                                                                                   |
| **Package manager + key commands** | What to use and why if the reason is non-obvious (e.g., "`npm install` will break the lockfile").                                                                             |
| **Dependency Locations**           | Document where dependencies are stored (e.g., `node_modules`, `.venv`) IF non-standard or relevant for agent environment setup/inspection.                                    |
| **File-scoped commands**           | Table of typecheck / lint / test commands targeting a single file. Omit rows the toolchain can't do.                                                                          |
| **Commit attribution**             | `Co-Authored-By:` trailer with the agent model's name and byline.                                                                                                             |
| **Key conventions**                | 3–7 bullets of project-specific patterns not enforced by linters (e.g., naming conventions, error handling styles, testing patterns). More than 7 is a documentation problem. |

See Section 1 of `references/guide.md` for formatted examples of each section.

## Writing "Key Conventions" (Best Practices)

The "Key conventions" section is critical because it captures what the linter _can't_ enforce. Write them to be **specific and actionable**, not vague:

### ❌ Bad Conventions (Vague, Not Actionable)

- "Use descriptive names" — Descriptive how? For what?
- "Follow best practices" — Which practices?
- "Test thoroughly" — How much is "thoroughly"?
- "Handle errors gracefully" — Graceful how? Log, retry, bail?
- "Keep naming consistent" — Consistent with what pattern?

### ✅ Good Conventions (Specific, Verifiable)

- "API handlers end with `.handler.ts` (e.g., `login.handler.ts`); utilities are generic"
- "Error handling: All errors inherit from `AppError` in `src/errors.ts`; include `statusCode` and `userMessage`"
- "Database: Never edit applied migrations; use `pnpm migrate create --name feature` for new migrations"
- "Testing: Every async function has an integration test. Sync utilities only need unit tests"
- "Async patterns: Use `async/await` in routers and services; callbacks in middleware"
- "Dependency injection: Constructor injection only (no `@Autowired` field injection)"
- "API routes: Keep HTTP concerns separate from business logic; routers import services, not vice versa"

### The 3-7 Bullet Rule

- **3 bullets:** Minimum to be useful
- **5-7 bullets:** Sweet spot for comprehensive guidance without overload
- **>7 bullets:** Too many; move extras to `docs/PATTERNS.md` and link from AGENTS.md

### Writing Template

For each convention bullet, answer:

1. **What:** The pattern or rule
2. **Where:** Location or context (if applicable)
3. **Why:** Brief reason (optional, but helps justify the rule)

Example:

> "API routes: HTTP validation and response formatting in handlers; business logic in services. Keeps concerns separate and makes services reusable."

## Optional sections (only if they earn it)

- **API / route patterns** — show one tiny template, not an explanation
- **CLI commands** — table format
- **File naming** — only if non-standard (e.g. `*.handler.ts` not `*Handler.ts`)
- **Critical files** — point at 2-3 files an agent must read before changing related code
- **Legacy/avoid** — flag dead code or deprecated patterns

## Anti-patterns

**MANDATORY — READ ENTIRE FILE:** `references/guide.md` if you are refactoring an existing instructions file.

The most common failure modes and _why_ they hurt are documented in `references/guide.md`. Read it once if you're refactoring an existing file — the patterns there are what you're cutting.

**NEVER include the following in agent instructions:**

- **NEVER** include "Welcome to…" / "This document explains…" intros. Agents do not need warmth or warmup.
- **NEVER** restate linter rules already in config files (e.g. "Use 2 spaces"). Rely on the linter instead.
- **NEVER** list skills, plugins, or tools the agent auto-discovers. The system prompt provides these.
- **NEVER** provide full project-wide build commands for testing if file-scoped commands exist.
- **NEVER** give generic instructions ("write clean code", "test thoroughly").
- **NEVER** write prose paragraphs explaining philosophy. Skimmability is destroyed.
- **NEVER** leave stale TODOs and "we should eventually…" notes. The agent will try to action them immediately.

## Examples

**DO load** `references/guide.md` when the user shows you an existing bloated file and asks to trim or refactor it.
**Do NOT load** `references/guide.md` when drafting from scratch with clear project signals — the templates are sufficient.
