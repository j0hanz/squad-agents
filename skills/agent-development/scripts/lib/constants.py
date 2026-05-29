"""
Centralized constants for agent-development scripts.
"""

from __future__ import annotations

# Models
KNOWN_MODELS = {
    "claude-haiku-4-5-20251001",
    "claude-haiku-4-5",
    "claude-sonnet-4-6",
    "claude-opus-4-7",
}

# Tools
SHELL_TOOLS = frozenset({"bash", "shell", "computer_use"})

# Frontmatter Keys
KNOWN_FRONTMATTER_KEYS = {
    "name",
    "description",
    "model",
    "color",
    "tools",
    "skills",
    "mcp_servers",
}
