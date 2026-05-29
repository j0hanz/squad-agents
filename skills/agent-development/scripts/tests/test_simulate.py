import json
import subprocess
import sys
from pathlib import Path
import os
import pytest

SCRIPT = Path(__file__).parent.parent / "simulate.py"
AGENT_FIXTURE = Path(__file__).parent / "fixtures" / "clean-cc-subagent.md"


@pytest.fixture
def cases_yaml(tmp_path):
    p = tmp_path / "cases.yaml"
    p.write_text(
        "suite: test\n"
        f"agent: {AGENT_FIXTURE}\n"
        "runs: 1\n"
        "cases:\n"
        "  - name: smoke\n"
        "    prompt: 'find README.md'\n"
        "    expect:\n"
        "      must_not_call: ['Bash(*)']\n"
    )
    return p


def test_refuses_without_safety_flag(cases_yaml, tmp_path, monkeypatch):
    # Workspace is NOT ephemeral and NOT --worktree/--sandbox — must refuse.
    monkeypatch.delenv("CLAUDE_CODE_REMOTE", raising=False)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(AGENT_FIXTURE), str(cases_yaml), "--dry-run"],
        capture_output=True,
        text=True,
        cwd=str(Path.home()),  # non-tmpdir cwd
    )
    assert result.returncode == 2
    assert (
        "safety" in (result.stderr + result.stdout).lower()
        or "sandbox" in (result.stderr + result.stdout).lower()
        or "worktree" in (result.stderr + result.stdout).lower()
    )


def test_refuses_in_remote_environment(cases_yaml, tmp_path):
    env = os.environ.copy()
    env["CLAUDE_CODE_REMOTE"] = "true"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(AGENT_FIXTURE),
            str(cases_yaml),
            "--dry-run",
            "--sandbox",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 2
    assert "remote" in (result.stderr + result.stdout).lower()


def test_dry_run_emits_plan(cases_yaml, tmp_path):
    env = os.environ.copy()
    env.pop("CLAUDE_CODE_REMOTE", None)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(AGENT_FIXTURE),
            str(cases_yaml),
            "--dry-run",
            "--sandbox",
            "--report",
            "json",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert payload["suite"] == "test"
    assert payload["safety_checks_passed"] is True


def test_observer_script_written_to_simulate_dir(cases_yaml, tmp_path):
    env = os.environ.copy()
    env.pop("CLAUDE_CODE_REMOTE", None)
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(AGENT_FIXTURE),
            str(cases_yaml),
            "--dry-run",
            "--sandbox",
            "--simulate-dir",
            str(tmp_path / ".simulate"),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert (tmp_path / ".simulate" / "observer.py").exists()
    assert (tmp_path / ".simulate" / "hooks-config.json").exists()
