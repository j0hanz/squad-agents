"""Tests for codebase-init run.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from run import validate_agents_md_file  # noqa: E402


def _write_agents_md(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "AGENTS.md"
    path.write_text(body, encoding="utf-8")
    return path


_BASE_BODY = """# Agent Instructions

## File-Scoped Commands

| Task | Command |
| ---- | ------- |
| Test | `pytest` |

## Commit Attribution

Co-Authored-By: Claude <noreply@anthropic.com>
"""


def test_hard_rules_section_required_fails(tmp_path: Path) -> None:
    path = _write_agents_md(tmp_path, _BASE_BODY)
    result = validate_agents_md_file(path)
    assert result.success is False
    assert any("Hard Rules" in str(issue) for issue in result.issues)


def test_package_override_exempt_from_hard_rules(tmp_path: Path) -> None:
    body = _BASE_BODY + "\nSee root `/AGENTS.md` for shared setup and workspace commands.\n"
    path = _write_agents_md(tmp_path, body)
    result = validate_agents_md_file(path)
    assert not any("Hard Rules" in str(issue) for issue in result.issues)


def test_hard_rules_marker_missing_warns(tmp_path: Path) -> None:
    body = _BASE_BODY.replace(
        "## Commit Attribution",
        "## Hard Rules\n\n"
        "- **Commit policy:** placeholder\n"
        "- **Project maturity:** placeholder\n"
        "- **Testing rigor:** placeholder\n\n"
        "## Commit Attribution",
    )
    path = _write_agents_md(tmp_path, body)
    result = validate_agents_md_file(path)
    assert result.success is True
    assert any("marker" in str(issue).lower() for issue in result.issues)


def test_hard_rules_marker_malformed_warns(tmp_path: Path) -> None:
    body = _BASE_BODY.replace(
        "## Commit Attribution",
        "## Hard Rules\n\n"
        "- **Commit policy:** placeholder\n"
        "- **Project maturity:** placeholder\n"
        "- **Testing rigor:** placeholder\n\n"
        "## Commit Attribution",
    )
    body += "\n<!-- codebase-init:hard-rules v2 commit=strict maturity=development testing=touched-files -->\n"
    path = _write_agents_md(tmp_path, body)
    result = validate_agents_md_file(path)
    assert result.success is True
    assert any("marker" in str(issue).lower() for issue in result.issues)
