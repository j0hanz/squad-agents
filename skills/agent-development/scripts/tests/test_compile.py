import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"


def run_compile(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "compile.py")] + [str(a) for a in args],
        capture_output=True,
        text=True,
    )


class TestCompile(unittest.TestCase):
    def test_clean_agent_exits_zero(self):
        r = run_compile(FIXTURES / "clean-agent.md", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_outputs_valid_json(self):
        r = run_compile(FIXTURES / "clean-agent.md", "--json")
        payload = json.loads(r.stdout)
        self.assertIsInstance(payload, dict)

    def test_payload_has_required_fields(self):
        r = run_compile(FIXTURES / "clean-agent.md", "--json")
        payload = json.loads(r.stdout)
        self.assertEqual(payload["name"], "clean-example-agent")
        self.assertEqual(payload["model"], "claude-sonnet-4-6")
        self.assertEqual(payload["color"], "#4A90E2")

    def test_payload_tools_structure(self):
        r = run_compile(FIXTURES / "clean-agent.md", "--json")
        payload = json.loads(r.stdout)
        self.assertEqual(len(payload["tools"]), 1)
        self.assertEqual(payload["tools"][0]["name"], "web-search")
        self.assertEqual(payload["tools"][0]["permission"], "always_ask")

    def test_payload_skills_structure(self):
        r = run_compile(FIXTURES / "clean-agent.md", "--json")
        payload = json.loads(r.stdout)
        self.assertEqual(payload["skills"][0]["name"], "my-custom-skill")
        self.assertEqual(payload["skills"][0]["version"], "1.0.0")

    def test_system_prompt_included(self):
        r = run_compile(FIXTURES / "clean-agent.md", "--json")
        payload = json.loads(r.stdout)
        self.assertIn("system_prompt", payload)
        self.assertIn("You are the Documentation Assistant", payload["system_prompt"])

    def test_invalid_schema_exits_two(self):
        r = run_compile(FIXTURES / "invalid-schema.md", "--for", "create", "--json")
        self.assertEqual(r.returncode, 2)

    def test_invalid_schema_error_on_stderr(self):
        r = run_compile(FIXTURES / "invalid-schema.md", "--for", "create", "--json")
        self.assertIn("COMPILE_REQ", r.stderr)

    def test_human_mode_shows_preview(self):
        r = run_compile(FIXTURES / "clean-agent.md", "--for", "update")
        self.assertIn("wholesale", r.stdout.lower())

    def test_out_flag_writes_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            r = run_compile(FIXTURES / "clean-agent.md", "--out", tmp_path)
            self.assertEqual(r.returncode, 0)
            with open(tmp_path) as f:
                payload = json.load(f)
            self.assertEqual(payload["name"], "clean-example-agent")
        finally:
            os.unlink(tmp_path)

    def test_for_create_mode(self):
        r = run_compile(FIXTURES / "clean-agent.md", "--for", "create", "--json")
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout)
        self.assertIn("description", payload)

    def test_compile_cc_subagent(self):
        r = run_compile(FIXTURES / "clean-cc-subagent.md", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["kind"], "cc_subagent")
        self.assertEqual(payload["name"], "explore-codebase")
        self.assertIn("Read", payload["tools"])

    def test_compile_managed_still_works(self):
        r = run_compile(FIXTURES / "clean-agent.md", "--json")
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout)
        self.assertNotEqual(payload.get("kind"), "cc_subagent")
        self.assertEqual(payload["name"], "clean-example-agent")


if __name__ == "__main__":
    unittest.main()
