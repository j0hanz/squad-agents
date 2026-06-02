"""Tests for skills/planning/scripts — scaffold, sync, parser, validate."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_parser import parse_spec, parse_plan  # noqa: E402
from scaffold import scaffold  # noqa: E402
from sync import sync  # noqa: E402
from validate import validate_spec, validate_plan, validate_cross  # noqa: E402


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
def plan_file(tmp_path: Path, spec_file: Path) -> Path:
    """A minimal plan with one task that satisfies REQ-001."""
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
    p = tmp_path / "test-feature.plan.md"
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
    import shutil

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
    assert errors == [], f"unexpected errors: {errors}"


def test_validate_plan_valid(plan_file: Path) -> None:
    errors, warnings = validate_plan(plan_file)
    assert errors == [], f"unexpected errors: {errors}"


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
