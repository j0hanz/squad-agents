"""Tests for skills/make-a-skill/scripts — scaffold_skill, validate_skill."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scaffold_skill import scaffold  # noqa: E402
from validate_skill import validate_skill  # noqa: E402


# ---------------------------------------------------------------------------
# scaffold_skill
# ---------------------------------------------------------------------------


def test_scaffold_writes_skill_md_with_real_name(tmp_path: Path) -> None:
    created = scaffold("demo-skill", out_dir=tmp_path)
    skill_md = tmp_path / "demo-skill" / "SKILL.md"
    assert created == [skill_md]
    content = skill_md.read_text(encoding="utf-8")
    assert "name: demo-skill" in content
    assert "{{FILL" in content  # description and body are placeholders


def test_scaffold_rejects_uppercase_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        scaffold("Demo-Skill", out_dir=tmp_path)


def test_scaffold_rejects_path_separator_in_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        scaffold("demo/skill", out_dir=tmp_path)


def test_scaffold_refuses_overwrite_without_force(tmp_path: Path) -> None:
    scaffold("demo-skill", out_dir=tmp_path)
    with pytest.raises(FileExistsError):
        scaffold("demo-skill", out_dir=tmp_path)
    scaffold("demo-skill", out_dir=tmp_path, force=True)  # does not raise


def test_scaffold_optional_dirs(tmp_path: Path) -> None:
    created = scaffold(
        "demo-skill",
        out_dir=tmp_path,
        with_scripts=True,
        with_references=True,
        with_evals=True,
    )
    paths = {p.name for p in created}
    assert "demo_skill.py" in paths
    assert "checklist.md" in paths
    assert "evals.json" in paths
    evals_data = json.loads(
        (tmp_path / "demo-skill" / "evals" / "evals.json").read_text()
    )
    assert evals_data["skill_name"] == "demo-skill"


# ---------------------------------------------------------------------------
# validate_skill — structural errors
# ---------------------------------------------------------------------------


def test_freshly_scaffolded_skill_fails_validation(tmp_path: Path) -> None:
    scaffold("demo-skill", out_dir=tmp_path)
    errors, _ = validate_skill(tmp_path / "demo-skill" / "SKILL.md")
    assert any("description" in e and "FILL" in e for e in errors)
    assert any("unfilled" in e for e in errors)


def test_fully_drafted_skill_passes_validation(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """\
---
name: demo-skill
description: "Does a demonstration thing for tests. Not for production use. Trigger on: 'demo skill', 'run the demo'."
disable-model-invocation: false
---

# demo-skill

Does exactly one thing, for test purposes.

## Step 1: Do the thing

Run the thing.
""",
        encoding="utf-8",
    )
    errors, warnings = validate_skill(skill_dir / "SKILL.md")
    assert errors == []


def test_name_directory_mismatch_is_error(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: wrong-name\ndescription: "x" \n---\n\n# demo\n',
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("does not match" in e for e in errors)


def test_missing_frontmatter_is_error(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "# demo-skill\n\nNo frontmatter here.\n", encoding="utf-8"
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("frontmatter" in e.lower() for e in errors)


def test_dangling_reference_link_is_error(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "long enough description text padded out to a hundred and twenty characters minimum so the warning does not fire here, ok"\n---\n\n'
        "# demo-skill\n\nRead `references/missing.md` for details.\n",
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("references/missing.md" in e for e in errors)


def test_placeholder_mentioned_in_code_span_is_not_an_error(tmp_path: Path) -> None:
    """A skill explaining the {{FILL convention in backticks (like make-a-skill's
    own SKILL.md) must not be flagged as having an unfilled placeholder."""
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "long enough description text padded out to a hundred and twenty characters minimum so the warning does not fire here, ok"\n---\n\n'
        "# demo-skill\n\nFill in every `{{FILL: ...}}` placeholder before validating.\n",
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert errors == []


# ---------------------------------------------------------------------------
# validate_skill — evals.json shape variants
# ---------------------------------------------------------------------------


def _base_skill(tmp_path: Path) -> Path:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "long enough description text padded out to a hundred and twenty characters minimum so the warning does not fire here, ok"\n---\n\n'
        "# demo-skill\n\nDoes a thing.\n",
        encoding="utf-8",
    )
    return skill_dir


def test_evals_bare_array_shape_is_valid(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(
        json.dumps([{"prompt": "do the thing", "assertions": ["it did the thing"]}]),
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert errors == []


def test_evals_object_shape_is_valid(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(
        json.dumps(
            {
                "skill_name": "demo-skill",
                "evals": [
                    {"prompt": "do the thing", "expectations": ["it did the thing"]}
                ],
            }
        ),
        encoding="utf-8",
    )
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert errors == []


def test_malformed_evals_json_is_error(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text("{not valid json", encoding="utf-8")
    errors, _ = validate_skill(skill_dir / "SKILL.md")
    assert any("not valid JSON" in e for e in errors)


def test_vague_adjective_is_warning_not_error(tmp_path: Path) -> None:
    skill_dir = _base_skill(tmp_path)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8") + "\nThis is a simple and robust step.\n",
        encoding="utf-8",
    )
    errors, warnings = validate_skill(skill_md)
    assert errors == []
    assert any("simple" in w for w in warnings)
    assert any("robust" in w for w in warnings)
