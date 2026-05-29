"""
Finding dataclass + human/JSON renderers + exit-code calculator.
All scripts emit Finding objects; this module renders them.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class Finding:
    severity: str  # 'error' | 'warn' | 'info'
    code: str
    message: str
    path: str


def render_human(findings: List[Finding], title: str = "") -> str:
    lines = [title, ""] if title else []
    if not findings:
        lines.append("OK No findings.")
        return "\n".join(lines)
    for f in findings:
        if f.severity == "error":
            prefix = "!! [ERROR]"
        elif f.severity == "warn":
            prefix = " ! [WARN] "
        else:
            prefix = "   [INFO] "
        lines.append(f"{prefix} {f.code}: {f.message}")
    return "\n".join(lines)


def render_json(findings: List[Finding]) -> str:
    return json.dumps([asdict(f) for f in findings], indent=2)


def compute_exit_code(findings: List[Finding], strict: bool = False) -> int:
    """
    0 = clean or info-only
    1 = warnings present (and not strict)
    2 = any error present (or any warn in strict mode)
    """
    if strict:
        has_blocking = any(f.severity in ("error", "warn") for f in findings)
    else:
        has_blocking = any(f.severity == "error" for f in findings)

    if has_blocking:
        return 2
    if any(f.severity == "warn" for f in findings):
        return 1
    return 0
