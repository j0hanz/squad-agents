# Implementation Plan: Merge create-specs + create-plan into `planning`

## Goal

Replace the two skills [skills/create-specs/](skills/create-specs/) and [skills/create-plan/](skills/create-plan/) with one cross-aligned skill `skills/planning/` that produces two paired artifacts per invocation (`plan/<name>.specs.md` + `plan/<name>.plan.md`), enforces a `Satisfies:` traceability spine via a unified script suite, and rewires `spec-driven-development` to a single Planning Gate. Done when `npm run validate`, `npm run test:python`, and an end-to-end `scaffold → sync → validate --cross` smoke pass with zero broken references to the deleted skills.

## Requirements & Constraints

- `REQ-001`: One `planning` skill produces both `plan/<name>.specs.md` and `plan/<name>.plan.md` sharing a stem.
- `REQ-002`: Every plan task carries a `Satisfies:` field listing spec IDs; `validate.py --cross` enforces the coverage matrix (no orphan tasks, no uncovered requirements).
- `REQ-003`: A unified 4-script suite (`scaffold.py`, `sync.py`, `discover.py`, `validate.py`) on one bundled `spec_parser.py` extended to parse `Satisfies:` fields.
- `REQ-004`: A single depth dial (`sketch`/`contract`/`blueprint`) drives both artifacts; modifiers `--quick`, `--assume-paths`, `--spec-only`, `--from-spec`.
- `REQ-005`: One merged `reviewer.md` agent scores spec + plan + traceability.
- `REQ-006`: `spec-driven-development` Steps 2+3 collapse into one Planning Gate invoking `planning`; all ~21 references repoint to `planning`.
- `CON-001`: MUST NOT leave any reference to `create-specs` or `create-plan` in `skills/`, `lib/`, or `package.json` after completion (verified by grep).
- `CON-002`: MUST NOT delete `lib/` or the old skill dirs until a guard grep confirms no live importers remain outside the deleted code.
- `PAT-001`: ESM/Python conventions per [AGENTS.md](AGENTS.md); scripts are stdlib-only, Python 3.10+, self-contained within the skill.
- `SEC-001`: Scripts MUST remain read-only except `scaffold.py`/`sync.py` writes, which only write inside the target `plan/` dir.

## Current Context

Verified during discovery:

- Parser exists in three places: [lib/spec_parser.py](lib/spec_parser.py) (used only by [generate_plan.py](skills/create-plan/scripts/generate_plan.py)), a bundled copy [skills/create-specs/scripts/spec_parser.py](skills/create-specs/scripts/spec_parser.py) (used by [validate_spec.py](skills/create-specs/scripts/validate_spec.py)), re-exported by [lib/**init**.py](lib/__init__.py).
- `_IDS_RE` already captures `REQ|SEC|PERF|COMP|AC|VAL|CON`: [spec_parser.py:26](lib/spec_parser.py#L26). No `Satisfies:`/task parsing yet.
- Discovery helper is solid and relocatable as-is: [discover.py](skills/create-plan/scripts/discover.py).
- Two reviewer agents to merge: [create-specs/agents/reviewer.md](skills/create-specs/agents/reviewer.md) (sonnet, spec) and [create-plan/agents/reviewer.md](skills/create-plan/agents/reviewer.md) (haiku, plan).
- Skills are auto-discovered; [bin/validate-plugin.mjs](bin/validate-plugin.mjs) reads the `skills/` dir and warns when a SKILL.md > 300 lines has no `references/`. No manifest enumerates skills; [.claude-plugin/plugin.json](.claude-plugin/plugin.json) does not list them.
- No Python tests registered for either skill: [package.json:16](package.json#L16) (`test:python`).
- Consumer wiring: [spec-driven-development/SKILL.md](skills/spec-driven-development/SKILL.md) (Spec Gate [L165](skills/spec-driven-development/SKILL.md#L165), Plan Gate [L190](skills/spec-driven-development/SKILL.md#L190)), [diagnose_dependencies.py:37](skills/spec-driven-development/scripts/diagnose_dependencies.py#L37), SDD references, [architecture/SKILL.md:144](skills/architecture/SKILL.md#L144), [using-agent-dev/SKILL.md:51](skills/using-agent-dev/SKILL.md#L51), [skill-routing-map.md:11](skills/using-agent-dev/references/skill-routing-map.md#L11).
- No `commands/*.md` reference either skill (verified).

---

## PHASE-000: Safety Net & Scaffolding

### TASK-000: Create work branch and capture baseline

Depends on: none
Files: [package.json](package.json)
Symbols: none
Action: Create branch `refactor/planning-skill` off `master`, then run the existing suites to capture a green baseline before changes.
Validate: Run `git checkout -b refactor/planning-skill && npm run validate && npm run test:python`
Expected result: Branch created; validate prints "All validations passed"; pytest exits 0.

### TASK-001: Scaffold the planning skill directory tree

Depends on: TASK-000
Files: [skills/planning/](skills/planning/)
Symbols: none
Action: Create empty dirs `skills/planning/scripts/`, `skills/planning/references/`, `skills/planning/agents/`, `skills/planning/evals/`, `skills/planning/tests/` (add a `.gitkeep` where needed so they are tracked).
Validate: Run `python -c "import pathlib,sys; sys.exit(0 if all(pathlib.Path('skills/planning',d).is_dir() for d in ['scripts','references','agents','evals','tests']) else 1)"`
Expected result: Exit code 0 — all five subdirectories exist.

---

## PHASE-001: The Engine (Unified Script Suite)

### TASK-002: Build the unified bundled parser with plan/Satisfies support

Depends on: TASK-001
Files: [skills/planning/scripts/spec_parser.py](skills/planning/scripts/spec_parser.py)
Symbols: none
Action: Author `spec_parser.py` starting from [lib/spec_parser.py](lib/spec_parser.py) (`SpecDocument`, `parse_spec`, `_IDS_RE`, `_HEADING_RE`). Add `@dataclass PlanTask` (fields: `id`, `title`, `satisfies: set[str]`, `fields: dict[str,str]`), a `@dataclass PlanDocument` (`tasks: list[PlanTask]`, `phases: list[str]`, `satisfied_ids: set[str]`), and `parse_plan(path)` that walks `### TASK-` headers and extracts the `Satisfies:` line into `satisfies`. Keep zero non-stdlib imports.
Validate: Run `python -c "import sys; sys.path.insert(0,'skills/planning/scripts'); import spec_parser as s; assert hasattr(s,'parse_plan') and hasattr(s,'parse_spec'); print('ok')"`
Expected result: Prints `ok`; both functions importable from the bundled module.

### TASK-003: Build scaffold.py emitting both paired artifacts with matching IDs

Depends on: TASK-002
Files: [skills/planning/scripts/scaffold.py](skills/planning/scripts/scaffold.py)
Symbols: none
Action: Author `scaffold.py` merging the templates/domain snippets from [scaffold_spec.py](skills/create-specs/scripts/scaffold_spec.py). CLI: `scaffold.py <name> --depth {sketch,contract,blueprint} [--dir plan] [--domain api|cli] [--goal TEXT]`. Write `<dir>/<name>.specs.md` (depth-sized 8-section spec with `REQ-001`/`SEC-001`/`AC-001`/`VAL-001` placeholders) and `<dir>/<name>.plan.md` (Goal + a cross-link header line `Spec: [<name>.specs.md](<name>.specs.md)` + empty `PHASE-001`). Both files carry a matching `# <name>` title stem.
Validate: Run `python skills/planning/scripts/scaffold.py demo --depth contract --dir /tmp/pl && test -f /tmp/pl/demo.specs.md && test -f /tmp/pl/demo.plan.md && grep -q "demo.specs.md" /tmp/pl/demo.plan.md`
Expected result: Both files created; plan file contains the cross-link to the spec file.

### TASK-004: Build sync.py (spec → plan task stubs with Satisfies, idempotent)

Depends on: TASK-002
Files: [skills/planning/scripts/sync.py](skills/planning/scripts/sync.py)
Symbols: none
Action: Author `sync.py` replacing [generate_plan.py](skills/create-plan/scripts/generate_plan.py). Read `<name>.specs.md`, and for every `REQ/SEC/PERF` emit a `### TASK-NNN` stub with `Satisfies: <ID>` pre-filled and empty `Files/Symbols/Action/Validate/Expected result`. Merge-by-ID into an existing `<name>.plan.md`: tasks whose `Satisfies` already covers an ID are preserved verbatim; only missing IDs append new stubs. Add a trailing `PHASE-END` acceptance task mapping `AC-###`. CLI: `sync.py <name>.specs.md [--plan <name>.plan.md]`.
Validate: Run `python skills/planning/scripts/scaffold.py demo2 --depth contract --dir /tmp/pl2 && python skills/planning/scripts/sync.py /tmp/pl2/demo2.specs.md && grep -c "Satisfies:" /tmp/pl2/demo2.plan.md`
Expected result: `grep -c` returns ≥ 1 (at least one task stub with a `Satisfies:` field).

### TASK-005: Relocate discover.py into the planning skill

Depends on: TASK-001
Files: [skills/planning/scripts/discover.py](skills/planning/scripts/discover.py)
Symbols: none
Action: Copy [discover.py](skills/create-plan/scripts/discover.py) verbatim to the planning scripts dir (stdlib-only, no path edits needed; the help text examples may be updated to `skills/planning/scripts/discover.py`).
Validate: Run `python skills/planning/scripts/discover.py --files "skills/planning/scripts/*.py"`
Expected result: Markdown link list including `discover.py`, `scaffold.py`, `sync.py`, `spec_parser.py`.

### TASK-006: Build validate.py with --spec/--plan/--cross modes

Depends on: TASK-002
Files: [skills/planning/scripts/validate.py](skills/planning/scripts/validate.py)
Symbols: none
Action: Author `validate.py` merging the logic of [validate_spec.py](skills/create-specs/scripts/validate_spec.py) (`SECTIONS_BY_LEVEL`, requirement linter, REQ→AC→VAL traceability) and [validate_plan.py](skills/create-plan/scripts/validate_plan.py) (mandatory task fields, markdown-link check, DAG). Add `--cross` using `parse_spec` + `parse_plan`: every `REQ/SEC/PERF` must appear in some task's `Satisfies` (else "uncovered requirement"); every `Satisfies` ID must exist in the spec (else "orphan task"); every `AC` must map to ≥1 task. CLI: `validate.py <name> [--spec|--plan|--cross]` (default runs all three on the paired `<name>.specs.md`/`<name>.plan.md`); nonzero exit on any ERROR; print a coverage matrix summary.
Validate: Run `python skills/planning/scripts/validate.py /tmp/pl2/demo2 --cross; echo "exit=$?"`
Expected result: Coverage-matrix report prints; exit code reflects orphan/uncovered status (documented in output).

### TASK-007: Write pytest coverage for the script suite

Depends on: TASK-003, TASK-004, TASK-006
Files: [skills/planning/tests/test_planning_scripts.py](skills/planning/tests/test_planning_scripts.py)
Symbols: none
Action: Write pytest tests using `tmp_path`: (a) `scaffold` creates both files with matching stem and cross-link; (b) `parse_plan` extracts `Satisfies` IDs; (c) `sync` is idempotent (second run does not duplicate authored tasks); (d) `validate --cross` flags an orphan task and an uncovered requirement on crafted fixtures.
Validate: Run `python -m pytest skills/planning/tests/test_planning_scripts.py -q`
Expected result: All tests pass, 0 failures.

### TASK-008: Register planning tests in the python test script

Depends on: TASK-007
Files: [package.json](package.json)
Symbols: [test:python](package.json#L16)
Action: Append `skills/planning/tests/` to the `test:python` pytest path list at [package.json:16](package.json#L16).
Validate: Run `npm run test:python`
Expected result: pytest collects and passes the new `skills/planning/tests/` directory; exit 0.

---

## PHASE-002: Skill Content & Agent

### TASK-009: Author the lean planning SKILL.md

Depends on: TASK-006
Files: [skills/planning/SKILL.md](skills/planning/SKILL.md)
Symbols: none
Action: Write a ≤ 200-line `SKILL.md` with frontmatter (`name: planning`, merged trigger description covering both spec and plan vocab, `user-invocable: true`, `allowed-tools: Bash(python *) Bash(python3 *)`, `argument-hint` documenting depth + modifiers). Body: the depth dial table, the artifact-pairing/naming rule, the linear pipeline (Intake → Spec → validate --spec → Sync plan → discover → validate --plan → validate --cross → reviewer → handoff), the canonical task block with the new `Satisfies:` field, and a reference table pointing to `references/`. Push templates/examples to references (progressive disclosure to stay under the 300-line validator warning).
Validate: Run `node bin/validate-plugin.mjs`
Expected result: "All validations passed"; no "Large skill … should extract content to references/" warning for planning.

### TASK-010: Port and consolidate references/

Depends on: TASK-009
Files: [skills/planning/references/](skills/planning/references/)
Symbols: none
Action: Create `references/spec-template.md` + `references/domain-examples.md` (from [create-specs references](skills/create-specs/references/domain-examples.md) and [self-check.md](skills/create-specs/references/self-check.md)), `references/plan-template.md` + `references/decomposition.md` + `references/discovery.md` + `references/validation.md` + `references/output-examples.md` (from [create-plan references](skills/create-plan/references/)), and a new `references/traceability.md` documenting the `Satisfies:` spine and `--cross` matrix. Update intra-doc links to the new paths.
Validate: Run `rg -n "create-specs|create-plan" skills/planning/references/ || echo "clean"`
Expected result: Prints `clean` — no stale skill-name references in the ported docs.

### TASK-011: Merge the two reviewer agents into one

Depends on: TASK-009
Files: [skills/planning/agents/reviewer.md](skills/planning/agents/reviewer.md)
Symbols: none
Action: Author one `reviewer.md` (model `claude-sonnet-4-6`, tools Read/Glob/Grep) taking `spec_path`, `plan_path`, `maturity`. Combine the spec section-scoring from [create-specs reviewer](skills/create-specs/agents/reviewer.md) and the plan dimension-scoring from [create-plan reviewer](skills/create-plan/agents/reviewer.md), and add a `traceability` block scoring spec↔plan coverage (orphan tasks, uncovered REQs, AC→task gaps). Emit one JSON schema with `ready_for_execution` gated on spec score, plan score, and zero traceability gaps.
Validate: Run `node bin/validate-plugin.mjs`
Expected result: "All validations passed"; reviewer.md frontmatter parses (has `description`).

### TASK-012: Create the merged evals set

Depends on: TASK-009
Files: [skills/planning/evals/evals.json](skills/planning/evals/evals.json)
Symbols: none
Action: Author `evals.json` (`skill_name: planning`) combining the spec cases from [create-specs evals](skills/create-specs/evals/evals.json) and the plan cases from [create-plan evals](skills/create-plan/evals/evals.json), plus one new case asserting that a single invocation yields both paired artifacts and a clean `validate.py --cross`.
Validate: Run `python -c "import json; d=json.load(open('skills/planning/evals/evals.json')); assert d['skill_name']=='planning' and len(d['evals'])>=4; print('ok')"`
Expected result: Prints `ok`; valid JSON with ≥ 4 eval cases.

---

## PHASE-003: Repoint Consumers

### TASK-013: Collapse SDD Spec+Plan gates into one Planning Gate

Depends on: TASK-009
Files: [skills/spec-driven-development/SKILL.md](skills/spec-driven-development/SKILL.md)
Symbols: [Specification Gate](skills/spec-driven-development/SKILL.md#L165)
Action: Replace Steps 2 ([L165](skills/spec-driven-development/SKILL.md#L165)) and 3 ([L190](skills/spec-driven-development/SKILL.md#L190)) with a single "### 2. Planning Gate ← `planning` required" that invokes `planning` once (producing both `<name>.specs.md` + `<name>.plan.md`), and renumber the following Implementation/Acceptance steps. Update the gate description to reference `validate.py --spec/--plan/--cross`.
Validate: Run `rg -n "Planning Gate" skills/spec-driven-development/SKILL.md && rg -c "Specification Gate" skills/spec-driven-development/SKILL.md`
Expected result: One "Planning Gate" present; "Specification Gate" count is 0.

### TASK-014: Update SDD supporting tables and notation to `planning`

Depends on: TASK-013
Files: [skills/spec-driven-development/SKILL.md](skills/spec-driven-development/SKILL.md)
Symbols: none
Action: Update the response-length table ([L43](skills/spec-driven-development/SKILL.md#L43)), avoid-patterns ([L49-50](skills/spec-driven-development/SKILL.md#L49)), artifacts table ([L63-64](skills/spec-driven-development/SKILL.md#L63)), notation note ([L69](skills/spec-driven-development/SKILL.md#L69)), prerequisites ([L93](skills/spec-driven-development/SKILL.md#L93)), required sub-skills table ([L103-104](skills/spec-driven-development/SKILL.md#L103)), and fast-path mention ([L122](skills/spec-driven-development/SKILL.md#L122)) to name `planning` and its scripts (`scaffold.py`/`sync.py`/`validate.py`).
Validate: Run `rg -n "create-specs|create-plan" skills/spec-driven-development/SKILL.md || echo "clean"`
Expected result: Prints `clean`.

### TASK-015: Rewrite the dependency diagnostic for `planning`

Depends on: TASK-006
Files: [skills/spec-driven-development/scripts/diagnose_dependencies.py](skills/spec-driven-development/scripts/diagnose_dependencies.py)
Symbols: [PREREQUISITES](skills/spec-driven-development/scripts/diagnose_dependencies.py#L37)
Action: Replace the five `create-specs`/`create-plan` prerequisite entries ([L37-64](skills/spec-driven-development/scripts/diagnose_dependencies.py#L37)) with checks for `skills/planning/SKILL.md`, `skills/planning/scripts/scaffold.py`, `skills/planning/scripts/sync.py`, and `skills/planning/scripts/validate.py`.
Validate: Run `python skills/spec-driven-development/scripts/diagnose_dependencies.py; echo "exit=$?"`
Expected result: All listed prerequisites report `[OK]`; exit code 0.

### TASK-016: Repoint SDD reference docs

Depends on: TASK-013
Files: [skills/spec-driven-development/references/example-cycle.md](skills/spec-driven-development/references/example-cycle.md)
Symbols: none
Action: Update `create-specs`/`create-plan` mentions to `planning` across [example-cycle.md](skills/spec-driven-development/references/example-cycle.md) (L21,23,43,45,94), [anti-patterns.md:21](skills/spec-driven-development/references/anti-patterns.md#L21), [scope-interview.md](skills/spec-driven-development/references/scope-interview.md) (L40,55,63,64), [spec-recovery.md:63](skills/spec-driven-development/references/spec-recovery.md#L63), [implementation-governance.md:56](skills/spec-driven-development/references/implementation-governance.md#L56), and [sketch-template.md:51](skills/spec-driven-development/references/sketch-template.md#L51). Reflect the single-invocation flow and new script names.
Validate: Run `rg -n "create-specs|create-plan" skills/spec-driven-development/references/ || echo "clean"`
Expected result: Prints `clean`.

### TASK-017: Update SDD evals to reference `planning`

Depends on: TASK-013
Files: [skills/spec-driven-development/evals/evals.json](skills/spec-driven-development/evals/evals.json)
Symbols: none
Action: Update expectation strings at L13, L25, L104, L111, L131 to name `planning` and the single Planning Gate (the full cycle becomes brainstorming → planning).
Validate: Run `python -c "import json;json.load(open('skills/spec-driven-development/evals/evals.json'));print('ok')" && (rg -n "create-specs|create-plan" skills/spec-driven-development/evals/evals.json || echo clean)`
Expected result: Prints `ok` then `clean`.

### TASK-018: Repoint architecture, using-agent-dev, and routing map

Depends on: TASK-009
Files: [skills/using-agent-dev/references/skill-routing-map.md](skills/using-agent-dev/references/skill-routing-map.md)
Symbols: none
Action: Update [architecture/SKILL.md:144](skills/architecture/SKILL.md#L144) (hand-off target → `planning`), [using-agent-dev/SKILL.md](skills/using-agent-dev/SKILL.md) L51 and L62 (process-skill lists → `planning`), and [skill-routing-map.md](skills/using-agent-dev/references/skill-routing-map.md) L11-12 and L27-28 (collapse the two rows into one `planning` row covering specs + plans).
Validate: Run `rg -n "create-specs|create-plan" skills/architecture skills/using-agent-dev || echo "clean"`
Expected result: Prints `clean`.

---

## PHASE-004: Delete Old Skills & Cleanup

### TASK-019: Guard then delete the two old skill directories

Depends on: TASK-014, TASK-015, TASK-016, TASK-017, TASK-018
Files: [skills/create-specs/](skills/create-specs/)
Symbols: none
Action: Run a repo-wide guard grep for live references; only if it reports `clean` outside the dirs themselves, delete `skills/create-specs/` and `skills/create-plan/`.
Validate: Run `rg -l "create-specs|create-plan" --glob '!skills/create-specs/**' --glob '!skills/create-plan/**' --glob '!**/__pycache__/**' --glob '!plan/**' || echo "clean"` then `rm -rf skills/create-specs skills/create-plan && test ! -d skills/create-specs && test ! -d skills/create-plan && echo deleted`
Expected result: Guard prints `clean`; then prints `deleted`; both directories gone.

### TASK-020: Guard then remove the orphaned lib/ parser

Depends on: TASK-002, TASK-019
Files: [lib/spec_parser.py](lib/spec_parser.py)
Symbols: none
Action: Confirm nothing imports `lib`/`spec_parser` outside the now-deleted code and the new bundled copy; only if `clean`, delete `lib/spec_parser.py` and `lib/__init__.py` (remove `lib/` if empty).
Validate: Run `rg -n "from lib|import lib|lib\.spec_parser|sys.path.*lib" --glob '!**/__pycache__/**' --glob '!skills/planning/**' || echo "clean"` then `rm -f lib/spec_parser.py lib/__init__.py && echo removed`
Expected result: Guard prints `clean`; then prints `removed`.

---

## PHASE-END: Full Validation

### TASK-021: Run the full plugin + test gate

Depends on: TASK-008, TASK-019, TASK-020
Files: [package.json](package.json)
Symbols: none
Action: Run plugin validation and both test suites to confirm nothing regressed after deletion and rewiring.
Validate: Run `npm run validate && npm run test:python && npm run test:node`
Expected result: "All validations passed"; pytest exit 0; node --test exit 0.

### TASK-022: End-to-end traceability smoke test

Depends on: TASK-021
Files: [skills/planning/scripts/validate.py](skills/planning/scripts/validate.py)
Symbols: none
Action: From a clean temp dir, run `scaffold.py smoke --depth contract`, fill two REQs + matching ACs in the spec, run `sync.py`, author one task per REQ with `Satisfies:`, then run `validate.py smoke --cross`. Then intentionally remove one task's `Satisfies` and re-run to confirm the orphan/uncovered error fires.
Validate: Run `python skills/planning/scripts/validate.py /tmp/smoke/smoke --cross; echo "exit=$?"`
Expected result: Clean coverage matrix (exit 0) when complete; nonzero exit with a specific "uncovered requirement" message after the deliberate break.

### TASK-023: Spawn the merged reviewer on the new skill

Depends on: TASK-011, TASK-022
Files: [skills/planning/agents/reviewer.md](skills/planning/agents/reviewer.md)
Symbols: none
Action: Use the Agent tool with the contents of `skills/planning/agents/reviewer.md`, passing the smoke `spec_path` and `plan_path`, to confirm the agent returns valid JSON with `ready_for_execution` and a populated `traceability` block.
Validate: Review the returned JSON for `ready_for_execution: true` and zero traceability gaps on the completed smoke artifacts.
Expected result: Reviewer returns schema-valid JSON; `ready_for_execution: true`; no orphan/uncovered findings.

---

## Testing & Validation

- Unit: `python -m pytest skills/planning/tests/ -q` (parser, scaffold, sync idempotency, cross-coverage).
- Plugin: `npm run validate` (frontmatter, skill structure, <300-line lean core).
- Regression: `npm run test:node` + `npm run test:python` after deletion.
- Integration: `node tests/integration/test-skills-load.mjs` to confirm `planning` loads and the deleted skills no longer resolve.
- E2E: the TASK-022 scaffold→sync→validate --cross cycle.

## Acceptance Criteria

- `AC-001`: One `/planning` run produces `plan/<name>.specs.md` + `plan/<name>.plan.md` (verified by TASK-003/TASK-022).
- `AC-002`: `validate.py --cross` reports a coverage matrix and fails on orphan tasks / uncovered requirements (TASK-006/TASK-022).
- `AC-003`: `rg "create-specs|create-plan"` across `skills/`, `lib/`, `package.json` returns no live references (TASK-019/TASK-020 guards).
- `AC-004`: `npm run validate && npm run test:python && npm run test:node` all pass (TASK-021).
- `AC-005`: `diagnose_dependencies.py` reports all `planning` prerequisites OK (TASK-015).

## Rollback Strategy

All work is on `refactor/planning-skill`. If the gate (TASK-021) fails irrecoverably: `git checkout master` abandons the branch with zero impact on the live skills. Because deletions (TASK-019/020) are the last content steps before validation, a failed validation can be reverted with `git restore --source=master --staged --worktree skills/create-specs skills/create-plan lib`. Each phase is independently committable for granular bisecting.

## Decision Log

- Bundled parser inside `skills/planning/scripts/` (not shared `lib/`) — keeps the skill self-contained and portable, matching how `validate_spec.py` already bundled its own copy; `lib/` had only one live importer.
- `validate.py --cross` enforces the spine rather than restructuring spec/plan into one file (Approach A from the brainstorm) — keeps both artifacts independently valid and human-readable.
- Deletion sequenced last, behind guard greps, to satisfy CON-002 and keep rollback trivial.
