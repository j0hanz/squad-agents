---
name: codebase-init
description: "Initialize or audit repository instructions. Generates high-signal AGENTS.md wired to CLAUDE.md/GEMINI.md stubs. Not for documenting a specific feature's spec or design (see request-plan, parallel-brainstorming). Trigger on: 'init codebase', 'onboard repo', 'audit AGENTS.md', 'setup agent instructions', 'codebase-init', 'initialize project memory'."
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash(python *) Bash(python3 *) AskUserQuestion Skill
---

# codebase-init

**goal:** Maintain lean, high-signal `AGENTS.md`.
**constraint:** `CLAUDE.md`/`GEMINI.md` must be one-line redirect stubs to `AGENTS.md` (no duplicate contents).
**format:** Body style must be markdown-kv (`key: value` lines) — never prose paragraphs.
**target:** `AGENTS.md` < 100 lines.

## Process Flow

```
Trigger: Init/Audit Request
  -- audit only --> Audit Mode -> Lint AGENTS.md -> Report Issues
  -- full init ----> Init Mode -> Phase 0: Mode Selection (if AGENTS.md exists)
                                     -- AGENTS.md absent --------------> Phase 0: Policy Survey
                                     -- generate fresh new skeleton ----> Phase 0: Overwrite Confirmation
                                     -- update existing instructions ---> Phase 0: Marker Detection

Phase 0: Overwrite Confirmation
  -- cancel -------------> Halt (no partial file)
  -- confirm overwrite ---> Phase 0: Policy Survey

Phase 0: Marker Detection
  -- marker present --> Phase 1: Environment Discovery
  -- marker absent ---> Phase 0: Policy Survey

Phase 0: Policy Survey (ask 3 questions)
  -- survey complete --> Phase 1: Environment Discovery
  -- cancelled --------> Halt (no partial file)

Phase 1: Environment Discovery (analyze toolchain/structure)
  -> Phase 1.5: Architecting Mapping (detect patterns)
  -> Phase 2: Draft (scaffold AGENTS.md)
  -> Phase 3: Write, Wire, Validate (wire variants, lint)
```

## Phase 0: Mode Selection & Hard Rule Survey

- constraint: Check if root `AGENTS.md` exists.
- condition_absent: Proceed to Policy Survey.
- condition_exists: Call `AskUserQuestion` with `["Update existing instructions (Recommended)", "Generate fresh new skeleton"]`.

### Update/Overwrite Actions

- selection_generate: Call `AskUserQuestion` to confirm overwrite (`["Yes, overwrite", "Cancel"]`).
- trigger_cancel: Halt immediately.
- trigger_overwrite: Proceed to Policy Survey.
- selection_update: Scan `AGENTS.md` for `<!-- codebase-init:hard-rules v1 ... -->` (exact `v1` match).
- condition_marker_found: Bypass Policy Survey -> proceed to Phase 1.
- condition_marker_absent: Proceed to Policy Survey.

### Policy Survey Constraints

- tool-call: Call `AskUserQuestion` exactly once with all 3 questions ordered.
- options-strict: Never add "Other". Surface exactly 3 options per question.
- cancellation: Halt immediately on any dismiss. Do not write partial files.
- scope: Skip survey for monorepo package-level `AGENTS.md`. Only survey on root `AGENTS.md`.
- preservation: Preserve all pre-existing sections if regenerating `AGENTS.md` without marker.

### Survey Questions & Heuristics

- question_1: Commit & attribution policy.
  - options: `[strict, relaxed, minimal]`
  - heuristic: Match git log format rate or `CONTRIBUTING.md`.
- question_2: Project maturity state.
  - options: `[production, development]`
  - heuristic: Match version/tag, `CHANGELOG`, or release workflow.
- question_3: Testing rigor.
  - options: `[always, touched-files, not-enforced]`
  - heuristic: Check if CI gates on test suite.

### CI/CD Automation

- survey: Never surveyed.
- detection: `scripts/run.py analyze-env` via `.github/workflows/` or `.gitlab-ci.yml`.
- action: `scaffold-agents-md` auto-fills marker `ci=` value.
- override: Use `--ci <github-actions|gitlab-ci|local-only>` only if detection fails.
- reference: Read `references/hard-rules.md` for exact wording.

---

## Phase 1: Environment Discovery

- command: `python "$CLAUDE_PLUGIN_ROOT/skills/codebase-init/scripts/run.py" analyze-all . --max-depth 2`
- env-resolution: Fallback to relative path `skills/codebase-init` if `$CLAUDE_PLUGIN_ROOT` undefined.
- action: Run `analyze-env`, `find-dependencies`, `scan-structure`.

### Manual Fallback (On Failure)

- toolchain: Inspect manifest files (`package.json`, `pyproject.toml`, etc.). Do not hallucinate.
- structure: Run `ls -R` (limited depth).
- workflows: Inspect `.github/workflows/` or `.gitlab-ci.yml`.

---

## Phase 1.5: Architecting Mapping

- action: Read `references/phase-1.5-architecting.md`.
- requirement: Select `--language` value and detect tech stack patterns.

---

## Phase 2: Draft

- command: `python "$CLAUDE_PLUGIN_ROOT/skills/codebase-init/scripts/run.py" scaffold-agents-md --language <node|python|go|rust|java|dotnet|bun> --purpose "<one sentence from Phase 1>" --commit <strict|relaxed|minimal> --maturity <production|development> --testing <always|touched-files|not-enforced> [--pm "<real pm from Phase 1>"] [--set key=value ...] --out AGENTS.md`
- mapping_commit: Strict/Relaxed/Minimal -> `strict` | `relaxed` | `minimal`
- mapping_maturity: Production/Development -> `production` | `development`
- mapping_testing: Always required/Touched-files only/Not enforced -> `always` | `touched-files` | `not-enforced`
- manual-fallback: Construct `AGENTS.md` manually observing required sections/formats if command fails.

### Post-Generation Actions

- fix: Correct Toolchain/Dependency/Command defaults.
- replace: Swap Key Conventions TODO with 3-7 actual `key: value` lines.
  - verify_code: Verifiable by reading code (no vague principles).
  - verify_linter: Beyond linter scope (focus on design/architecture).
  - verify_count: Exactly 3 to 7 items.

### Required Sections (Strict Order)

- 1_header: `# Agent Instructions` or `# <Project> Agent Instructions`
- 2_description: `purpose: <one sentence>`
- 3_hard_rules: Exactly 4 KV lines (`commit:`, `maturity:`, `testing:`, `ci:`) + marker comment.
- 4_toolchain: Package manager and environment commands (KV format).
- 5_file_commands: Table of file-targeted typecheck/lint/test commands.
- 6_conventions: 3-7 actionable KV lines.
- 7_attribution: `Co-Authored-By: <Model Name>` at EOF.

---

## Phase 3: Write, Wire, Validate

- action_1: Apply edits directly to Phase 2 `AGENTS.md`. Do not rewrite from scratch.
- action_2: Run `python "$CLAUDE_PLUGIN_ROOT/skills/codebase-init/scripts/run.py" wire-agents AGENTS.md CLAUDE.md GEMINI.md`
- action_3: Run `python "$CLAUDE_PLUGIN_ROOT/skills/codebase-init/scripts/run.py" lint-agents-md AGENTS.md`
- action_4: Fix all lint errors.

### Manual Fallback

- failure_wire: Manually wire `CLAUDE.md` and `GEMINI.md` with exact stub `# See [AGENTS.md](AGENTS.md)`.
- failure_lint: Ensure no prose in lists, strict KV format, under 100 lines, no TODOs, and valid Attribution.

### Next Skills

- architecting: Map patterns, "God" modules, circular dependencies.
- parallel-brainstorming: Explore features.
- request-plan: Create implementation plans.
- context-optimizer: If context bloats mid-skill (long reads, many tool calls).

---

## Audit Mode

- trigger: Validation request only (no regeneration).
- action: Skip Phases 0, 1, 1.5, 2.
- command: `python "$CLAUDE_PLUGIN_ROOT/skills/codebase-init/scripts/run.py" lint-agents-md AGENTS.md`
- constraint: Do NOT read `references/hard-rules.md` or `references/phase-1.5-architecting.md`.

---

## Failure Recovery

- trigger: Any step fails.
- action_halt: Stop execution immediately.
- action_diagnose: Invoke `diagnose` via `Skill` tool using script `stderr` and `AGENTS.md`.
- constraint: No manual fixes until root cause confirmed.
- resume: Resume at failed phase post-resolution (never restart from Phase 0).

---

## Prohibitions

- never: Hallucinate tools/commands.
- never: Hand-write/copy `AGENTS.md` skeleton (must use scaffold-agents-md).
- never: Symlink/copy full content to `CLAUDE.md`/`GEMINI.md` (must use 1-line stub).
- never: Reorder `AGENTS.md` sections.
- never: Leave placeholder TODOs.
