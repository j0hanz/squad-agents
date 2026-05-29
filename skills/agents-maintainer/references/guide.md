# Agent Maintenance Reference Guide

This guide contains everything you need to draft, refactor, and wire `AGENTS.md` files (and their variants like `CLAUDE.md`, `GEMINI.md`, etc.).

## 1. Templates

Adapt these templates to the project shape. Every command and convention must come from the actual repo, not the template.

### Base template (single-package JS/TS)

```markdown
# Agent Instructions

## Package Manager

Use **pnpm** — `pnpm install`, `pnpm dev`, `pnpm test`. `npm install` will break the lockfile.

## Dependency Locations

- Node dependencies: `node_modules/`

## File-Scoped Commands

| Task      | Command                             |
| --------- | ----------------------------------- |
| Typecheck | `pnpm tsc --noEmit path/to/file.ts` |
| Lint      | `pnpm eslint path/to/file.ts`       |
| Test      | `pnpm jest path/to/file.test.ts`    |

## Key Conventions

- API routes live in `src/api/routes/` — follow patterns there
- Errors thrown from handlers are caught by `src/middleware/error.ts`
- DB migrations: `pnpm migrate create <name>`, never edit applied migrations

## Commit Attribution

AI commits MUST include a `Co-Authored-By:` trailer with the agent model's name and byline.
Example: `Co-Authored-By: Claude Opus 4 <noreply@anthropic.com>`
```

### Monorepo (pnpm workspaces / Turborepo)

Add this on top of the base template.

```markdown
## Workspace Layout

| Package     | Path          | Purpose       |
| ----------- | ------------- | ------------- |
| `@acme/api` | `apps/api`    | HTTP API      |
| `@acme/db`  | `packages/db` | Prisma client |

## Dependency Locations

- Root dependencies: `node_modules/`
- Workspace packages: `apps/*/node_modules`, `packages/*/node_modules`

## Cross-Package Commands

- Run script in package: `pnpm --filter @acme/api test`
- Run across all: `pnpm -r build` (uses Turbo cache)

Each package may have its own `AGENTS.md` with overrides.
```

#### Monorepo: Package-Level AGENTS.md Overrides

If a package uses different tooling, create a package-level AGENTS.md. Example:

**File: `apps/api/AGENTS.md`**
```markdown
# @acme/api Agent Instructions

See root `/AGENTS.md` for shared setup and workspace commands.

## Override: Test Runner

This package uses Mocha instead of Jest:

| Task | Command |
| Test | `mocha --require ts-node/register src/**/*.test.ts` |
| Test (one file) | `mocha --require ts-node/register src/auth/test_login.test.ts` |

All other conventions apply from root AGENTS.md.
```

**When to Create Package-Level AGENTS.md:**
- ✓ Package uses different test runner, linter, or build tool than root
- ✓ Package has unique setup requirements
- ✗ Don't duplicate root sections; reference root instead

### Python (uv / poetry / pip)

```markdown
# Agent Instructions

## Package Manager

Use **uv** — `uv sync`, `uv run pytest`, `uv add <pkg>`. Don't use raw `pip install`.

## Dependency Locations

- Python virtual environment: `.venv/`
- Site packages: `.venv/lib/python3.x/site-packages/`

## File-Scoped Commands

| Task      | Command                                         |
| --------- | ----------------------------------------------- |
| Typecheck | `uv run mypy path/to/file.py`                   |
| Lint      | `uv run ruff check path/to/file.py`             |
| Test      | `uv run pytest path/to/test_file.py::test_name` |

## Key Conventions

- Public API lives in `src/<pkg>/__init__.py` — keep `__all__` in sync
- Settings: `src/<pkg>/config.py` uses pydantic-settings.

## Commit Attribution

AI commits MUST include a `Co-Authored-By:` trailer.
```

### Go

```markdown
# Agent Instructions

## Package Manager
Use **Go Modules** — `go mod tidy`, `go build`, `go test`.

## Dependency Locations
- Vendored dependencies: `vendor/` (if used)
- Module cache: `$GOPATH/pkg/mod`

## File-Scoped Commands

| Task | Command |
| ---- | ------- |
| Lint | `golangci-lint run path/to/file.go` |
| Test | `go test -run TestName path/to/package` |

## Key Conventions
- Place binaries in `cmd/`
- Follow idiomatic Go error handling: `if err != nil { return err }`

## Commit Attribution
AI commits MUST include a `Co-Authored-By:` trailer.
```

### Rust (Cargo)

```markdown
# Agent Instructions

## Package Manager
Use **Cargo** — `cargo build`, `cargo test`, `cargo clippy`.

## Dependency Locations
- Build artifacts: `target/`

## File-Scoped Commands

| Task | Command |
| ---- | ------- |
| Lint | `cargo clippy --package <pkg_name> -- -D warnings` |
| Test | `cargo test --package <pkg_name> test_name` |

## Key Conventions
- Use `Result<T, E>` for error handling.
- Documentation comments should use `///`.

## Commit Attribution
AI commits MUST include a `Co-Authored-By:` trailer.
```

### Spring Boot (Java)

```markdown
# Agent Instructions

## Package Manager

Use **Maven** — `mvn clean install`, `mvn test`. Or **Gradle** — `gradle build`, `gradle test`.

## Dependency Locations

- Maven: `target/` (build), `~/.m2/repository` (cache)
- Gradle: `build/` (build), `~/.gradle` (cache)

## File-Scoped Commands

| Task | Command |
| ---- | ------- |
| Compile | `mvn compile -pl :<module_name>` or `gradle -p :<module> build` |
| Test | `mvn test -Dtest=TestClass#testMethod -pl :<module>` |

## Key Conventions

- API endpoints: Use `@RestController` in `src/main/java/com/...controller/` package
- Error handling: Custom exceptions inherit from `ApplicationException`; include HTTP status + message
- Database migrations: Use Flyway or Liquibase in `src/main/resources/db/migration/`
- Dependency injection: Prefer constructor injection over field injection

## Commit Attribution

AI commits MUST include a `Co-Authored-By:` trailer.
```

### .NET / C#

```markdown
# Agent Instructions

## Package Manager

Use **dotnet** — `dotnet restore`, `dotnet build`, `dotnet test`.

## Dependency Locations

- NuGet: `~/.nuget/packages`
- Build: `bin/`, `obj/`

## File-Scoped Commands

| Task | Command |
| ---- | ------- |
| Build | `dotnet build -p :<ProjectName>` |
| Test | `dotnet test --filter FullyQualifiedName~TestClassName` |

## Key Conventions

- Async methods: End with `Async` suffix; use `async/await` throughout
- Dependency injection: Configure in `Program.cs`; use constructor injection
- Error handling: Custom exception types; use `Result<T>` or exceptions (pick one consistently)
- Migrations (EF Core): `dotnet ef migrations add <name>`, never edit applied migrations

## Commit Attribution

AI commits MUST include a `Co-Authored-By:` trailer.
```

### Bun

```markdown
# Agent Instructions

## Package Manager

Use **bun** — `bun install`, `bun run`, `bun test`. Fast JavaScript runtime.

## Dependency Locations

- Modules: `node_modules/`

## File-Scoped Commands

| Task | Command |
| ---- | ------- |
| Test | `bun test path/to/file.test.ts` |
| Run | `bun path/to/file.ts` |

## Key Conventions

- Test runner: Built-in, no Jest config needed
- Prefer native Bun APIs (`Bun.file()`, `Bun.write()`) over Node equivalents when possible
- Scripts run with `--hot` flag for file-watch mode

## Commit Attribution

AI commits MUST include a `Co-Authored-By:` trailer.
```

### Polyglot / Multi-Language Projects

For projects combining multiple languages, create **language-specific sections** within one AGENTS.md, or **separate AGENTS.md per subsystem** if toolchains differ significantly.

#### Single AGENTS.md Approach (Shared Conventions)

```markdown
# Agent Instructions

## Overview

This project spans Python (API) and TypeScript (Frontend).

## Shared Conventions
- Error handling: All errors include unique error code + user-facing message
- Testing: Both suites use same coverage thresholds (80% minimum)

## Backend (Python + FastAPI)

### Package Manager
Use **uv**: `uv sync`, `uv run pytest`

### File-Scoped Commands
| Task | Command |
| Test | `uv run pytest src/api/test_*.py::test_name` |

## Frontend (TypeScript + React)

### Package Manager
Use **pnpm**: `pnpm install`, `pnpm test`

### File-Scoped Commands
| Task | Command |
| Test | `pnpm jest src/components/__tests__/Button.test.tsx` |
```

#### Separate AGENTS.md per Subsystem

If languages have very different toolchains:

```
project-root/
├── AGENTS.md (shared conventions only)
├── backend/
│   ├── AGENTS.md (Python-specific)
│   └── [Python code]
└── frontend/
    ├── AGENTS.md (TypeScript-specific)
    └── [React code]
```

See monorepo section for how to structure package-level overrides.

## 2. Anti-Patterns (What to Cut)

When refactoring, aggressively remove these:

- **Intros/Warmups:** Delete "Welcome to..." or "This document explains...". Agents don't need warmups.
- **Linter/Formatter Rules:** Delete "Use 2 spaces", "Prefer const". Let the linter enforce these.
- **Auto-discovered Tools:** Don't list MCP servers or tools the agent already knows about.
- **Full Project Builds:** Prefer file-scoped commands (e.g., `tsc --noEmit single-file.ts`) over `pnpm build`.
- **Generic Instructions:** Delete "Write clean code", "Test thoroughly". Be specific or delete.
- **Prose Explanations:** Convert paragraphs into concise bullets. Agents skim.
- **Stale TODOs:** Delete "TODO: migrate to Vite". Agents will try to action them immediately.
- **Repeating README/CONTRIBUTING:** Link to them instead (`See CONTRIBUTING.md for branch naming.`).
- **File Trees:** Point to 2-3 critical files instead of pasting a massive `ls` output.
- **Auto-generated Boilerplate:** Delete anything not specifically grounded in the _current_ repo.

## 2.5 Key Conventions: Good vs. Bad Examples

The "Key conventions" section should capture patterns the linter can't enforce. Here's what works and what doesn't:

### Bad Conventions (Vague, Unverifiable)

```markdown
- Use descriptive names
- Follow best practices
- Be careful with error handling
- Test everything
- Keep it simple
- Think about performance
```

**Why these fail:**
- "Descriptive names" — Can't verify. Descriptive for what? `login_handler` vs. `auth` vs. `handleLogin`?
- "Best practices" — Vague. Which practices? A list of 100?
- "Be careful" — Subjective. No way to test compliance.
- "Test everything" — Undefined. Unit only? Integration? End-to-end?
- "Keep it simple" — Can't measure. Simple by what standard?

### Good Conventions (Specific, Verifiable)

```markdown
- **File naming:** Handlers end with `.handler.ts`, utilities end with `.util.ts`. Example: `login.handler.ts`, `date.util.ts`
- **Error handling:** All errors inherit from `AppError` (see `src/errors.ts`). Include `statusCode` (HTTP) and `userMessage` (user-facing).
- **Testing:** Every exported function has a test. Every async function has an integration test. Sync utilities only need unit tests.
- **Database migrations:** Never edit applied migrations. Create new migrations with `pnpm migrate create --name feature_name`.
- **API patterns:** Routers call services; services return data (not HTTP responses). HTTP formatting in handlers only.
- **Dependency injection:** Constructor injection only. No field injection (`@Autowired`) or service locators.
```

**Why these work:**
- Specific file patterns (`*.handler.ts`, `*.util.ts`)
- Clear class/interface inheritance (`extends AppError`)
- Measurable coverage rules ("every async function")
- Concrete locations (`src/errors.ts`)
- Clear examples and counter-examples
- Verifiable from code review

### The 3-7 Bullet Rule

Aim for **5-7 conventions**:
- **Too few (<3):** Not enough guidance; agents have to guess
- **Sweet spot (5-7):** Comprehensive but scannable; agents can remember them
- **Too many (>7):** Overwhelming; move to detailed docs and link

If you have 10+ conventions, that's a signal that:
1. Your codebase has too many unwritten rules, OR
2. You should document them in `docs/CONVENTIONS.md` and link from AGENTS.md

### Writing Checklist

For each convention, verify:
- [ ] **Specific:** Can someone verify compliance by reading code?
- [ ] **Location aware:** Include file/folder if applicable (e.g., `src/errors.ts`)
- [ ] **Actionable:** An agent could follow this rule without asking for clarification
- [ ] **Not a linter rule:** Linter configs should enforce, not AGENTS.md
- [ ] **Not generic:** Avoid "write clean code", "be careful", "best practices"

## 3. Scripts Reference

Helper scripts are available via `scripts/run.py`:

```bash
python scripts/run.py <command> [args]
```

- `analyze-all [target_dir] [--max-depth 3]` — Run analyze-env, find-dependencies, and scan-structure sequentially
- `analyze-env [target_dir]` — Detect package manager, test runner, linter, monorepo structure
- `find-dependencies [target_dir]` — Locate installed dependency directories
- `scan-structure [target_dir] [--max-depth 3]` — Output directory tree (respects .gitignore)
- `lint-agents-md <path_to_AGENTS.md>` — Validate AGENTS.md length, filler text, commit attribution
- `wire-agents <source_file> <target1> [target2...]` — Create symlink/hardlink/copy fallbacks

## 4. File Setup & Symlinking

Create a canonical `AGENTS.md` and link agent-specific files to it. Use the provided wiring script to safely handle platform differences (especially on Windows):

```bash
python scripts/run.py wire-agents AGENTS.md CLAUDE.md GEMINI.md
```

This script will attempt to create symlinks, and will automatically fall back to hardlinks or file copies if symlinks are not supported by the environment.

| Agent / tool           | File it looks for                   |
| ---------------------- | ----------------------------------- |
| OpenAI Codex / generic | `AGENTS.md`                         |
| Claude Code            | `CLAUDE.md`                         |
| Gemini CLI             | `GEMINI.md`                         |
| Cursor                 | `.cursorrules` or `.cursor/rules/*` |

**Cursor:** `.cursorrules` requires plain text; copy the body of `AGENTS.md` into it.

## 5. Refactoring Examples

### Before (Bloated)

```markdown
# Welcome to FooBar

This project is built with TS, React, and PG. We love clean code.

- Use 2 spaces
- Always use semicolons
- Run `pnpm test` to run all tests
```

### After (Lean)

```markdown
# Agent Instructions

## Package Manager

Use **pnpm**.

## File-Scoped Commands

| Task | Command                          |
| ---- | -------------------------------- |
| Test | `pnpm jest path/to/file.test.ts` |

## Commit Attribution

AI commits MUST include a `Co-Authored-By:` trailer.
```
