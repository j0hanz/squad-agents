import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.agent_parser import (
    parse_agent,
    AgentSpec,
    Tool,
    SkillPin,
    McpServer,
    detect_agent_kind,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseAgent(unittest.TestCase):
    def test_returns_agentspec(self):
        spec = parse_agent(str(FIXTURES / "clean-agent.md"))
        self.assertIsInstance(spec, AgentSpec)

    def test_parses_scalar_fields(self):
        spec = parse_agent(str(FIXTURES / "clean-agent.md"))
        self.assertEqual(spec.name, "clean-example-agent")
        self.assertEqual(spec.model, "claude-sonnet-4-6")
        self.assertEqual(spec.color, "#4A90E2")

    def test_parses_tools(self):
        spec = parse_agent(str(FIXTURES / "clean-agent.md"))
        self.assertEqual(len(spec.tools), 1)
        self.assertIsInstance(spec.tools[0], Tool)
        self.assertEqual(spec.tools[0].name, "web-search")
        self.assertEqual(spec.tools[0].permission, "always_ask")

    def test_parses_skills(self):
        spec = parse_agent(str(FIXTURES / "clean-agent.md"))
        self.assertEqual(len(spec.skills), 1)
        self.assertIsInstance(spec.skills[0], SkillPin)
        self.assertEqual(spec.skills[0].name, "my-custom-skill")
        self.assertEqual(spec.skills[0].version, "1.0.0")

    def test_parses_mcp_servers(self):
        spec = parse_agent(str(FIXTURES / "clean-agent.md"))
        self.assertEqual(len(spec.mcp_servers), 1)
        self.assertIsInstance(spec.mcp_servers[0], McpServer)
        self.assertEqual(spec.mcp_servers[0].name, "trusted-database")
        self.assertEqual(spec.mcp_servers[0].permission, "always_ask")

    def test_system_prompt_extracted(self):
        spec = parse_agent(str(FIXTURES / "clean-agent.md"))
        self.assertIn("You are the Documentation Assistant", spec.system_prompt)

    def test_missing_optional_tool_permission(self):
        spec = parse_agent(str(FIXTURES / "dangerous-permissions.md"))
        mcp = spec.mcp_servers[0]
        self.assertIsNone(mcp.permission)

    def test_missing_skill_version(self):
        spec = parse_agent(str(FIXTURES / "unpinned-skill.md"))
        formatter = next(s for s in spec.skills if s.name == "formatter")
        self.assertIsNone(formatter.version)

    def test_no_tools_returns_empty_list(self):
        spec = parse_agent(str(FIXTURES / "weak-prompt.md"))
        self.assertEqual(spec.tools, [])
        self.assertEqual(spec.skills, [])
        self.assertEqual(spec.mcp_servers, [])

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            parse_agent("/nonexistent/agent.md")

    def test_raw_frontmatter_stored(self):
        spec = parse_agent(str(FIXTURES / "invalid-schema.md"))
        self.assertIn("unknown_field", spec.raw_frontmatter)

    def test_path_stored_on_spec(self):
        path = str(FIXTURES / "clean-agent.md")
        spec = parse_agent(path)
        self.assertEqual(spec.path, path)


class TestDetectAgentKind(unittest.TestCase):
    def test_detect_managed_by_mcp_servers(self):
        assert (
            detect_agent_kind(
                {"mcp_servers": [{"name": "x", "permission": "always_ask"}]}
            )
            == "managed"
        )

    def test_detect_managed_by_color(self):
        assert detect_agent_kind({"color": "#4A90E2", "tools": []}) == "managed"

    def test_detect_managed_by_skills_with_version(self):
        assert (
            detect_agent_kind({"skills": [{"name": "x", "version": "1.0.0"}]})
            == "managed"
        )

    def test_detect_cc_subagent_flat_tools(self):
        assert (
            detect_agent_kind({"tools": ["Read", "Grep"], "model": "claude-sonnet-4-6"})
            == "cc_subagent"
        )

    def test_detect_unknown_when_ambiguous(self):
        assert detect_agent_kind({"description": "x"}) == "unknown"


if __name__ == "__main__":
    unittest.main()
