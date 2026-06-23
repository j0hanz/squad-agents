"""Tests for codebase-init run.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from run import (  # noqa: E402
    render_agents_md_skeleton,
    validate_agents_md_file,
    analyze_project_env,
    validate_hooks_config,
    validate_manifest_file,
    should_ignore,
    wire_agents_files,
    get_dependencies,
    validate_skill_files,
)


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


def test_unresolved_model_name_placeholder_fails(tmp_path: Path) -> None:
    body = _BASE_BODY.replace(
        "Co-Authored-By: Claude <noreply@anthropic.com>",
        "Co-Authored-By: <Model Name>",
    )
    path = _write_agents_md(tmp_path, body)
    result = validate_agents_md_file(path)
    assert result.success is False
    assert any("<Model Name>" in str(issue) for issue in result.issues)


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
        "python",
        "test repo",
        "strict",
        "production",
        "not-enforced",
        ci="github-actions",
    )
    # The raw skeleton always leaves "<Model Name>" unresolved (see Phase 2
    # post-generation actions, which substitute it before declaring done).
    content = content.replace("<Model Name>", "Claude")
    path = _write_agents_md(tmp_path, content)
    result = validate_agents_md_file(path)
    assert not result.has_errors


def test_scaffold_skeleton_unsubstituted_model_name_fails(tmp_path: Path) -> None:
    content = render_agents_md_skeleton(
        "python",
        "test repo",
        "strict",
        "production",
        "not-enforced",
        ci="github-actions",
    )
    path = _write_agents_md(tmp_path, content)
    result = validate_agents_md_file(path)
    assert result.has_errors


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
    assert any(
        "missing the 'ci' parameter" in str(issue).lower() for issue in result.issues
    )

    # Adding 'ci' should resolve the warning
    body_with_ci = body.replace(
        "testing=always -->", "testing=always ci=github-actions -->"
    )
    path_with_ci = _write_agents_md(tmp_path, body_with_ci)
    result_with_ci = validate_agents_md_file(path_with_ci)
    assert not any(
        "missing the 'ci' parameter" in str(issue).lower()
        for issue in result_with_ci.issues
    )


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
    assert (
        "<!-- codebase-init:hard-rules v1 commit=relaxed maturity=development testing=always ci=github-actions -->"
        in content
    )

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
    assert (
        "<!-- codebase-init:hard-rules v1 commit=strict maturity=production testing=touched-files ci=gitlab-ci -->"
        in python_content
    )
    assert (
        "typing: use Type Annotations (PEP 484) on all public function definitions"
        in python_content
    )


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

    (workflows_dir / "ci.yml").write_text("name: CI", encoding="utf-8")
    env = analyze_project_env(tmp_path)
    assert env.ci_provider == "github-actions"


def test_hooks_config_with_arguments(tmp_path: Path) -> None:
    # Set up dummy hooks.json and handler script in tmp_path
    hooks_file = tmp_path / "hooks" / "hooks.json"
    hooks_file.parent.mkdir(parents=True, exist_ok=True)

    # Create the script file so it exists
    script_file = tmp_path / "hooks" / "shell-safety.sh"
    script_file.write_text("echo 'hello'", encoding="utf-8")

    # Command containing trailing arguments/flags
    hooks_content = """{
        "hooks": {
            "PreToolUse": [
                {
                    "hooks": [
                        {
                            "command": "bash \\"${CLAUDE_PLUGIN_ROOT}/hooks/shell-safety.sh\\" --verbose"
                        }
                    ]
                }
            ]
        }
    }"""
    hooks_file.write_text(hooks_content, encoding="utf-8")

    result = validate_hooks_config(hooks_file)
    assert result.success is True
    assert len(result.issues) == 0


def test_hooks_config_with_null_hooks(tmp_path: Path) -> None:
    hooks_file = tmp_path / "hooks" / "hooks.json"
    hooks_file.parent.mkdir(parents=True, exist_ok=True)

    # Null hooks key under a hook entry
    hooks_content = """{
        "hooks": {
            "PreToolUse": [
                {
                    "hooks": null
                }
            ]
        }
    }"""
    hooks_file.write_text(hooks_content, encoding="utf-8")

    # This should return a clean validation error/warning instead of crashing
    result = validate_hooks_config(hooks_file)
    assert result.success is False
    assert any(
        "must be an array" in str(issue).lower()
        or "must be an object" in str(issue).lower()
        for issue in result.issues
    )


def test_manifest_file_type_safety(tmp_path: Path) -> None:
    manifest_file = tmp_path / "plugin.json"

    # Write invalid manifest containing an array instead of a dict object
    manifest_file.write_text("[1, 2, 3]", encoding="utf-8")
    result = validate_manifest_file(manifest_file)
    assert result.success is False
    assert any(
        "Manifest must be a JSON object" in str(issue) for issue in result.issues
    )


def test_agents_md_utf8_bom(tmp_path: Path) -> None:
    body = "\ufeff" + _BASE_BODY.replace(
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
    assert result.success is True
    assert not any("H1 header" in str(issue) for issue in result.issues)


def test_should_ignore_leading_slash() -> None:
    root = Path("C:/my_project")
    # Anchored path
    assert should_ignore(Path("C:/my_project/dist"), {"/dist"}, root) is True
    assert should_ignore(Path("C:/my_project/subdir/dist"), {"/dist"}, root) is False

    # Non-anchored path
    assert should_ignore(Path("C:/my_project/dist"), {"dist"}, root) is True
    assert should_ignore(Path("C:/my_project/subdir/dist"), {"dist"}, root) is True


def test_should_ignore_case_sensitivity() -> None:
    root = Path("C:/my_project")
    # A wildcard pattern should match case-sensitively on all systems
    assert should_ignore(Path("C:/my_project/Dist"), {"di*t"}, root) is False
    assert should_ignore(Path("C:/my_project/dist"), {"di*t"}, root) is True


def test_agents_md_multiline_comment_handling(tmp_path: Path) -> None:
    body = _BASE_BODY.replace(
        "## Commit Attribution",
        "## Hard Rules\n\n"
        "- **Commit policy:** placeholder\n"
        "- **Project maturity:** placeholder\n"
        "- **Testing rigor:** placeholder\n\n"
        "<!-- codebase-init:hard-rules v1 commit=strict maturity=production testing=always ci=github-actions -->\n\n"
        "<!--\n"
        "filler words welcome to this doc\n"
        "unresolved todo check should still trigger:\n"
        "TODO: this should fail\n"
        "-->\n\n"
        "## Commit Attribution",
    )
    path = _write_agents_md(tmp_path, body)
    result = validate_agents_md_file(path)
    assert result.success is False
    # Check that it detected the TODO but NOT the filler words inside the multiline comment
    assert any("Unresolved TODO detected" in str(issue) for issue in result.issues)
    assert not any("Filler text detected" in str(issue) for issue in result.issues)


def test_wire_agents_files_success(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    source = tmp_path / "AGENTS.md"
    source.write_text("Source content", encoding="utf-8")

    target1 = tmp_path / "CLAUDE.md"
    target2 = tmp_path / "GEMINI.md"

    code = wire_agents_files(source, [target1, target2])
    assert code == 0
    assert target1.read_text(encoding="utf-8") == "# See [AGENTS.md](AGENTS.md)\n"
    assert target2.read_text(encoding="utf-8") == "# See [AGENTS.md](AGENTS.md)\n"


def test_wire_agents_files_outside_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    # Create source inside root
    source = tmp_path / "AGENTS.md"
    source.write_text("Source content", encoding="utf-8")

    # Try target outside root (using parent directory)
    outside_dir = tmp_path.parent
    target = outside_dir / "CLAUDE.md"

    code = wire_agents_files(source, [target])
    assert code == 1
    assert not target.exists()


def test_get_dependencies(tmp_path: Path) -> None:
    # Create fake node_modules directory with some files
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()

    file1 = node_modules / "a.js"
    file1.write_text("console.log(1);", encoding="utf-8")

    sub = node_modules / "sub"
    sub.mkdir()
    file2 = sub / "b.js"
    file2.write_text("x" * 1024 * 1024, encoding="utf-8")  # 1 MB

    deps = get_dependencies(tmp_path)
    assert len(deps) == 1
    assert deps[0].name == "node_modules"
    assert deps[0].size_mb > 0.9


def test_validate_skill_files(tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Create a valid skill
    skill1 = skills_dir / "valid-skill"
    skill1.mkdir()
    (skill1 / "SKILL.md").write_text(
        "---\nname: valid-skill\ndescription: valid desc\n---\nBody content",
        encoding="utf-8",
    )

    # Create an invalid skill (missing SKILL.md)
    skill2 = skills_dir / "invalid-no-skill-md"
    skill2.mkdir()

    # Create an invalid skill (missing frontmatter name)
    skill3 = skills_dir / "invalid-missing-name"
    skill3.mkdir()
    (skill3 / "SKILL.md").write_text(
        "---\ndescription: missing name\n---\nBody", encoding="utf-8"
    )

    # Create a skill that is too long (above 150 lines default)
    skill4 = skills_dir / "too-long"
    skill4.mkdir()
    long_content = "---\nname: too-long\ndescription: test desc\n---\n" + "\n".join(
        ["line"] * 160
    )
    (skill4 / "SKILL.md").write_text(long_content, encoding="utf-8")

    res = validate_skill_files(skills_dir)
    assert res.success is False

    # Find issues related to each skill
    messages = [issue.message for issue in res.issues]
    assert any("has no SKILL.md" in m for m in messages)
    assert any("missing frontmatter key: 'name'" in m for m in messages)
    assert any("is long (>150 lines)" in m for m in messages)
