"""Tests for codebase-init run.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from run import render_agents_md_skeleton, validate_agents_md_file, analyze_project_env  # noqa: E402


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
        "<!-- codebase-init:hard-rules v1 commit=strict maturity=production testing=always ci=github-actions -->\n\n"
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
        "node", "test repo", "relaxed", "development", "always", ci="github-actions"
    )
    assert content.index("## Hard Rules") < content.index("## Package Manager")
    assert (
        "<!-- codebase-init:hard-rules v1 commit=relaxed maturity=development testing=always ci=github-actions -->"
        in content
    )


def test_scaffold_skeleton_applies_overrides() -> None:
    content = render_agents_md_skeleton(
        "node",
        "test repo",
        "relaxed",
        "development",
        "always",
        ci="github-actions",
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
        "python", "test repo", "strict", "production", "not-enforced", ci="github-actions"
    )
    path = _write_agents_md(tmp_path, content)
    result = validate_agents_md_file(path)
    assert not result.has_errors


def test_hard_rules_marker_missing_ci_warns(tmp_path: Path) -> None:
    # A marker without 'ci' should trigger a warning
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
    assert result.success is True  # Warning, not a failure
    assert any("missing the 'ci' parameter" in str(issue).lower() for issue in result.issues)

    # Adding 'ci' should resolve the warning
    body_with_ci = body.replace(
        "testing=always -->",
        "testing=always ci=github-actions -->"
    )
    path_with_ci = _write_agents_md(tmp_path, body_with_ci)
    result_with_ci = validate_agents_md_file(path_with_ci)
    assert not any("missing the 'ci' parameter" in str(issue).lower() for issue in result_with_ci.issues)


def test_todo_detection_in_comments_and_code_blocks(tmp_path: Path) -> None:
    # 1. TODO in standard text (should fail)
    body1 = _BASE_BODY.replace(
        "## Commit Attribution",
        "## Hard Rules\n\n"
        "- **Commit policy:** placeholder\n"
        "- **Project maturity:** placeholder\n"
        "- **Testing rigor:** placeholder\n\n"
        "<!-- codebase-init:hard-rules v1 commit=strict maturity=production testing=always ci=github-actions -->\n\n"
        "TODO: finish this section\n\n"
        "## Commit Attribution",
    )
    path1 = _write_agents_md(tmp_path, body1)
    result1 = validate_agents_md_file(path1)
    assert result1.success is False
    assert any("Unresolved TODO detected" in str(issue) for issue in result1.issues)

    # 2. TODO in HTML comments (should fail)
    body2 = _BASE_BODY.replace(
        "## Commit Attribution",
        "## Hard Rules\n\n"
        "- **Commit policy:** placeholder\n"
        "- **Project maturity:** placeholder\n"
        "- **Testing rigor:** placeholder\n\n"
        "<!-- codebase-init:hard-rules v1 commit=strict maturity=production testing=always ci=github-actions -->\n\n"
        "<!-- TODO: fix formatting -->\n\n"
        "## Commit Attribution",
    )
    path2 = _write_agents_md(tmp_path, body2)
    result2 = validate_agents_md_file(path2)
    assert result2.success is False
    assert any("Unresolved TODO detected" in str(issue) for issue in result2.issues)

    # 3. TODO inside code fence (should be ignored)
    body3 = _BASE_BODY.replace(
        "## Commit Attribution",
        "## Hard Rules\n\n"
        "- **Commit policy:** placeholder\n"
        "- **Project maturity:** placeholder\n"
        "- **Testing rigor:** placeholder\n\n"
        "<!-- codebase-init:hard-rules v1 commit=strict maturity=production testing=always ci=github-actions -->\n\n"
        "```\n"
        "// TODO: this is ignored in code blocks\n"
        "```\n\n"
        "## Commit Attribution",
    )
    path3 = _write_agents_md(tmp_path, body3)
    result3 = validate_agents_md_file(path3)
    assert result3.success is True
    assert not any("Unresolved TODO detected" in str(issue) for issue in result3.issues)


def test_scaffold_skeleton_generates_conventions_and_ci() -> None:
    content = render_agents_md_skeleton(
        "node", "test repo", "relaxed", "development", "always", ci="github-actions"
    )
    # Check that CI rule is generated
    assert "ci: automated CI running on GitHub Actions" in content
    assert "<!-- codebase-init:hard-rules v1 commit=relaxed maturity=development testing=always ci=github-actions -->" in content
    
    # Check language conventions are present
    assert "## Key Conventions" in content
    assert "imports: ESM import/export syntax only — no CommonJS require()" in content
    
    # Check that there is no TODO checklist
    assert "- [ ]" not in content
    assert "TODO" not in content

    # Test another language: python
    python_content = render_agents_md_skeleton(
        "python", "test repo", "strict", "production", "touched-files", ci="gitlab-ci"
    )
    assert "ci: automated CI running on GitLab CI" in python_content
    assert "<!-- codebase-init:hard-rules v1 commit=strict maturity=production testing=touched-files ci=gitlab-ci -->" in python_content
    assert "typing: use Type Annotations (PEP 484) on all public function definitions" in python_content


def test_automated_ci_detection(tmp_path: Path) -> None:
    # 1. Fallback / local-only
    env = analyze_project_env(tmp_path)
    assert env.ci_provider == "local-only"

    # 2. GitLab CI detection
    (tmp_path / ".gitlab-ci.yml").write_text("some-gitlab-ci-content", encoding="utf-8")
    env = analyze_project_env(tmp_path)
    assert env.ci_provider == "gitlab-ci"

    # Clean up GitLab CI file
    (tmp_path / ".gitlab-ci.yml").unlink()

    # 3. GitHub Actions detection (empty workflows folder)
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    env = analyze_project_env(tmp_path)
    assert env.ci_provider == "local-only"  # empty workflows folder is local-only

    # 4. GitHub Actions detection (workflows folder with files)
    (workflows_dir / "ci.yml").write_text("name: CI", encoding="utf-8")
    env = analyze_project_env(tmp_path)
    assert env.ci_provider == "github-actions"
