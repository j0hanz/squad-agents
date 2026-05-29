# Skill Composition

## Why compose

The workspace has 21 sibling skills. An agent that reinvents `code-review` or `github-automation` work is technical debt from day one. Compose first; only build new where no sibling exists.

When designing an agent, start by checking what skills already exist. The agent-development skill integrates a recommendation engine to discover matching skills automatically. Use it before committing to a custom implementation.

## Discovery

To find candidate skills for your agent task, run:

    python scripts/recommend-skills.py path/to/agent.md

This outputs a ranked list of candidate skills with:

- Match score (0-100) based on keyword overlap with your agent's purpose
- Match reason (why the skill was recommended)
- Version(s) available
- Tool usage summary (what permissions it needs)

## Pinning rules

- **NEVER use `latest` in production.** Pin exact versions only (e.g., `v1.2.0`, not `latest` or `*`).
- Use `latest` only during active local experimentation and development.
- When you update a pinned skill, run `diff.py` against the prior configuration first to catch breaking changes.
- Pin one major version: If a skill exports major versions v1, v2, v3, pin one version and document migration paths if you need to upgrade.

## Audit-before-pin checklist

Before pinning a skill to your agent, perform these checks:

1. **Read SKILL.md frontmatter:** Review the candidate skill's description and any allowlist hints. Ensure its purpose aligns with your use case.

2. **Scan tool usage:** Use `rg` (ripgrep) to check the skill's scripts for tool calls you don't expect or don't permit:

```bash
rg "Bash|Edit|Write" skills/code-review/scripts/
```

If the skill calls tools your agent doesn't allow, you cannot use it safely.

1. **Verify tool intersection:** Ensure the skill's tool needs are a subset of your agent's allowlist. If the skill requires `Bash` but your agent only allows `Read` and `Grep`, it won't work.

2. **Check disable-model-invocation:** If the skill's frontmatter has `disable-model-invocation: true`, it won't auto-trigger from descriptions. You'll need explicit `Skill` tool calls to invoke it.

## Per-primitive composition syntax

### Managed Agent

In your agent's manifest (frontmatter + YAML), pin skills by name and version:

```yaml
skills:
  - name: "code-review"
    version: "1.2.0"
  - name: "github-automation"
    version: "2.1.0"
```

The platform merges these skills into the agent's behavior at invoke time.

### Claude Code Subagent

For subagents running in Claude Code sessions:

- **Ensure `Skill` is in `tools:` allowlist** — otherwise the agent cannot invoke skills programmatically.
- **Document expected skills** in the agent's description so users know what to install:

  ```markdown
  ## Skills this agent expects:

  - code-review (any v1.x)
  - github-automation (>=1.0)
  ```

- Users must have these skills installed in their Claude Code workspace before the agent can use them.

## Recommended sibling skills (quick reference)

Common skills available in this workspace:

- **code-review:** Automated code review and quality assessment
- **hook-development:** Hooks design and pattern guidance
- **diagrams:** Mermaid rendering and visualization
- **github-automation:** GitHub Actions workflows and CLI API integration
- **security-auditor:** Security vulnerability scanning
- **documentation-engineer:** Documentation generation and maintenance

For a complete list, run `ls skills/` or query `recommend-skills.py` with a task description.
