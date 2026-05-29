---
name: "example-agent-name"
description: "Use this agent when you need to [action]. It helps with [purpose]. <example>Can you do X?</example>"
model: "claude-sonnet-4-6"
color: "#4A90E2"
tools:
  - name: "bash"
    permission: "always_ask"
skills:
  # BEST PRACTICE: Run scripts/recommend-skills.py to discover matching sibling skills.
  # Always pin EXACT versions; never use `latest` in production.
  # Example: Run `python scripts/recommend-skills.py` to get ranked candidates.
  - name: "my-custom-skill"
    version: "1.0.0"
mcp_servers:
  - name: "trusted-database"
    permission: "always_allow"
---

# Agent Template

You are the [Role] Agent. Your primary goal is to [Goal].

## Core Directives

1. You must always [Action].
2. You must never [Restriction].

## Tools & Capabilities

When asked to perform [Task], use the [Tool Name] tool. Validate inputs carefully according to the tool schema.

## Error Handling

If you encounter a timeout or permission denial, you must explain the issue to the user and suggest an alternative approach. Do not fail silently.
