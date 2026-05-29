# Phase 1.5 — Architecture & Convention Mapping

From the Phase 1 reconnaissance data, extract these specific signals **before** proceeding to Phase 2.

## Architecture Pattern Detection

Use file structure to identify the pattern:

| Pattern                   | Detection Signals                                                                             | Example                          |
| ------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------- |
| **MVC/REST API**          | `src/routes/`, `src/controllers/`, `src/models/` present                                      | Express app, Django, Spring Boot |
| **Modular/Feature-based** | `src/<feature>/` structure (e.g., `src/auth/`, `src/users/`) with per-feature files           | Feature-scoped modules           |
| **Layered/DDD**           | `src/api/`, `src/domain/`, `src/infra/`, `src/application/` clear separation                  | Domain-driven design             |
| **Monorepo**              | `turbo.json`, `pnpm-workspace.yaml`, `nx.json`, `lerna.json`, or `workspaces` in package.json | Workspace-based projects         |
| **Microservices**         | Multiple `package.json` / `go.mod` / etc. in separate dirs with independent tooling           | Services in separate paths       |
| **Monolith + CLI**        | Multiple entry points (`src/server.ts`, `src/cli.ts`, `cmd/`)                                 | API + CLI tools                  |
| **Unclear**               | Pattern doesn't match above → Ask the user                                                    | Don't guess                      |

## What to Extract

Document these findings concisely (not as prose):

- **Tech Stack:** Language(s), primary framework, ORM/database if applicable, build tool
- **Architecture:** Which pattern from table above?
- **Conventions:** If detectable from file structure:
  - File naming patterns (e.g., `.handler.ts`, `.service.ts`, `_test.go`)
  - Error handling approach (if visible from code)
  - Key module organization

**Verify, don't guess** — if a convention can't be confidently detected from static analysis, ask the user.

## Phase 1.5 → Phase 2 Template Decision Tree

### Decision 1: Is this a monorepo?

- Check for: `turbo.json`, `pnpm-workspace.yaml`, `nx.json`, `lerna.json`, or `workspaces` in package.json
- → YES: Use **Monorepo Template**
- → NO: Continue to Decision 2

### Decision 2: What's the primary language?

| Language              | Marker Files                                         | Template                                  |
| --------------------- | ---------------------------------------------------- | ----------------------------------------- |
| JavaScript/TypeScript | `package.json` (Node env)                            | **Base Template**                         |
| Python                | `pyproject.toml`, `.venv/`, `poetry.lock`, `uv.lock` | **Python/uv Template**                    |
| Go                    | `go.mod`, `go.sum`                                   | **Go Template**                           |
| Rust                  | `Cargo.toml`, `Cargo.lock`                           | **Rust Template**                         |
| Java                  | `pom.xml`, `build.gradle`                            | **Spring Boot Template**                  |
| C# / .NET             | `.csproj`, `.sln`                                    | **.NET Template**                         |
| JavaScript (Bun)      | `bun.lockb`                                          | **Bun Template**                          |
| Multiple languages    | Various (2+ languages)                               | **Polyglot guidance** (separate sections) |

### Decision 3: Customize for Your Project

Once you've selected a template:

1. Keep all **required sections** (see "Required sections" in SKILL.md)
2. Include **optional sections** that apply (API Patterns, CLI Commands, etc.)
3. Delete optional sections that don't apply
4. Add **project-specific conventions** (3-7 bullets; see [guide.md](guide.md))

For **monorepos specifically:**

- Are all packages the same language? If yes, base monorepo template applies
- Different languages per package? Add separate language sections or package-level AGENTS.md files (see guide.md)
