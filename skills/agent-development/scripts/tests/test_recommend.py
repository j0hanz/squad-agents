import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))


def run_recommend(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "recommend.py")] + [str(a) for a in args],
        capture_output=True,
        text=True,
    )


class TestRecommend(unittest.TestCase):
    def test_exits_zero_always(self):
        r = run_recommend(FIXTURES / "clean-agent.md")
        self.assertEqual(r.returncode, 0)

    def test_json_output_has_required_keys(self):
        r = run_recommend(FIXTURES / "clean-agent.md", "--json")
        result = json.loads(r.stdout)
        for key in (
            "recommended_tier",
            "recommended_model",
            "score",
            "reasons",
            "current_model",
            "has_shell_tool",
        ):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_recommended_tier_is_valid(self):
        r = run_recommend(FIXTURES / "clean-agent.md", "--json")
        tier = json.loads(r.stdout)["recommended_tier"]
        self.assertIn(tier, ("haiku", "sonnet", "opus"))

    def test_shell_tool_not_haiku(self):
        r = run_recommend(FIXTURES / "shell-tool-agent.md", "--json")
        result = json.loads(r.stdout)
        self.assertNotEqual(result["recommended_tier"], "haiku")

    def test_shell_tool_flag_set(self):
        r = run_recommend(FIXTURES / "shell-tool-agent.md", "--json")
        result = json.loads(r.stdout)
        self.assertTrue(result["has_shell_tool"])

    def test_reasons_list_present(self):
        r = run_recommend(FIXTURES / "clean-agent.md", "--json")
        result = json.loads(r.stdout)
        self.assertIsInstance(result["reasons"], list)

    def test_drift_notice_when_model_differs(self):
        # shell-tool-agent.md uses haiku but recommendation should be sonnet
        r = run_recommend(FIXTURES / "shell-tool-agent.md", "--json")
        result = json.loads(r.stdout)
        self.assertIsNotNone(result.get("drift_notice"))

    def test_human_output_shows_recommendation(self):
        r = run_recommend(FIXTURES / "clean-agent.md")
        self.assertIn("Recommended", r.stdout)
        self.assertIn("Reasoning trail", r.stdout)

    def test_missing_file_exits_two(self):
        r = run_recommend("/nonexistent.md")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
