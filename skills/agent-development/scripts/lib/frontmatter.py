"""Parse YAML frontmatter from markdown files."""

from __future__ import annotations
import re
from typing import Any, Tuple, Dict


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from markdown.

    Args:
        content: The full content of the markdown file.

    Returns:
        A tuple of (frontmatter_dict, body_text).
    """
    try:
        import yaml
    except ImportError:
        # If PyYAML is missing, we can't parse frontmatter.
        return {}, content

    match = re.match(r"---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        fm = yaml.safe_load(match.group(1))
        if not isinstance(fm, dict):
            return {}, content
        body = match.group(2)
        return fm, body
    except (yaml.YAMLError, AttributeError):
        # Return empty frontmatter if parsing fails
        return {}, content
