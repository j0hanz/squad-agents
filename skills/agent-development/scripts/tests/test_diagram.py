import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "diagram.py"
AGENT_FIXTURE = Path(__file__).parent / "fixtures" / "clean-cc-subagent.md"
HOOKS_FIXTURE = Path(__file__).parent / "fixtures" / "valid-hook-config.json"


def test_json_format_default():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(AGENT_FIXTURE), "--format", "json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "nodes" in data and "edges" in data
    node_ids = {n["id"] for n in data["nodes"]}
    assert "agent" in node_ids
    # The 3 tools (Read, Grep, Glob) should be nodes
    assert {"tool_Read", "tool_Grep", "tool_Glob"} <= node_ids


def test_mermaid_format():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(AGENT_FIXTURE), "--format", "mermaid"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "graph LR" in result.stdout
    assert "agent" in result.stdout


def test_includes_hook_bindings():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(AGENT_FIXTURE),
            "--include-hooks",
            str(HOOKS_FIXTURE),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    hook_edges = [e for e in data["edges"] if e.get("kind") == "hook"]
    assert hook_edges, "expected at least one hook edge"
