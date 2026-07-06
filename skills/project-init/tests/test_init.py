"""Tests for the project-init engine. Run: python -m pytest skills/project-init/tests"""

from __future__ import annotations

import json
from pathlib import Path

import init
import pytest


def _claim(key, value, path, match=None, confidence=0.5):
    ev = {"path": path}
    if match is not None:
        ev["match"] = match
    return {"key": key, "value": value, "evidence": ev, "confidence": confidence}


def test_pnpm_vs_npm_resolves_to_lockfile_winner(tmp_path: Path):
    """Conflicting claims: the one citing the lockfile (tier 4) beats the README (tier 1)."""
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
    (tmp_path / "README.md").write_text("run npm install to set up\n")
    claims = [
        _claim("pm", "npm", "README.md", match="npm", confidence=0.9),
        _claim("pm", "pnpm", "pnpm-lock.yaml", match="lockfileVersion", confidence=0.5),
    ]
    winners, _ = init.merge_claims(claims, tmp_path)
    assert winners["pm"].value == "pnpm"


def test_no_match_command_claim_is_dropped(tmp_path: Path):
    """A command/version key without an evidence match never auto-passes."""
    (tmp_path / "package.json").write_text('{"name": "x"}\n')
    claim, reason = init.verify_claim(
        _claim("cmd.build", "make all", "package.json"), tmp_path
    )
    assert claim is None
    assert "requires a literal evidence match" in reason


def test_out_of_repo_and_symlink_evidence_rejected(tmp_path: Path):
    """Containment guard: a path escaping the repo root is rejected even via symlink."""
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("npm\n")
    repo = tmp_path / "repo"
    repo.mkdir()
    # Direct traversal.
    claim, reason = init.verify_claim(
        _claim("pm", "npm", "../secret.txt", match="npm"), repo
    )
    assert claim is None and "escapes repo root" in reason
    # Via an in-repo symlink pointing outside (skip if the FS can't symlink).
    link = repo / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this filesystem")
    claim, reason = init.verify_claim(
        _claim("pm", "npm", "link.txt", match="npm"), repo
    )
    assert claim is None and "escapes repo root" in reason


def test_generated_file_uses_lf_newlines(tmp_path: Path, monkeypatch):
    """Byte-level: AGENTS.md is written with \\n, never \\r\\n (Windows regression guard)."""
    (tmp_path / "package.json").write_text('{"packageManager": "pnpm@9"}\n')
    claims_file = tmp_path / "claims.json"
    claims_file.write_text(
        json.dumps(
            [
                _claim("pm", "pnpm", "package.json", match="pnpm"),
                _claim("cmd.build", "pnpm build", "package.json", match="pnpm"),
                _claim("cmd.test", "pnpm test", "package.json", match="pnpm"),
            ]
        )
    )
    monkeypatch.chdir(tmp_path)
    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            str(claims_file),
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
            "--purpose",
            "test repo",
            "--out",
            "AGENTS.md",
        ]
    )
    assert init._cmd_generate(args) == 0
    raw = (tmp_path / "AGENTS.md").read_bytes()
    assert b"\r\n" not in raw
    assert b"project-init:hard-rules v1" in raw


def test_value_sanitization_blocks_kv_injection():
    """A match value carrying a newline can't forge a second kv line."""
    assert "\n" not in init._sanitize_value("pnpm\nmalicious: value")


def test_out_of_vocab_key_dropped(tmp_path: Path):
    (tmp_path / "x.txt").write_text("hi\n")
    claim, reason = init.verify_claim(_claim("random_key", "v", "x.txt"), tmp_path)
    assert claim is None and "out-of-vocab" in reason


def test_lint_catches_missing_marker_and_todo():
    bad = "# Agent Instructions\n\npurpose: x\n\n## Hard Rules\n\nTODO fix\n"
    fails = init.lint_agents_md(bad)
    assert any("marker" in f for f in fails)
    assert any("TODO" in f for f in fails)


def test_linter_passes_package_scoped_agents_md():
    """Linter passes a valid package-scoped AGENTS.md and fails if the marker is missing or malformed."""
    valid_pkg = "# Agent Instructions: packages/api\n\npurpose: api subproject\n\n<!-- project-init:package-scoped packages/api -->\n"
    fails = init.lint_agents_md(valid_pkg)
    assert not fails

    missing_marker = "# Agent Instructions: packages/api\n\npurpose: api subproject\n"
    fails = init.lint_agents_md(missing_marker)
    assert any("marker" in f for f in fails)

    malformed_marker = "# Agent Instructions: packages/api\n\npurpose: api subproject\n\n<!-- project-init:package-scoped -->\n"
    fails = init.lint_agents_md(malformed_marker)
    assert "missing/malformed project-init:package-scoped marker" in fails


def test_cmd_alias_normalizes_to_canonical_key(tmp_path: Path):
    """`cmd.tests` and `cmd.test` collapse to one canonical key, not two."""
    assert init.normalize_key("cmd.tests") == "cmd.test"
    assert init.normalize_key("cmd.tsc") == "cmd.typecheck"
    assert init.normalize_key("file.fmt") == "file.format"
    (tmp_path / "package.json").write_text('{"scripts":{"test":"vitest"}}\n')
    winners, _ = init.merge_claims(
        [
            _claim("cmd.tests", "vitest", "package.json", match="test", confidence=0.5),
            _claim(
                "cmd.test", "vitest run", "package.json", match="test", confidence=0.9
            ),
        ],
        tmp_path,
    )
    assert list(winners) == ["cmd.test"]
    assert winners["cmd.test"].value == "vitest run"


def test_unknown_command_bucket_dropped(tmp_path: Path):
    """An out-of-set command suffix (no canonical bucket) is dropped, not bloated in."""
    assert init.normalize_key("cmd.deploy") is None
    (tmp_path / "Makefile").write_text("deploy:\n\tkubectl apply\n")
    claim, reason = init.verify_claim(
        _claim("cmd.deploy", "make deploy", "Makefile", match="deploy"), tmp_path
    )
    assert claim is None and "out-of-vocab" in reason


def test_conv_bucket_is_capped(tmp_path: Path):
    """conv.* is open-suffix but capped so it can't blow the budget."""
    (tmp_path / "x.txt").write_text("y\n")
    claims = [
        _claim(f"conv.c{i}", f"rule {i}", "x.txt", confidence=i / 10) for i in range(10)
    ]
    winners, dropped = init.merge_claims(claims, tmp_path)
    assert sum(1 for k in winners if k.startswith("conv.")) == init.CAPS["conv."]
    assert any("cap of" in d for d in dropped)


def test_stack_key_renders_after_purpose(tmp_path: Path):
    (tmp_path / "go.mod").write_text("module x\ngo 1.22\n")
    winners, _ = init.merge_claims(
        [_claim("stack", "Go 1.22", "go.mod", match="go 1.22")], tmp_path
    )
    out = init.render_agents_md(
        winners, "minimal", "development", "always", "local-only"
    )
    assert "- Go 1.22" in out
    assert out.index("## Project") < out.index("- Go 1.22") < out.index("## Hard Rules")


def test_prescan_skips_vendor_and_counts_packages(tmp_path: Path):
    (tmp_path / "package.json").write_text("{}\n")
    (tmp_path / "pkg-a").mkdir()
    (tmp_path / "pkg-a" / "package.json").write_text("{}\n")
    nm = tmp_path / "node_modules" / "dep"
    nm.mkdir(parents=True)
    (nm / "package.json").write_text("{}\n")  # must NOT be counted
    result = init.prescan(tmp_path)
    assert "node_modules/dep" not in result["packages"]
    assert result["package_count"] == 2  # root + pkg-a


def test_claims_filtering_by_package_prefix(tmp_path: Path):
    """Claims are filtered to only keep those matching the specified package prefix."""
    (tmp_path / "packages").mkdir()
    (tmp_path / "packages" / "api").mkdir()
    (tmp_path / "packages" / "frontend").mkdir()
    (tmp_path / "packages" / "api" / "package.json").write_text('{"name": "api"}\n')
    (tmp_path / "packages" / "frontend" / "package.json").write_text(
        '{"name": "frontend"}\n'
    )
    (tmp_path / "README.md").write_text("root readme\n")

    claims = [
        _claim("pm", "pnpm", "packages/api/package.json", match="api", confidence=0.9),
        _claim(
            "cmd.build",
            "pnpm build",
            "packages/api/package.json",
            match="api",
            confidence=0.9,
        ),
        _claim(
            "cmd.test",
            "vitest",
            "packages/frontend/package.json",
            match="frontend",
            confidence=0.8,
        ),
        _claim("conv.git", "ESM only", "README.md", confidence=0.5),
    ]

    # Run merge_claims as normal
    winners, _ = init.merge_claims(claims, tmp_path)

    # Simulate filtering logic
    package_path = "packages/api"
    prefix = package_path.strip().replace("\\", "/").rstrip("/") + "/"
    filtered = {
        k: v
        for k, v in winners.items()
        if v.evidence.path.replace("\\", "/").startswith(prefix)
    }

    assert "pm" in filtered
    assert "cmd.build" in filtered
    assert "cmd.test" not in filtered
    assert "conv.git" not in filtered


def test_cli_package_filtering(tmp_path: Path, monkeypatch):
    """CLI option --package correctly filters generated AGENTS.md content to the package directory prefix."""
    (tmp_path / "packages").mkdir()
    (tmp_path / "packages" / "api").mkdir()
    (tmp_path / "packages" / "api" / "package.json").write_text('{"name": "api"}\n')
    (tmp_path / "README.md").write_text("root readme\n")

    claims_file = tmp_path / "claims.json"
    claims_file.write_text(
        json.dumps(
            [
                _claim(
                    "pm",
                    "pnpm",
                    "packages/api/package.json",
                    match="api",
                    confidence=0.9,
                ),
                _claim(
                    "cmd.build",
                    "pnpm build",
                    "packages/api/package.json",
                    match="api",
                    confidence=0.9,
                ),
                _claim(
                    "cmd.test", "vitest", "README.md", match="readme", confidence=0.8
                ),
            ]
        )
    )
    monkeypatch.chdir(tmp_path)
    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            str(claims_file),
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
            "--purpose",
            "test repo",
            "--package",
            "packages/api",
            "--out",
            "AGENTS.md",
        ]
    )
    assert init._cmd_generate(args) == 0
    raw = (tmp_path / "AGENTS.md").read_text()
    assert "- pnpm" in raw
    assert "- `pnpm build`" in raw
    assert "vitest" not in raw


def test_render_package_scoped_agents_md(tmp_path: Path):
    """Rendering with package parameter excludes hard rules and adds package-scoped header."""
    winners = {
        "purpose": init.Claim("purpose", "test pkg purpose", 4, 1.0),
        "stack": init.Claim("stack", "Go 1.22", 4, 1.0),
    }
    out = init.render_agents_md(
        winners,
        "minimal",
        "development",
        "always",
        "local-only",
        package="packages/api",
    )

    assert "# Agent Instructions: packages/api" in out
    assert "- test pkg purpose" in out
    assert "- Go 1.22" in out
    assert "## Hard Rules" not in out
    assert "project-init:hard-rules" not in out
    assert "project-init:package-scoped packages/api" in out


def test_verify_claim_path_handling(tmp_path: Path):
    """Verify that verify_claim returns relative, POSIX-style paths relative to root."""
    (tmp_path / "packages").mkdir()
    (tmp_path / "packages" / "api").mkdir()
    (tmp_path / "packages" / "api" / "package.json").write_text('{"name": "api"}\n')

    # Test with backslashes on Windows / normal relative path
    claim, reason = init.verify_claim(
        _claim("pm", "npm", "packages\\api\\package.json", match="api"), tmp_path
    )
    assert claim is not None
    assert claim.evidence.path == "packages/api/package.json"

    # Test with absolute path (that stays within repo root)
    abs_path = (tmp_path / "packages" / "api" / "package.json").resolve()
    claim, reason = init.verify_claim(
        _claim("pm", "npm", str(abs_path), match="api"), tmp_path
    )
    assert claim is not None
    assert claim.evidence.path == "packages/api/package.json"


def test_skip_value_omits_hard_rule_line_not_ci(tmp_path: Path):
    """`skip` drops the line from AGENTS.md and its marker; ci is never skippable."""
    out = init.render_agents_md({}, "skip", "skip", "skip", "github-actions")
    assert "- Automated CI runs on GitHub Actions" in out
    assert "commit=skip maturity=skip testing=skip ci=github-actions" in out
    assert "## Hard Rules" in out  # ci line keeps the section non-empty
    hard_rules_body = out.split("## Hard Rules", 1)[1].split("<!--", 1)[0]
    assert (
        hard_rules_body.count("- ") == 1
    )  # only the CI bullet remains, commit/maturity/testing all skipped


def test_skip_sections_filters_winners_and_records_marker(tmp_path: Path, monkeypatch):
    """--skip-sections removes the matching keys and is recorded in the marker
    for re-survey reuse, even though the rest of the section logic is untouched."""
    (tmp_path / "package.json").write_text('{"packageManager": "pnpm@9"}\n')
    claims_file = tmp_path / "claims.json"
    claims_file.write_text(
        json.dumps(
            [
                _claim("pm", "pnpm", "package.json", match="pnpm"),
                _claim("cmd.build", "pnpm build", "package.json", match="pnpm"),
                _claim("cmd.test", "pnpm test", "package.json", match="pnpm"),
                _claim("conv.imports", "ESM only", "package.json", match="pnpm"),
                _claim(
                    "dep.node_modules", "node_modules/", "package.json", match="pnpm"
                ),
            ]
        )
    )
    monkeypatch.chdir(tmp_path)
    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            str(claims_file),
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
            "--purpose",
            "test repo",
            "--skip-sections",
            "conventions,dependencies",
            "--out",
            "AGENTS.md",
        ]
    )
    assert init._cmd_generate(args) == 0
    raw = (tmp_path / "AGENTS.md").read_text()
    assert "## Key Conventions" not in raw
    assert "## Dependency Locations" not in raw
    assert "- pnpm" in raw  # untouched section still renders
    assert "sections=conventions,dependencies" in raw


def test_skip_sections_rejects_unknown_name(tmp_path: Path, monkeypatch, capsys):
    claims_file = tmp_path / "claims.json"
    claims_file.write_text("[]\n")
    monkeypatch.chdir(tmp_path)
    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            str(claims_file),
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
            "--purpose",
            "test repo",
            "--skip-sections",
            "bogus",
        ]
    )
    assert init._cmd_generate(args) == 1
    assert "unknown name(s): bogus" in capsys.readouterr().err


def test_bullet_lines_backtick_keeps_trailing_parenthetical_outside():
    """A value like 'npm run check (...)' backticks only the command, not the explanation."""
    out = init._bullet_lines(
        ["npm run check (build + type-check + eslint + prettier + knip + test)"],
        backtick=True,
    )
    assert out == [
        "- `npm run check` (build + type-check + eslint + prettier + knip + test)"
    ]


def test_bullet_lines_backtick_without_parenthetical():
    assert init._bullet_lines(["npm install"], backtick=True) == ["- `npm install`"]


def test_bullet_lines_split_explodes_conv_fact_separator():
    """conv.* values pack atomic facts with ' || '; each becomes its own bullet, untouched."""
    out = init._bullet_lines(
        ["Throw `FsError` carrying a `Problem` || Never throw raw `Error`"],
        split=True,
    )
    assert out == [
        "- Throw `FsError` carrying a `Problem`",
        "- Never throw raw `Error`",
    ]


def test_render_key_conventions_explodes_packed_value(tmp_path: Path):
    """End-to-end: a single conv.* claim with a packed value renders as multiple bullets."""
    (tmp_path / "x.txt").write_text("y\n")
    winners, _ = init.merge_claims(
        [
            _claim(
                "conv.errors",
                "Throw `FsError` carrying a `Problem` || Never throw raw `Error`",
                "x.txt",
            )
        ],
        tmp_path,
    )
    out = init.render_agents_md(winners, "skip", "skip", "skip", "local-only")
    assert "- Throw `FsError` carrying a `Problem`" in out
    assert "- Never throw raw `Error`" in out


def test_render_package_manager_splits_pm_and_common_commands(tmp_path: Path):
    """pm renders as its own bullet; cmd.* nests under a nested Common Commands subsection."""
    (tmp_path / "package.json").write_text('{"scripts":{"build":"tsc"}}\n')
    winners, _ = init.merge_claims(
        [
            _claim("pm", "npm", "package.json", match="scripts"),
            _claim("cmd.build", "npm run build", "package.json", match="scripts"),
        ],
        tmp_path,
    )
    out = init.render_agents_md(winners, "skip", "skip", "skip", "local-only")
    assert "- npm" in out
    assert "### Common Commands" in out
    assert "- `npm run build`" in out
    assert out.index("## Package Manager") < out.index("### Common Commands")


def test_marker_regex_accepts_old_files_without_sections_field():
    """Backward-compat: AGENTS.md written before the sections= field existed
    must still lint clean, or every pre-existing repo would break on re-lint."""
    old_style = (
        "# Agent Instructions\n\npurpose: x\n\n## Hard Rules\n\n"
        "commit: free-form\nmaturity: dev\ntesting: always\nci: local\n\n"
        "<!-- project-init:hard-rules v1 commit=minimal maturity=development "
        "testing=always ci=local-only -->\n"
    )
    assert init.lint_agents_md(old_style) == []


def test_cli_package_validation(tmp_path: Path, monkeypatch, capsys):
    """CLI option --package must exist and stay within the repo root."""
    claims_file = tmp_path / "claims.json"
    claims_file.write_text("[]\n")
    monkeypatch.chdir(tmp_path)

    # 1. Non-existent directory
    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            str(claims_file),
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
            "--purpose",
            "test repo",
            "--package",
            "nonexistent-dir",
        ]
    )
    assert init._cmd_generate(args) == 1
    captured = capsys.readouterr()
    assert "FAIL: --package path does not exist or escapes repo root" in captured.err

    # 2. Path escaping repo root (using '..')
    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            str(claims_file),
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
            "--purpose",
            "test repo",
            "--package",
            "../escaped",
        ]
    )
    assert init._cmd_generate(args) == 1
    captured = capsys.readouterr()
    assert "FAIL: --package path does not exist or escapes repo root" in captured.err

    # 3. Valid directory inside repo
    (tmp_path / "valid-pkg").mkdir()
    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            str(claims_file),
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
            "--purpose",
            "test repo",
            "--package",
            "valid-pkg",
        ]
    )
    assert init._cmd_generate(args) == 0


def test_cli_generate_invalid_claims(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    # 1. Missing claims file
    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            "missing_claims.json",
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
        ]
    )
    assert init._cmd_generate(args) == 1
    assert "FAIL: could not load claims" in capsys.readouterr().err

    # 2. Invalid JSON content
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("invalid json")
    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            str(bad_json),
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
        ]
    )
    assert init._cmd_generate(args) == 1
    assert "FAIL: could not load claims" in capsys.readouterr().err

    # 3. JSON is not an array
    dict_json = tmp_path / "dict.json"
    dict_json.write_text('{"key": "value"}')
    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            str(dict_json),
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
        ]
    )
    assert init._cmd_generate(args) == 1
    assert "claims file must be a JSON array" in capsys.readouterr().err


def test_cli_wire_subcommand(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "AGENTS.md"
    source.write_text("# Agent Instructions\n")
    target = tmp_path / "CLAUDE.md"

    args = init._build_parser().parse_args(["wire", str(source), str(target)])
    assert init._cmd_wire(args) == 0
    assert target.read_text() == "# See [AGENTS.md](AGENTS.md)\n"


def test_cli_lint_subcommand(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    # 1. Valid AGENTS.md
    valid_content = (
        "# Agent Instructions\n\npurpose: test\n\n## Hard Rules\n\n"
        "commit: minimal\nmaturity: development\ntesting: always\nci: local-only\n\n"
        "<!-- project-init:hard-rules v1 commit=minimal maturity=development testing=always ci=local-only -->\n"
    )
    agents_file = tmp_path / "AGENTS.md"
    agents_file.write_text(valid_content)

    args = init._build_parser().parse_args(["lint", str(agents_file)])
    assert init._cmd_lint(args) == 0
    assert "PASS: AGENTS.md is valid" in capsys.readouterr().out

    # 2. Invalid AGENTS.md
    invalid_file = tmp_path / "INVALID.md"
    invalid_file.write_text("bad text")
    args = init._build_parser().parse_args(["lint", str(invalid_file)])
    assert init._cmd_lint(args) == 1
    assert "FAIL" in capsys.readouterr().err


def test_cli_prescan_subcommand(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "package.json").write_text("{}\n")

    args = init._build_parser().parse_args(["prescan", str(tmp_path)])
    assert init._cmd_prescan(args) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["packages"] == ["."]
    assert out["has_manifest"] is True


def test_skip_sections_whitespace_and_commas(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    claims_file = tmp_path / "claims.json"
    claims_file.write_text("[]\n")

    args = init._build_parser().parse_args(
        [
            "generate",
            "--claims",
            str(claims_file),
            "--commit",
            "minimal",
            "--maturity",
            "development",
            "--testing",
            "always",
            "--ci",
            "local-only",
            "--skip-sections",
            " conventions , , dependencies ",
        ]
    )
    assert init._cmd_generate(args) == 0


def test_budget_trimming_mismatch_logic(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(init, "MAX_LINES", 28)

    # We construct a set of winners that is just large enough to exceed 28 lines with dummy rules,
    # but stays under 28 lines when all hard rules are skipped.
    winners = {
        "purpose": init.Claim("purpose", "A repo to test budget trimming", 4, 1.0),
        "pm": init.Claim("pm", "npm", 4, 1.0),
        "cmd.build": init.Claim("cmd.build", "npm run build", 4, 1.0),
        "cmd.test": init.Claim("cmd.test", "npm test", 4, 1.0),
        "conv.rule1": init.Claim("conv.rule1", "Convention 1", 4, 1.0),
        "conv.rule2": init.Claim("conv.rule2", "Convention 2", 4, 1.0),
        "conv.rule3": init.Claim("conv.rule3", "Convention 3", 4, 1.0),
    }

    # If we trim to budget using actual "skip" options, it shouldn't drop any rules.
    trimmed_winners_no_skip, dropped_no_skip = init._trim_to_budget(
        winners,
        commit="minimal",
        maturity="development",
        testing="not-enforced",
        ci="local-only",
    )

    trimmed_winners_skip, dropped_skip = init._trim_to_budget(
        winners, commit="skip", maturity="skip", testing="skip", ci="local-only"
    )

    # In the no-skip (dummy values) run, at least one convention is dropped to fit.
    assert len(dropped_no_skip) > 0
    # In the skip run (shorter document), the document already fits, so nothing is dropped!
    assert len(dropped_skip) == 0


def test_evidence_tier_custom():
    """Verify correct evidence tier classification for go.mod, go.sum, and Makefile."""
    # go.mod is manifest / config -> Tier 3
    assert init.evidence_tier("go.mod") == 3
    assert init.evidence_tier("path/to/go.mod") == 3

    # go.sum is lockfile -> Tier 4
    assert init.evidence_tier("go.sum") == 4

    # Makefile is other source file -> Tier 2
    assert init.evidence_tier("Makefile") == 2
    assert init.evidence_tier("makefile") == 2

    # package-lock.json is lockfile -> Tier 4
    assert init.evidence_tier("package-lock.json") == 4

    # package.json is config/manifest -> Tier 3
    assert init.evidence_tier("package.json") == 3

    # README.md is prose/docs -> Tier 1
    assert init.evidence_tier("README.md") == 1

