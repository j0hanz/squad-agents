# Managed Agents Grounding

This file contains the foundational principles and reference links for Claude Managed Agents (beta: `managed-agents-2026-04-01`).

## Authoritative Sources

When necessary to clarify specific API schema details to the user, you may reference or present these external URLs:

- <https://platform.claude.com/docs/en/managed-agents/overview.md>
- <https://platform.claude.com/docs/en/managed-agents/quickstart.md>
- <https://platform.claude.com/docs/en/managed-agents/agent-setup.md>
- <https://platform.claude.com/docs/en/managed-agents/tools.md>
- <https://platform.claude.com/docs/en/managed-agents/permission-policies.md>
- <https://platform.claude.com/docs/en/managed-agents/onboarding.md>

## Additional resources

- Agent evaluation patterns and benchmarking: <https://raw.githubusercontent.com/davila7/claude-code-templates/refs/heads/main/cli-tool/components/skills/ai-research/agent-evaluation/SKILL.md>
- Agent architecture patterns (ReAct, Plan-and-Execute, Tool Registry): <https://raw.githubusercontent.com/davila7/claude-code-templates/refs/heads/main/cli-tool/components/skills/ai-research/ai-agents-architect/SKILL.md>

## Suggested CI integration

Run these gates in order, fail fast:

```bash
# Gate 1 -- basic markdown/frontmatter lint
./scripts/validate-agent.sh proposed.md

# Gate 2 -- safety/permission audit (--strict treats latest-pins as errors)
python scripts/audit.py --strict --json proposed.md

# Gate 3 -- block destructive updates (compare against production config)
python scripts/diff.py prod.md proposed.md --json
```

Exit codes: `0` = clean, `1` = warnings only, `2` = errors (CI fails).

## Core Constraints & Technical Details

1. **Beta Header:**
   The required beta header for these features is `managed-agents-2026-04-01`.

2. **Tool Configurations (`configs`):**
   The `configs` array provides per-tool overrides. This allows you to set a `default_config` (e.g., `enabled: true`, permission `always_ask`) and override specific tools that are known to be safe or explicitly unsafe.

3. **Permission Policies:**
   - **`always_ask`**: The default and safest policy for tool sets.
   - **`always_allow`**: Should ONLY be used for fully trusted, specific MCP servers. Applying this broadly to `agent_toolset` is a major security risk.

4. **Wholesale Replacement (Critical Pitfall):**
   When using the `agents.update` API, arrays such as `tools`, `skills`, and `mcp_servers` are replaced entirely. **You must always send the complete array.** Omitting items from the list during an update effectively deletes them from the agent configuration.

5. **Skill Versioning:**
   Always pin a `version` for custom skills in stable environments. Only use `latest` for active experimentation.
