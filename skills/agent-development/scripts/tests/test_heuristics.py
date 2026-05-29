import sys
import json
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.report import Finding, render_human, render_json, compute_exit_code
from lib.pricing import get_pricing, cost_usd, PRICING_DATE
from lib.heuristics import (
    estimate_tokens,
    estimate_input_tokens,
    score_complexity,
    score_to_tier,
    has_shell_tool,
    TOOL_SCHEMA_TOKENS,
)
from lib.agent_parser import AgentSpec, Tool


class TestFinding(unittest.TestCase):
    def test_finding_instantiation(self):
        f = Finding(severity="error", code="PERM001", message="test", path="/a.md")
        self.assertEqual(f.severity, "error")
        self.assertEqual(f.code, "PERM001")

    def test_render_json_valid(self):
        findings = [Finding("error", "PERM001", "bad permission", "/a.md")]
        output = render_json(findings)
        parsed = json.loads(output)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["code"], "PERM001")
        self.assertEqual(parsed[0]["severity"], "error")

    def test_render_json_empty(self):
        output = render_json([])
        self.assertEqual(json.loads(output), [])

    def test_render_human_no_findings(self):
        output = render_human([])
        self.assertIn("No findings", output)

    def test_render_human_shows_codes(self):
        findings = [
            Finding("error", "PERM001", "bad perm", "/a.md"),
            Finding("warn", "PIN001", "latest pin", "/a.md"),
        ]
        output = render_human(findings)
        self.assertIn("PERM001", output)
        self.assertIn("PIN001", output)

    def test_exit_code_error(self):
        findings = [Finding("error", "X", "msg", "/a.md")]
        self.assertEqual(compute_exit_code(findings), 2)

    def test_exit_code_warn_only(self):
        findings = [Finding("warn", "X", "msg", "/a.md")]
        self.assertEqual(compute_exit_code(findings), 1)

    def test_exit_code_info_only(self):
        findings = [Finding("info", "X", "msg", "/a.md")]
        self.assertEqual(compute_exit_code(findings), 0)

    def test_exit_code_clean(self):
        self.assertEqual(compute_exit_code([]), 0)

    def test_strict_promotes_warn_to_error(self):
        findings = [Finding("warn", "PIN001", "msg", "/a.md")]
        self.assertEqual(compute_exit_code(findings, strict=True), 2)

    def test_strict_does_not_affect_info(self):
        findings = [Finding("info", "X", "msg", "/a.md")]
        self.assertEqual(compute_exit_code(findings, strict=True), 0)


class TestPricing(unittest.TestCase):
    def test_known_model_returns_exact_rates(self):
        inp, out, fallback = get_pricing("claude-sonnet-4-6")
        self.assertEqual(inp, 3.00)
        self.assertEqual(out, 15.00)
        self.assertFalse(fallback)

    def test_haiku_rates(self):
        inp, out, fallback = get_pricing("claude-haiku-4-5-20251001")
        self.assertEqual(inp, 0.80)
        self.assertFalse(fallback)

    def test_opus_rates(self):
        inp, out, fallback = get_pricing("claude-opus-4-7")
        self.assertEqual(inp, 15.00)
        self.assertFalse(fallback)

    def test_unknown_model_uses_fallback(self):
        _, _, fallback = get_pricing("claude-unknown-999")
        self.assertTrue(fallback)

    def test_partial_match_sonnet(self):
        _, _, fallback = get_pricing("claude-sonnet-99-future")
        self.assertFalse(fallback)

    def test_cost_usd_calculation(self):
        cost, _ = cost_usd(1_000_000, 0, "claude-haiku-4-5-20251001")
        self.assertAlmostEqual(cost, 0.80, places=4)

    def test_pricing_date_present(self):
        self.assertRegex(PRICING_DATE, r"^\d{4}-\d{2}-\d{2}$")


def _make_spec(
    system_prompt="",
    description="",
    model="claude-sonnet-4-6",
    tools=None,
    skills=None,
    mcp_servers=None,
):
    return AgentSpec(
        path="test.md",
        name="test",
        description=description,
        model=model,
        color=None,
        tools=tools or [],
        skills=skills or [],
        mcp_servers=mcp_servers or [],
        system_prompt=system_prompt,
    )


class TestHeuristics(unittest.TestCase):
    def test_estimate_tokens_basic(self):
        self.assertEqual(estimate_tokens("hello"), 1)  # 5 chars // 4 = 1
        self.assertEqual(estimate_tokens("a" * 400), 100)

    def test_estimate_tokens_never_zero(self):
        self.assertEqual(estimate_tokens(""), 1)

    def test_estimate_input_tokens_includes_tools(self):
        spec = _make_spec(
            system_prompt="x" * 400,  # 100 tokens
            tools=[Tool("bash"), Tool("search")],
        )
        expected = 100 + 2 * TOOL_SCHEMA_TOKENS
        self.assertEqual(estimate_input_tokens(spec), expected)

    def test_score_complexity_many_tools(self):
        spec = _make_spec(tools=[Tool(f"t{i}") for i in range(6)])
        score, reasons = score_complexity(spec)
        self.assertGreater(score, 0)
        self.assertTrue(any("tools" in r for r in reasons))

    def test_score_complexity_low_tier_keywords(self):
        spec = _make_spec(system_prompt="classify extract dispatch route label")
        score, reasons = score_complexity(spec)
        self.assertLess(score, 0)

    def test_score_complexity_high_tier_keywords(self):
        spec = _make_spec(
            system_prompt="perform security audit and root cause analysis"
        )
        score, reasons = score_complexity(spec)
        self.assertGreater(score, 0)

    def test_score_to_tier_low_score(self):
        spec = _make_spec()
        self.assertEqual(score_to_tier(0, spec), "haiku")

    def test_score_to_tier_medium_score(self):
        spec = _make_spec(system_prompt="x" * 100, tools=[Tool("t1")])
        self.assertEqual(score_to_tier(3, spec), "sonnet")

    def test_score_to_tier_high_score(self):
        spec = _make_spec(system_prompt="x" * 100, tools=[Tool("t1")])
        self.assertEqual(score_to_tier(5, spec), "opus")

    def test_shell_tool_overrides_haiku(self):
        spec = _make_spec(tools=[Tool("bash", permission="always_ask")])
        self.assertEqual(score_to_tier(0, spec), "sonnet")

    def test_trivial_agent_override(self):
        spec = _make_spec(system_prompt="x" * 10)
        self.assertEqual(score_to_tier(3, spec), "haiku")

    def test_has_shell_tool_true(self):
        spec = _make_spec(tools=[Tool("bash")])
        self.assertTrue(has_shell_tool(spec))

    def test_has_shell_tool_false(self):
        spec = _make_spec(tools=[Tool("web-search")])
        self.assertFalse(has_shell_tool(spec))


if __name__ == "__main__":
    unittest.main()
