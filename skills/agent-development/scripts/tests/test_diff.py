import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"


def run_diff(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "diff.py")] + [str(a) for a in args],
        capture_output=True,
        text=True,
    )


class TestDiff(unittest.TestCase):
    def test_identical_files_exits_zero(self):
        r = run_diff(FIXTURES / "prod.md", FIXTURES / "prod.md")
        self.assertEqual(r.returncode, 0)

    def test_destructive_exits_two(self):
        r = run_diff(FIXTURES / "prod.md", FIXTURES / "proposed-destructive.md")
        self.assertEqual(r.returncode, 2)

    def test_safe_update_exits_zero(self):
        r = run_diff(FIXTURES / "prod.md", FIXTURES / "proposed-safe.md")
        self.assertEqual(r.returncode, 0)

    def test_deletion_finding_present(self):
        r = run_diff(
            FIXTURES / "prod.md", FIXTURES / "proposed-destructive.md", "--json"
        )
        findings = json.loads(r.stdout)
        del_codes = [f["code"] for f in findings if "DEL" in f["code"]]
        self.assertTrue(del_codes, "Expected at least one deletion finding")

    def test_tool_deletion_detected(self):
        r = run_diff(
            FIXTURES / "prod.md", FIXTURES / "proposed-destructive.md", "--json"
        )
        findings = json.loads(r.stdout)
        self.assertTrue(
            any(
                f["code"] == "DIFF_DEL_TOOL" and "file-writer" in f["message"]
                for f in findings
            )
        )

    def test_skill_deletion_detected(self):
        r = run_diff(
            FIXTURES / "prod.md", FIXTURES / "proposed-destructive.md", "--json"
        )
        findings = json.loads(r.stdout)
        self.assertTrue(any(f["code"] == "DIFF_DEL_SKILL" for f in findings))

    def test_permission_downgrade_detected(self):
        r = run_diff(
            FIXTURES / "prod.md", FIXTURES / "proposed-destructive.md", "--json"
        )
        findings = json.loads(r.stdout)
        self.assertTrue(any(f["code"] == "DIFF_PERM_DOWNGRADE" for f in findings))

    def test_addition_info_finding(self):
        r = run_diff(FIXTURES / "prod.md", FIXTURES / "proposed-safe.md", "--json")
        findings = json.loads(r.stdout)
        self.assertTrue(
            any(
                f["code"] == "DIFF_ADD_TOOL" and "chart-generator" in f["message"]
                for f in findings
            )
        )

    def test_version_bump_info_finding(self):
        r = run_diff(FIXTURES / "prod.md", FIXTURES / "proposed-safe.md", "--json")
        findings = json.loads(r.stdout)
        self.assertTrue(any(f["code"] == "DIFF_VERSION_BUMP" for f in findings))

    def test_json_output_valid(self):
        r = run_diff(
            FIXTURES / "prod.md", FIXTURES / "proposed-destructive.md", "--json"
        )
        self.assertIsInstance(json.loads(r.stdout), list)

    def test_missing_file_exits_two(self):
        r = run_diff("/nonexistent.md", FIXTURES / "prod.md")
        self.assertEqual(r.returncode, 2)

    def test_diff_directory_mode_detects_hook_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            left = tmp_path / "left"
            right = tmp_path / "right"
            (left / "hooks").mkdir(parents=True)
            right.mkdir()
            (left / "hooks" / "hooks.json").write_text('{"hooks":{}}', encoding="utf-8")
            r = run_diff(left, right, "--json")
            self.assertEqual(r.returncode, 2)
            deltas = json.loads(r.stdout)
            self.assertEqual(deltas["hooks"]["status"], "removed")

    def test_diff_file_mode_unchanged(self):
        r = run_diff(FIXTURES / "prod.md", FIXTURES / "prod.md", "--json")
        self.assertEqual(r.returncode, 0)
        findings = json.loads(r.stdout)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
