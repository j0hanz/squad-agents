"""Tests for codebase-init run.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from run import render_agents_md_skeleton, validate_agents_md_file  # noqa: E402


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
    body = _BASE_BODY + "\n# See [AGENTS.md](../AGENTS.md)\n"
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


def test_well_formed_marker_does_not_trigger_generic_advice_warn(
    tmp_path: Path,
) -> None:
    # testing=always must not be flagged by the generic-advice heuristic,
    # which otherwise matches the bare word "always".
    body = _BASE_BODY.replace(
        "## Commit Attribution",
        "## Hard Rules\n\n"
        "- **Commit policy:** placeholder\n"
        "- **Project maturity:** placeholder\n"
        "- **Testing rigor:** placeholder\n\n"
        "<!-- codebase-init:hard-rules v1 commit=strict maturity=production testing=always -->\n\n"
        "## Commit Attribution",
    )
    path = _write_agents_md(tmp_path, body)
    result = validate_agents_md_file(path)
    assert not any("generic advice" in str(issue).lower() for issue in result.issues)


def test_generic_advice_inside_code_fence_is_ignored(tmp_path: Path) -> None:
    body = _BASE_BODY.replace(
        "## Commit Attribution",
        "## Hard Rules\n\n"
        "- **Commit policy:** placeholder\n"
        "- **Project maturity:** placeholder\n"
        "- **Testing rigor:** placeholder\n\n"
        "```\n// always validate input\n```\n\n"
        "## Commit Attribution",
    )
    path = _write_agents_md(tmp_path, body)
    result = validate_agents_md_file(path)
    assert not any("generic advice" in str(issue).lower() for issue in result.issues)


def test_scaffold_skeleton_has_hard_rules_before_toolchain() -> None:
    content = render_agents_md_skeleton(
        "node", "test repo", "relaxed", "development", "always"
    )
    assert content.index("## Hard Rules") < content.index("## Package Manager")
    assert (
        "<!-- codebase-init:hard-rules v1 commit=relaxed maturity=development testing=always -->"
        in content
    )


def test_scaffold_skeleton_applies_overrides() -> None:
    content = render_agents_md_skeleton(
        "node",
        "test repo",
        "relaxed",
        "development",
        "always",
        pm_override="npm",
        toolchain_overrides={"test": "npm test"},
    )
    assert "pm: npm" in content
    assert "test: `npm test`" in content
    assert "dev: `pnpm dev`" in content  # untouched default survives


def test_scaffold_skeleton_rejects_unknown_language() -> None:
    try:
        render_agents_md_skeleton("cobol", "x", "relaxed", "development", "always")
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown language")


def test_scaffold_skeleton_passes_validation(tmp_path: Path) -> None:
    content = render_agents_md_skeleton(
        "python", "test repo", "strict", "production", "not-enforced"
    )
    path = _write_agents_md(tmp_path, content)
    result = validate_agents_md_file(path)
    assert not result.has_errors
