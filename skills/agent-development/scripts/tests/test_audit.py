import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"


def run_audit(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "audit.py")] + [str(a) for a in args],
        capture_output=True,
        text=True,
    )


class TestAudit(unittest.TestCase):
    def test_clean_agent_exits_zero(self):
        r = run_audit(FIXTURES / "clean-agent.md")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_dangerous_exits_two(self):
        r = run_audit(FIXTURES / "dangerous-permissions.md")
        self.assertEqual(r.returncode, 2)

    def test_perm001_detected(self):
        r = run_audit(FIXTURES / "dangerous-permissions.md", "--json")
        codes = [f["code"] for f in json.loads(r.stdout)]
        self.assertIn("PERM001", codes)

    def test_perm002_detected(self):
        r = run_audit(FIXTURES / "dangerous-permissions.md", "--json")
        codes = [f["code"] for f in json.loads(r.stdout)]
        self.assertIn("PERM002", codes)

    def test_perm003_detected(self):
        r = run_audit(FIXTURES / "dangerous-permissions.md", "--json")
        codes = [f["code"] for f in json.loads(r.stdout)]
        self.assertIn("PERM003", codes)

    def test_pin001_warn_by_default(self):
        r = run_audit(FIXTURES / "unpinned-skill.md", "--json")
        findings = json.loads(r.stdout)
        pin001 = [f for f in findings if f["code"] == "PIN001"]
        self.assertTrue(pin001)
        self.assertEqual(pin001[0]["severity"], "warn")
        self.assertEqual(r.returncode, 1)

    def test_pin001_error_in_strict(self):
        r = run_audit(FIXTURES / "unpinned-skill.md", "--strict", "--json")
        findings = json.loads(r.stdout)
        pin001 = [f for f in findings if f["code"] == "PIN001"]
        self.assertTrue(pin001)
        self.assertEqual(pin001[0]["severity"], "error")
        self.assertEqual(r.returncode, 2)

    def test_pin002_detected(self):
        r = run_audit(FIXTURES / "unpinned-skill.md", "--json")
        codes = [f["code"] for f in json.loads(r.stdout)]
        self.assertIn("PIN002", codes)

    def test_weak_prompt_triggers_prompt_codes(self):
        r = run_audit(FIXTURES / "weak-prompt.md", "--json")
        codes = [f["code"] for f in json.loads(r.stdout)]
        self.assertIn("PROMPT001", codes)
        self.assertIn("DESC001", codes)
        self.assertIn("DESC002", codes)
        self.assertIn("BETA001", codes)

    def test_json_output_is_valid(self):
        r = run_audit(FIXTURES / "dangerous-permissions.md", "--json")
        findings = json.loads(r.stdout)
        self.assertIsInstance(findings, list)
        self.assertTrue(all("code" in f and "severity" in f for f in findings))

    def test_human_output_not_json(self):
        r = run_audit(FIXTURES / "clean-agent.md")
        self.assertRaises(json.JSONDecodeError, json.loads, r.stdout)

    def test_nonexistent_file_exits_two(self):
        r = run_audit("/nonexistent/agent.md")
        self.assertEqual(r.returncode, 2)

    def test_skill001_fires_on_release_mention(self):
        r = run_audit(FIXTURES / "managed-agent-needs-gh-cli.md", "--json")
        findings = json.loads(r.stdout)
        codes = [f["code"] for f in findings]
        self.assertIn("SKILL001", codes)

    def test_ccsa001_on_bad_tools_shape(self):
        r = run_audit(FIXTURES / "cc-subagent-bad-tools.md", "--json")
        findings = json.loads(r.stdout)
        codes = [f["code"] for f in findings]
        self.assertIn("CCSA001", codes)

    def test_ccsa002_on_undocumented_skills(self):
        r = run_audit(FIXTURES / "cc-subagent-skill-undocumented.md", "--json")
        findings = json.loads(r.stdout)
        codes = [f["code"] for f in findings]
        self.assertIn("CCSA002", codes)


if __name__ == "__main__":
    unittest.main()
