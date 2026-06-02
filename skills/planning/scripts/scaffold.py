#!/usr/bin/env python3
"""scaffold.py — Emit paired <name>.specs.md + <name>.plan.md templates.

Usage:
    python scaffold.py <name> [--depth sketch|contract|blueprint]
                              [--dir plan] [--domain api|cli]
                              [--goal TEXT]

Both files are written to <dir>/. If <dir> doesn't exist it is created.
The plan file contains a cross-link back to the spec file so the pairing
is visible from either artifact.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Spec templates by depth
# ---------------------------------------------------------------------------

_SPEC_TEMPLATES: dict[str, str] = {
    "sketch": """\
# {name}

## 1. Goal

- {goal}
- Completion signal: [one measurable observable outcome]

## 2. Requirements

- `REQ-001`: [Requirement — use MUST/SHALL + measurable threshold]
- `REQ-002`: [Requirement]

## 3. Constraints

- `CON-001`: [What the solution MUST NOT do — optional for sketch]

## 4. Interfaces

- [Rough description of inputs/outputs]
""",
    "contract": """\
# {name}

## 1. Goal

- {goal}
- Completion signal: [one measurable observable outcome]

## 2. Requirements

- `REQ-001`: [Requirement — use MUST/SHALL + measurable threshold]
- `REQ-002`: [Requirement]

## 3. Constraints

- `CON-001`: [What the solution MUST NOT do]

## 4. Interfaces

The system exposes the following interfaces:

### [Interface Name]

**Input:**
- `field` (type, required|optional): [description]

**Output:**
- `field` (type): [description]

**Errors:**
- `400`: [Missing/invalid fields]
- `401`: [Unauthorized]
- `500`: [Internal error]

## 5. Context

- Files: [path/to/relevant/file]
- Current behavior: [what exists today]
- Conventions: [naming, patterns this project follows]

## 6. Acceptance Criteria & Validation

- `AC-001`: [User-observable result]
- `VAL-001`: `[runnable shell command to verify AC-001]`

## 7. Examples & Edge Cases

**Positive example:**
```
Input:  [example]
Output: [example]
```

**Edge cases:**
- [Empty/null input → expected behavior]
- [Boundary condition → expected behavior]
""",
    "blueprint": """\
# {name}

## 1. Goal

- {goal}
- Completion signal: [one measurable observable outcome]

## 2. Requirements

- `REQ-001`: [Requirement — use MUST/SHALL + measurable threshold]
- `REQ-002`: [Requirement]
- `SEC-001`: [Security requirement]
- `PERF-001`: [Performance requirement with numeric threshold]

## 3. Constraints

- `CON-001`: [What the solution MUST NOT do]

## 4. Interfaces

The system exposes the following interfaces:

### [Interface Name]

**Input:**
- `field` (type, required|optional): [description]

**Output:**
- `field` (type): [description]

**Errors:**
- `400`: [Missing/invalid fields]
- `401`: [Unauthorized]
- `500`: [Internal error]
- `503`: [Downstream failure / timeout]

## 5. Context

- Files: [path/to/relevant/file]
- Architecture: [current system structure]
- Current behavior: [what exists today]
- Conventions: [naming, patterns this project follows]

## 6. Acceptance Criteria & Validation

- `AC-001`: [User-observable result]
- `VAL-001`: `[runnable shell command to verify AC-001]`

## 7. Examples & Edge Cases

**Positive example:**
```
Input:  [example]
Output: [example]
```

**Edge cases:**
- [Empty/null input → expected behavior]
- [Concurrent requests → expected behavior]
- [Timeout → expected behavior]

## 8. Notes & Risks

- `RISK-001`: [Risk with named mitigation or "accepted"]
- `NOTE-001`: [Rollout/migration/rollback note]
""",
}

# ---------------------------------------------------------------------------
# Domain snippets injected into spec
# ---------------------------------------------------------------------------

_DOMAIN_SNIPPETS: dict[str, dict[str, str]] = {
    "api": {
        "requirements": (
            "\n- `SEC-101`: All requests MUST include a valid Bearer token"
            " in the Authorization header.\n"
            "- `REQ-101`: The API MUST return JSON for all responses.\n"
        ),
        "interfaces": (
            "\n**Standard error cases (include in every endpoint):**\n"
            "- `400 Bad Request`: Invalid schema or missing required fields.\n"
            "- `401 Unauthorized`: Missing or invalid auth token.\n"
            "- `503 Service Unavailable`: Downstream dependency failure.\n"
        ),
    },
    "cli": {
        "requirements": (
            "\n- `REQ-201`: The tool MUST support `--json` for machine-readable output.\n"
            "- `REQ-202`: The tool MUST exit with a non-zero code on failure.\n"
            "- `COMP-201`: The tool MUST be compatible with POSIX-compliant shells.\n"
        ),
        "interfaces": "",
    },
}

# ---------------------------------------------------------------------------
# Plan template
# ---------------------------------------------------------------------------

_PLAN_TEMPLATE = """\
# {name}

Spec: [{name}.specs.md]({name}.specs.md)

## Goal

[Copy goal from spec, or leave for sync.py to populate]

## PHASE-001: Implementation

[Run `sync.py {name}.specs.md` to populate task stubs from spec requirements]

## PHASE-END: Acceptance

[Run `sync.py {name}.specs.md` to add acceptance task from spec ACs]
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _inject_domain(template: str, domain: str) -> str:
    snippets = _DOMAIN_SNIPPETS.get(domain, {})
    req_snip = snippets.get("requirements", "")
    iface_snip = snippets.get("interfaces", "")
    if req_snip and "## 2. Requirements" in template:
        template = template.replace(
            "## 2. Requirements", f"## 2. Requirements{req_snip}", 1
        )
    if iface_snip and "## 4. Interfaces" in template:
        if "The system exposes the following interfaces:" in template:
            template = template.replace(
                "The system exposes the following interfaces:",
                f"The system exposes the following interfaces:{iface_snip}",
                1,
            )
        else:
            # Fallback for sketch template
            template = template.replace(
                "## 4. Interfaces",
                f"## 4. Interfaces\n{iface_snip}",
                1,
            )
    return template


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def scaffold(
    name: str,
    depth: str = "contract",
    out_dir: str | Path = "plan",
    domain: str | None = None,
    goal: str = "One sentence: what capability or outcome?",
) -> tuple[Path, Path]:
    """Write paired spec + plan files. Returns (spec_path, plan_path)."""
    if "/" in name or "\\" in name or name.startswith(".") or "\x00" in name:
        raise ValueError(
            f"Invalid name {name!r}: must be a plain filename stem with no path separators"
        )
    if depth not in _SPEC_TEMPLATES:
        raise ValueError(
            f"Unknown depth {depth!r}; choose from {list(_SPEC_TEMPLATES)}"
        )

    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    spec_text = _SPEC_TEMPLATES[depth].format(name=name, goal=goal)
    if domain:
        spec_text = _inject_domain(spec_text, domain)

    plan_text = _PLAN_TEMPLATE.format(name=name)

    spec_path = out / f"{name}.specs.md"
    plan_path = out / f"{name}.plan.md"

    spec_path.write_text(spec_text, encoding="utf-8")
    plan_path.write_text(plan_text, encoding="utf-8")

    return spec_path, plan_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold paired <name>.specs.md + <name>.plan.md files."
    )
    parser.add_argument("name", help="Stem name (e.g. 'auth-jwt')")
    parser.add_argument(
        "--depth",
        choices=["sketch", "contract", "blueprint"],
        default="contract",
        help="Spec maturity level (default: contract)",
    )
    parser.add_argument(
        "--dir",
        default="plan",
        metavar="DIR",
        help="Output directory (default: plan/)",
    )
    parser.add_argument(
        "--domain",
        choices=["api", "cli"],
        help="Inject domain-specific snippets",
    )
    parser.add_argument("--goal", default=None, help="One-sentence goal to pre-fill")

    args = parser.parse_args()
    goal = args.goal or "One sentence: what capability or outcome?"
    spec_path, plan_path = scaffold(args.name, args.depth, args.dir, args.domain, goal)
    print(f"Created: {spec_path}")
    print(f"Created: {plan_path}")
    print(f"\nNext: fill in {spec_path.name}, then run:")
    print(f"  python sync.py {spec_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"scaffold.py: {e}", file=sys.stderr)
        sys.exit(1)
