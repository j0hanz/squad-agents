# Patch for quick_validate.py _parse_frontmatter function
def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a flat YAML-style frontmatter block into top-level key/value pairs."""
    try:
        import yaml

        result = yaml.safe_load(text) or {}
        return {k: str(v) for k, v in result.items() if isinstance(k, str)}
    except ImportError:
        pass

    # Fallback: hand-rolled parser for environments without PyYAML
    result: dict[str, str] = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = __import__("re").match(r"^([a-zA-Z_][a-zA-Z0-9_-]*):\s*(.*)", lines[i])
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value in (">", "|", ">-", "|-", ""):
                i += 1
                block: list[str] = []
                while i < len(lines) and (
                    lines[i].startswith("  ") or lines[i].startswith("\t")
                ):
                    block.append(lines[i].strip())
                    i += 1
                sep = "\n" if value in ("|", "|-") else " "
                result[key] = sep.join(block)
                continue
            else:
                result[key] = value.strip('"').strip("'")
        i += 1
    return result
