"""Tests for validate_agent.py — the subagent definition linter."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import validate_agent as va  # noqa: E402


# --- frontmatter parsing ---


def test_split_frontmatter_present():
    block, body = va.split_frontmatter("---\nname: x\n---\nbody here")
    assert block == "name: x"
    assert body.strip() == "body here"


def test_split_frontmatter_absent():
    block, body = va.split_frontmatter("no frontmatter\njust text")
    assert block is None


def test_parse_scalar_and_quoted():
    fm = va.parse_frontmatter('name: my-agent\nmodel: "sonnet"')
    assert fm["name"] == "my-agent"
    assert fm["model"] == "sonnet"


def test_parse_inline_comment_stripped():
    fm = va.parse_frontmatter("name: my-agent   # a comment")
    assert fm["name"] == "my-agent"


def test_parse_folded_block_scalar_with_comment():
    block = "description: >   # trigger\n  first line\n  second line\nmodel: sonnet"
    fm = va.parse_frontmatter(block)
    assert fm["description"] == "first line second line"
    assert fm["model"] == "sonnet"


def test_parse_inline_list():
    fm = va.parse_frontmatter("tools: [Read, Grep, Glob]")
    assert fm["tools"] == ["Read", "Grep", "Glob"]


def test_parse_block_list():
    fm = va.parse_frontmatter("skills:\n  - one\n  - two\nmodel: opus")
    assert fm["skills"] == ["one", "two"]
    assert fm["model"] == "opus"


def test_tool_names_strips_parens():
    assert va._tool_names("Agent(worker, researcher), Read") == ["Agent", "Read"]
    assert va._tool_names(["Bash", "Read"]) == ["Bash", "Read"]


# --- validation rules ---


def _write(tmp_path, text):
    p = tmp_path / "agent.md"
    p.write_text(text, encoding="utf-8")
    return p


GOOD = """---
name: security-reviewer
description: Audits a diff for security vulnerabilities. Use proactively after auth changes.
tools: Read, Grep, Glob
model: opus
---

You are a security reviewer. You audit code and report findings. You never modify code.

## Output
Return a markdown list of findings.
"""


def test_good_agent_no_errors(tmp_path):
    rep = va.validate(_write(tmp_path, GOOD))
    assert rep.errors == []


def test_missing_frontmatter(tmp_path):
    rep = va.validate(_write(tmp_path, "just a body, no frontmatter"))
    assert any("FM001" in e for e in rep.errors)


def test_bad_name_kebab(tmp_path):
    rep = va.validate(_write(tmp_path, GOOD.replace("security-reviewer", "Bad Name")))
    assert any("NAME003" in e for e in rep.errors)


def test_name_too_long(tmp_path):
    long_name = "a" * 65
    rep = va.validate(_write(tmp_path, GOOD.replace("security-reviewer", long_name)))
    assert any("NAME002" in e for e in rep.errors)


def test_missing_description(tmp_path):
    text = "---\nname: ok-agent\ntools: Read\n---\n\nBody with output contract.\nReturn a result.\n"
    rep = va.validate(_write(tmp_path, text))
    assert any("DESC001" in e for e in rep.errors)


def test_invalid_permission_mode(tmp_path):
    rep = va.validate(
        _write(
            tmp_path, GOOD.replace("model: opus", "model: opus\npermissionMode: yolo")
        )
    )
    assert any("PERM001" in e for e in rep.errors)


def test_bypass_permissions_warns(tmp_path):
    rep = va.validate(
        _write(
            tmp_path,
            GOOD.replace(
                "model: opus", "model: opus\npermissionMode: bypassPermissions"
            ),
        )
    )
    assert any("PERM002" in w for w in rep.warnings)


def test_invalid_effort(tmp_path):
    rep = va.validate(
        _write(tmp_path, GOOD.replace("model: opus", "model: opus\neffort: turbo"))
    )
    assert any("EFFORT001" in e for e in rep.errors)


def test_invalid_isolation(tmp_path):
    rep = va.validate(
        _write(tmp_path, GOOD.replace("model: opus", "model: opus\nisolation: sandbox"))
    )
    assert any("ISO001" in e for e in rep.errors)


def test_unknown_model_warns(tmp_path):
    rep = va.validate(_write(tmp_path, GOOD.replace("model: opus", "model: gpt-4")))
    assert any("MODEL001" in w for w in rep.warnings)


def test_full_model_id_ok(tmp_path):
    rep = va.validate(
        _write(tmp_path, GOOD.replace("model: opus", "model: claude-opus-4-8"))
    )
    assert not any("MODEL001" in w for w in rep.warnings)


def test_forbidden_tool_warns(tmp_path):
    rep = va.validate(
        _write(
            tmp_path,
            GOOD.replace("tools: Read, Grep, Glob", "tools: Read, AskUserQuestion"),
        )
    )
    assert any("TOOL001" in w for w in rep.warnings)


def test_escalation_tool_info(tmp_path):
    rep = va.validate(
        _write(
            tmp_path,
            GOOD.replace("tools: Read, Grep, Glob", "tools: Read, Bash, Write"),
        )
    )
    assert any("TOOL002" in i for i in rep.infos)


def test_tools_omitted_warns(tmp_path):
    text = "---\nname: ok-agent\ndescription: A clear, pushy description of when to use this agent.\n---\n\nYou do a job. Return a result.\n"
    rep = va.validate(_write(tmp_path, text))
    assert any("TOOL003" in w for w in rep.warnings)


def test_empty_body_errors(tmp_path):
    text = "---\nname: ok-agent\ndescription: A clear, pushy description of when to use this agent.\ntools: Read\n---\n"
    rep = va.validate(_write(tmp_path, text))
    assert any("BODY001" in e for e in rep.errors)


def test_aspirational_body_warns(tmp_path):
    rep = va.validate(
        _write(
            tmp_path,
            GOOD.replace(
                "You are a security reviewer.", "You should try to maybe review."
            ),
        )
    )
    assert any("BODY003" in w for w in rep.warnings)


def test_main_exit_code(tmp_path, capsys):
    bad = _write(tmp_path, "no frontmatter")
    rc = va.main([str(bad)])
    assert rc == 1
