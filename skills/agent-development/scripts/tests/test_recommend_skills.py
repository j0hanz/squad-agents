import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "recommend-skills.py"
SAMPLE_AGENT = Path(__file__).parent / "fixtures" / "clean-cc-subagent.md"
SAMPLE_SKILLS = Path(__file__).parent / "fixtures" / "sample-skills"


def test_cli_runs_and_emits_json():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(SAMPLE_AGENT),
            "--skill-dirs",
            str(SAMPLE_SKILLS),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode in (0, 1)  # 0 = matches, 1 = no high-confidence
    parsed = json.loads(result.stdout)
    assert "candidates" in parsed
    assert "caveats" in parsed


def test_cli_returns_2_on_missing_agent():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "nonexistent.md",
            "--skill-dirs",
            str(SAMPLE_SKILLS),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
