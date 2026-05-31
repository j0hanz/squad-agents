---
name: agents-maintainer
description: |
  Create, audit, refactor, or shorten AGENTS.md / CLAUDE.md / GEMINI.md and other agent-facing instruction files, or generate a codebase onboarding guide. Use when: user mentions agent docs, "instructions for Claude", project memory files, asks to "onboard me to this codebase" or "help me understand this repo", or an instruction file needs setup, trimming, deduplication, migration — or is over 100 lines, repeats linter rules, or drifts from real conventions.
disable-model-invocation: true
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

This is a three-phase Process. Do not skip phases.

### Express Mode (Skip Phases)

If the project environment is already well-understood (e.g., standard Node.js/TypeScript project, standard layout), you may skip the full 3-phase analysis:

1. Draft `AGENTS.md` directly using the appropriate template.
2. Run automated validation (Pass 1).
3. Finalize and wire (Phase 3).

*Note: If you skip Phase 1 and 1.5, you MUST explicitly ask the user to confirm the project stack (package manager, test runner) before finalizing.*

Run the analysis subcommands to instantly discover the project structure, tooling, and conventions.

```bash
python <skill-dir>/scripts/run.py analyze-env .
python <skill-dir>/scripts/run.py find-dependencies .
python <skill-dir>/scripts/run.py scan-structure . --max-depth 2
```

**What each subcommand does:**

- `run.py analyze-env` — Detects package manager, test runner, linter, monorepo structure
- `run.py find-dependencies` — Locates installed dependencies and their package locations (silent if none found)
- `run.py scan-structure` — Outputs directory tree while respecting .gitignore rules

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

**After Pass 1 PASS — spawn the `reviewer` subagent** (`agents/reviewer.md`):

```
Agent(
  description: "Semantic quality review of AGENTS.md",
  prompt: |
    agents_md_path: [absolute path to the AGENTS.md file]
    project_root: [project root directory, if available]
)
```

The agent scores the file on five semantic dimensions (signal density, convention specificity, command completeness, progressive disclosure, anti-pattern freedom) that the structural linter cannot catch. Review the returned `improvement_suggestions` sorted by `priority`. **Address all `high`-priority suggestions before Pass 2.** The `strengths` array confirms what to keep.

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

Use the `python <skill-dir>/scripts/run.py wire-agents AGENTS.md CLAUDE.md GEMINI.md` command. This script will safely attempt to create symlinks, and will automatically fall back to hardlinks or file copies if symlinks are not supported by the environment (e.g., on Windows without Developer Mode).

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
