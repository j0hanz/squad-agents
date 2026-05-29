"""Parse YAML frontmatter from markdown files."""

import re
from typing import Any, Tuple


def parse_frontmatter(content: str) -> Tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown.

    Returns: (frontmatter_dict, body_text)
    """
    import yaml

    match = re.match(r"---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        fm = yaml.safe_load(match.group(1)) or {}
        body = match.group(2)
        return fm, body
    except Exception:
        return {}, content
