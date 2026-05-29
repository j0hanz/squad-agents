import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"


def run_cost(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "cost.py")] + [str(a) for a in args],
        capture_output=True,
        text=True,
    )


class TestCost(unittest.TestCase):
    def test_exits_zero(self):
        r = run_cost(FIXTURES / "clean-agent.md")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_json_output_has_required_keys(self):
        r = run_cost(FIXTURES / "clean-agent.md", "--json")
        result = json.loads(r.stdout)
        for key in (
            "model",
            "total_input_tokens",
            "cost_per_run_usd",
            "suite_cost_usd",
            "runs",
            "smells",
            "pricing_date",
        ):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_default_runs_is_three(self):
        r = run_cost(FIXTURES / "clean-agent.md", "--json")
        result = json.loads(r.stdout)
        self.assertEqual(result["runs"], 3)

    def test_custom_runs(self):
        r = run_cost(FIXTURES / "clean-agent.md", "--runs", "10", "--json")
        result = json.loads(r.stdout)
        self.assertEqual(result["runs"], 10)
        self.assertAlmostEqual(
            result["suite_cost_usd"], result["cost_per_run_usd"] * 10, places=6
        )

    def test_suite_cost_equals_n_times_per_run(self):
        r = run_cost(FIXTURES / "clean-agent.md", "--runs", "5", "--json")
        result = json.loads(r.stdout)
        self.assertAlmostEqual(
            result["suite_cost_usd"], result["cost_per_run_usd"] * 5, places=6
        )

    def test_skill_bodies_caveat_in_smells(self):
        r = run_cost(FIXTURES / "clean-agent.md", "--json")
        result = json.loads(r.stdout)
        self.assertTrue(any("skill" in s.lower() for s in result["smells"]))

    def test_human_output_shows_dollar(self):
        r = run_cost(FIXTURES / "clean-agent.md")
        self.assertIn("$", r.stdout)

    def test_fallback_model_not_triggered_for_known_model(self):
        r = run_cost(FIXTURES / "shell-tool-agent.md", "--json")
        result = json.loads(r.stdout)
        self.assertFalse(result["is_fallback_pricing"])

    def test_missing_file_exits_two(self):
        r = run_cost("/nonexistent.md")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
