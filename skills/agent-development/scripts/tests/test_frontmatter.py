import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.frontmatter import parse_frontmatter


class TestParseFrontmatter(unittest.TestCase):
    def test_simple_string_values(self):
        content = '---\nname: "test-agent"\nmodel: claude-sonnet-4-6\n---\nbody text'
        fm, body = parse_frontmatter(content)
        self.assertEqual(fm["name"], "test-agent")
        self.assertEqual(fm["model"], "claude-sonnet-4-6")
        self.assertIn("body text", body)

    def test_quoted_values_stripped(self):
        content = "---\nname: \"my-agent\"\ncolor: '#AABBCC'\n---\n"
        fm, _ = parse_frontmatter(content)
        self.assertEqual(fm["name"], "my-agent")
        self.assertEqual(fm["color"], "#AABBCC")

    def test_list_of_dicts(self):
        content = "---\ntools:\n  - name: bash\n    permission: always_ask\n---\nbody"
        fm, _ = parse_frontmatter(content)
        self.assertEqual(len(fm["tools"]), 1)
        self.assertEqual(fm["tools"][0]["name"], "bash")
        self.assertEqual(fm["tools"][0]["permission"], "always_ask")

    def test_multiple_list_items(self):
        content = (
            "---\ntools:\n  - name: bash\n    permission: always_ask\n"
            "  - name: search\n    permission: always_allow\n---\n"
        )
        fm, _ = parse_frontmatter(content)
        self.assertEqual(len(fm["tools"]), 2)
        self.assertEqual(fm["tools"][1]["name"], "search")

    def test_no_frontmatter(self):
        content = "no frontmatter here"
        fm, body = parse_frontmatter(content)
        self.assertEqual(fm, {})
        self.assertEqual(body, content)

    def test_missing_close_delimiter(self):
        content = "---\nname: test\nbody without close"
        fm, body = parse_frontmatter(content)
        self.assertEqual(fm, {})

    def test_body_separated_correctly(self):
        content = "---\nname: x\n---\n\nSystem prompt here.\nSecond line."
        fm, body = parse_frontmatter(content)
        self.assertEqual(fm["name"], "x")
        self.assertIn("System prompt here.", body)

    def test_list_item_with_optional_field_absent(self):
        content = "---\nskills:\n  - name: my-skill\n---\n"
        fm, _ = parse_frontmatter(content)
        self.assertEqual(fm["skills"][0]["name"], "my-skill")
        self.assertNotIn("version", fm["skills"][0])


if __name__ == "__main__":
    unittest.main()
