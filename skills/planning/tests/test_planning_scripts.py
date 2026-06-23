"""Tests for skills/planning/scripts — scaffold, sync, parser, validate."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from spec_parser import parse_spec, parse_plan  # noqa: E402
from scaffold import scaffold  # noqa: E402
from sync import sync  # noqa: E402
from validate import validate_spec, validate_plan, validate_cross, validate_review  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def spec_file(tmp_path: Path) -> Path:
    """A minimal valid contract-level spec."""
    content = """\
# test-feature

## 1. Goal

- Enable users to authenticate with JWT tokens.
- Completion signal: Users can obtain a JWT and access protected endpoints.

## 2. Requirements

- `REQ-001`: The system MUST issue a signed JWT on successful login.
- `REQ-002`: The system MUST reject requests missing a valid Bearer token.
- `SEC-001`: Tokens MUST expire after 3600 seconds.

## 3. Constraints

- `CON-001`: The solution MUST NOT store tokens in plaintext.

## 4. Interfaces

The system exposes the following interfaces:

### POST /auth/login

**Input:**
- `email` (string, required): user email
- `password` (string, required): user password

**Output:**
- `token` (string): signed JWT

**Errors:**
- `400`: Missing fields
- `401`: Invalid credentials
- `500`: Internal error

## 5. Context

- Files: [src/auth.ts](src/auth.ts)
- Current behavior: No authentication exists yet.

## 6. Acceptance Criteria & Validation

- `AC-001`: A valid login request returns a 200 response with a JWT token.
- `VAL-001`: `npm test -- auth.test.ts`

## 7. Examples & Edge Cases

- Valid credentials -> 200 + token
- Wrong password -> 401
"""
    p = tmp_path / "test-feature.specs.md"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def plan_file(spec_file: Path) -> Path:
    """A minimal plan with one task that satisfies REQ-001, co-located with spec_file."""
    content = """\
# test-feature

Spec: [test-feature.specs.md](test-feature.specs.md)

## PHASE-001: Implementation

### TASK-001: Implement REQ-001

Depends on: none
Files: [src/auth.ts](src/auth.ts)
Symbols: [issueJwt](src/auth.ts#L10)
Satisfies: REQ-001
Action: Add JWT issuance logic.
Validate: `npm test -- auth.test.ts`
Expected result: All tests pass.

## PHASE-END: Acceptance
"""
    p = spec_file.parent / "test-feature.plan.md"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


def test_parse_spec_populates_reqs_and_acs(spec_file: Path) -> None:
    doc = parse_spec(spec_file)
    assert "REQ-001" in doc.reqs
    assert "REQ-002" in doc.reqs
    assert "SEC-001" in doc.reqs
    assert "AC-001" in doc.acs
    assert "VAL-001" in doc.vals
    assert "CON-001" in doc.cons


def test_parse_plan_extracts_satisfies(plan_file: Path) -> None:
    doc = parse_plan(plan_file)
    assert len(doc.tasks) == 1
    task = doc.tasks[0]
    assert task.id == "TASK-001"
    assert "REQ-001" in task.satisfies
    assert "REQ-001" in doc.satisfied_ids


# ---------------------------------------------------------------------------
# Scaffold tests
# ---------------------------------------------------------------------------


def test_scaffold_creates_both_files(tmp_path: Path) -> None:
    spec_path, plan_path = scaffold("my-feature", depth="contract", out_dir=tmp_path)
    assert spec_path.exists(), "spec file not created"
    assert plan_path.exists(), "plan file not created"


def test_scaffold_plan_contains_spec_crosslink(tmp_path: Path) -> None:
    spec_path, plan_path = scaffold("auth-jwt", depth="contract", out_dir=tmp_path)
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "auth-jwt.specs.md" in plan_text, "cross-link to spec file missing from plan"


def test_scaffold_both_share_same_stem(tmp_path: Path) -> None:
    spec_path, plan_path = scaffold("rate-limit", depth="sketch", out_dir=tmp_path)
    assert spec_path.stem == "rate-limit.specs"
    assert plan_path.stem == "rate-limit.plan"


def test_scaffold_all_depths(tmp_path: Path) -> None:
    for depth in ("sketch", "contract", "blueprint"):
        sp, pp = scaffold(f"feat-{depth}", depth=depth, out_dir=tmp_path / depth)
        assert sp.exists()
        assert pp.exists()


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


def test_sync_adds_satisfies_stubs(spec_file: Path, tmp_path: Path) -> None:
    plan_path = tmp_path / "test-feature.plan.md"
    added = sync(spec_file, plan_path)
    assert added > 0
    text = plan_path.read_text(encoding="utf-8")
    assert "Satisfies:" in text


def test_sync_is_idempotent(spec_file: Path, tmp_path: Path) -> None:
    plan_path = tmp_path / "test-feature.plan.md"
    sync(spec_file, plan_path)
    first_text = plan_path.read_text(encoding="utf-8")
    added_second = sync(spec_file, plan_path)
    second_text = plan_path.read_text(encoding="utf-8")
    assert added_second == 0, "second sync should add nothing"
    assert first_text == second_text, "plan should be unchanged after second sync"


def test_sync_preserves_authored_task(
    spec_file: Path, plan_file: Path, tmp_path: Path
) -> None:
    # plan_file already has TASK-001 covering REQ-001; sync should not duplicate it
    work = tmp_path / "preserve"
    work.mkdir()
    dest_spec = work / spec_file.name
    dest_plan = work / plan_file.name
    shutil.copy(spec_file, dest_spec)
    shutil.copy(plan_file, dest_plan)
    sync(dest_spec, dest_plan)
    text = dest_plan.read_text(encoding="utf-8")
    # REQ-001 should appear exactly once in Satisfies lines
    satisfies_lines = [
        ln for ln in text.splitlines() if "Satisfies:" in ln and "REQ-001" in ln
    ]
    assert len(satisfies_lines) == 1, (
        f"expected 1 Satisfies line for REQ-001, got {len(satisfies_lines)}"
    )


# ---------------------------------------------------------------------------
# Validate tests
# ---------------------------------------------------------------------------


def test_validate_spec_valid_contract(spec_file: Path) -> None:
    errors, warnings = validate_spec(spec_file, "contract")
    assert not errors, f"unexpected errors: {errors}"


def test_validate_plan_valid(plan_file: Path) -> None:
    errors, warnings = validate_plan(plan_file)
    assert not errors, f"unexpected errors: {errors}"


def test_validate_cross_clean(spec_file: Path, plan_file: Path) -> None:
    # plan_file only covers REQ-001; REQ-002 and SEC-001 are uncovered
    errors, warnings, matrix = validate_cross(spec_file, plan_file)
    uncovered = matrix["uncovered"]
    assert "REQ-002" in uncovered
    assert "SEC-001" in uncovered
    assert "REQ-001" not in uncovered


def test_validate_cross_orphan_task(spec_file: Path, tmp_path: Path) -> None:
    plan_text = """\
# test-feature

Spec: [test-feature.specs.md](test-feature.specs.md)

## PHASE-001: Implementation

### TASK-001: Implement nonexistent

Depends on: none
Files: none
Symbols: none
Satisfies: REQ-999
Action: This task satisfies a fake ID.
Validate: `echo ok`
Expected result: exit 0.
"""
    plan_path = tmp_path / "test-feature.plan.md"
    plan_path.write_text(plan_text, encoding="utf-8")
    errors, warnings, matrix = validate_cross(spec_file, plan_path)
    assert any("REQ-999" in e for e in errors), "orphan task not detected"


def test_validate_cross_flags_uncovered_requirement(
    spec_file: Path, tmp_path: Path
) -> None:
    # Empty plan — all requirements uncovered
    plan_text = """\
# test-feature

Spec: [test-feature.specs.md](test-feature.specs.md)

## PHASE-001: Implementation

### TASK-001: placeholder

Depends on: none
Files: none
Symbols: none
Satisfies: none
Action: placeholder
Validate: `echo ok`
Expected result: exit 0.
"""
    plan_path = tmp_path / "test-feature.plan.md"
    plan_path.write_text(plan_text, encoding="utf-8")
    errors, warnings, matrix = validate_cross(spec_file, plan_path)
    assert len(matrix["uncovered"]) > 0, "uncovered requirements not detected"
    assert any("Uncovered" in e for e in errors)


def test_validate_spec_ignores_code_ticks_and_false_positives(tmp_path: Path) -> None:
    # Test that code ticks block "and" / vague adjectives warnings,
    # and "be red" doesn't trigger passive voice warning
    spec_content = """\
# test-feature

## 1. Goal

- Testing code blocks.
- Completion signal: success.

## 2. Requirements

- `REQ-001`: The system MUST use `simple` and `robust` libraries.
- `REQ-002`: The indicator light MUST be red.
- `REQ-003`: The system MUST be configured.
"""
    p = tmp_path / "test-spec-ticks.specs.md"
    p.write_text(spec_content, encoding="utf-8")
    errors, warnings = validate_spec(p, "sketch")

    passive_voice_warnings = [w for w in warnings if "passive voice" in w]
    assert len(passive_voice_warnings) == 1
    assert "REQ-003" in passive_voice_warnings[0]

    vague_warnings = [w for w in warnings if "vague adjective" in w]
    assert len(vague_warnings) == 0


def test_parse_spec_ignores_referenced_ids_outside_definition_sections(
    tmp_path: Path,
) -> None:
    # Test that IDs referenced in Context or Goal section are not parsed as requirements/constraints defined in the spec
    spec_content = """\
# test-feature

## 1. Goal

- This enables JWT token capability. Related to REQ-999.
- Completion signal: success.

## 2. Requirements

- `REQ-001`: The system MUST validate auth tokens.

## 5. Context

- This builds on REQ-888 which was implemented previously.
"""
    p = tmp_path / "test-ref.specs.md"
    p.write_text(spec_content, encoding="utf-8")
    doc = parse_spec(p)
    assert "REQ-001" in doc.reqs
    assert "REQ-999" not in doc.reqs
    assert "REQ-888" not in doc.reqs


def test_parse_plan_multiline_fields(tmp_path: Path) -> None:
    plan_text = """\
# test-feature

Spec: [test-feature.specs.md](test-feature.specs.md)

## PHASE-001: Implementation

### TASK-001: Multi-line action task
Depends on: none
Files: [src/auth.ts](src/auth.ts)
Symbols: none
Satisfies: REQ-001
Action: Start the implementation.
  Then configure the security headers.
  Finally run unit tests.
Validate: `npm test`
Expected result:
  All unit tests pass successfully.
  Coverage is above 90%.

## PHASE-END: Acceptance
"""
    p = tmp_path / "test-multiline.plan.md"
    p.write_text(plan_text, encoding="utf-8")
    doc = parse_plan(p)
    assert len(doc.tasks) == 1
    task = doc.tasks[0]
    assert (
        task.fields["Action"]
        == "Start the implementation.\n  Then configure the security headers.\n  Finally run unit tests."
    )
    assert (
        task.fields["Expected result"]
        == "All unit tests pass successfully.\n  Coverage is above 90%."
    )


def test_parse_plan_multiline_fields_with_blank_lines(tmp_path: Path) -> None:
    plan_text = """\
# test-feature

Spec: [test-feature.specs.md](test-feature.specs.md)

## PHASE-001: Implementation

### TASK-001: Multi-line field with blank lines
Depends on: none
Files: [src/auth.ts](src/auth.ts)
Symbols: none
Satisfies: REQ-001
Action:
  Line 1 of action.

  Line 2 of action after a blank line.
Validate: `npm test`
Expected result: Done.

## PHASE-END: Acceptance
"""
    p = tmp_path / "test-multiline-blank.plan.md"
    p.write_text(plan_text, encoding="utf-8")
    doc = parse_plan(p)
    assert len(doc.tasks) == 1
    task = doc.tasks[0]
    assert (
        task.fields["Action"]
        == "Line 1 of action.\n\n  Line 2 of action after a blank line."
    )


def test_validate_plan_bare_path_check(tmp_path: Path) -> None:
    plan_text = """\
# test-feature

Spec: [test-feature.specs.md](test-feature.specs.md)

## PHASE-001: Implementation

### TASK-001: Implement something
Depends on: none
Files: [src/auth.ts](src/auth.ts), src/other.ts
Symbols: none
Satisfies: REQ-001
Action: Add something.
Validate: `npm test`
Expected result: Done.

## PHASE-END: Acceptance
"""
    p = tmp_path / "test-bare-path.plan.md"
    p.write_text(plan_text, encoding="utf-8")
    errs, _ = validate_plan(p)
    assert any("bare path" in e and "src/other.ts" in e for e in errs)


def test_scaffold_domain_injection_sketch(tmp_path: Path) -> None:
    # Test that domain injection works in sketch depth
    spec_path, plan_path = scaffold(
        "feat-sketch", depth="sketch", out_dir=tmp_path, domain="api"
    )
    spec_text = spec_path.read_text(encoding="utf-8")
    assert "Standard error cases" in spec_text
    assert "SEC-101" in spec_text


def test_validate_resolve_paths_bare_stem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Set current working directory to tmp_path
    monkeypatch.chdir(tmp_path)

    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()

    spec_file = plan_dir / "auth-jwt.specs.md"
    spec_file.write_text("# auth-jwt", encoding="utf-8")

    from validate import _resolve_paths

    spec_path, plan_path = _resolve_paths("auth-jwt")

    assert spec_path == spec_file.resolve()
    assert plan_path == (plan_dir / "auth-jwt.plan.md").resolve()


# ---------------------------------------------------------------------------
# validate_review tests (G1)
# ---------------------------------------------------------------------------


def test_validate_review_missing_file(tmp_path: Path) -> None:
    spec = tmp_path / "foo.specs.md"
    errors, warnings = validate_review(spec)
    assert any("not found" in e.lower() for e in errors)


def test_validate_review_passes_when_true(tmp_path: Path) -> None:
    review = tmp_path / "foo.review.md"
    review.write_text("ready_for_execution: true\n", encoding="utf-8")
    spec = tmp_path / "foo.specs.md"
    errors, warnings = validate_review(spec)
    assert errors == []


def test_validate_review_fails_when_field_absent(tmp_path: Path) -> None:
    review = tmp_path / "foo.review.md"
    review.write_text("# Review\nNo verdict here.\n", encoding="utf-8")
    spec = tmp_path / "foo.specs.md"
    errors, warnings = validate_review(spec)
    assert errors


def test_validate_review_fails_when_false_despite_true_in_comment(
    tmp_path: Path,
) -> None:
    # Regression: substring "ready_for_execution: true" in a comment must not pass
    review = tmp_path / "foo.review.md"
    review.write_text(
        "# Review\n<!-- ready_for_execution: true is the goal -->\nready_for_execution: false\n",
        encoding="utf-8",
    )
    spec = tmp_path / "foo.specs.md"
    errors, warnings = validate_review(spec)
    assert errors


# ---------------------------------------------------------------------------
# validate_cross and validate_plan edge cases (G2)
# ---------------------------------------------------------------------------


def test_validate_cross_fully_covered(spec_file: Path, tmp_path: Path) -> None:
    # Plan covers all three impl IDs from spec_file: REQ-001, REQ-002, SEC-001
    plan_text = """\
# test-feature

Spec: [test-feature.specs.md](test-feature.specs.md)

## PHASE-001: Implementation

### TASK-001: Implement login

Depends on: none
Files: [src/auth.ts](src/auth.ts)
Symbols: [issueJwt](src/auth.ts#L10)
Satisfies: REQ-001, SEC-001
Action: Add JWT issuance with expiry.
Validate: `npm test -- auth.test.ts`
Expected result: All tests pass.

### TASK-002: Implement token rejection

Depends on: TASK-001
Files: [src/auth.ts](src/auth.ts)
Symbols: [rejectInvalid](src/auth.ts#L20)
Satisfies: REQ-002
Action: Reject requests with missing or invalid Bearer token.
Validate: `npm test -- auth.test.ts`
Expected result: 401 returned on invalid token.

## PHASE-END: Acceptance
"""
    plan_path = spec_file.parent / "test-feature.plan.md"
    plan_path.write_text(plan_text, encoding="utf-8")
    errors, warnings, matrix = validate_cross(spec_file, plan_path)
    assert matrix["uncovered"] == [], (
        f"expected no uncovered reqs, got {matrix['uncovered']}"
    )
    assert not errors, f"unexpected errors: {errors}"


def test_validate_plan_missing_file(tmp_path: Path) -> None:
    errors, warnings = validate_plan(tmp_path / "plan" / "missing.plan.md")
    assert any("not found" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Pipeline tests (execute_plan_pipeline.py)
# ---------------------------------------------------------------------------


def _run_pipeline(name: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).parent.parent / "scripts" / "execute_plan_pipeline.py"
    return subprocess.run(
        [sys.executable, str(script), "--name", name],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_pipeline_succeeds_on_already_authored_artifacts(
    spec_file: Path, plan_file: Path, tmp_path: Path
) -> None:
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    shutil.copy(spec_file, plan_dir / spec_file.name)
    shutil.copy(plan_file, plan_dir / plan_file.name)

    result = _run_pipeline("test-feature", cwd=tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Pipeline completed successfully" in result.stdout


def test_pipeline_fails_cleanly_when_plan_missing(
    spec_file: Path, tmp_path: Path
) -> None:
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    shutil.copy(spec_file, plan_dir / spec_file.name)

    result = _run_pipeline("test-feature", cwd=tmp_path)

    assert result.returncode == 1
    assert "not found" in result.stdout.lower()
