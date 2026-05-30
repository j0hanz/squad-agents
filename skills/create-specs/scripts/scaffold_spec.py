#!/usr/bin/env python3
import argparse

TEMPLATES = {
    "sketch": """# [Title]

## 1. Goal
- One sentence: what capability or outcome?
- One measurable completion signal.

## 2. Requirements
- REQ-001: [Requirement]
- REQ-002: [Requirement]

## 3. Constraints
- CON-001: [Optional — what the solution does NOT do. Remove section if none apply.]

## 4. Interfaces
- [Rough description of inputs/outputs]
""",
    "contract": """# [Title]

## 1. Goal
- One sentence: what capability or outcome?
- One measurable completion signal.

## 2. Requirements
- REQ-001: [Requirement]
- REQ-002: [Requirement]

## 3. Constraints
- CON-001: [Constraint - what the solution does NOT do]

## 4. Interfaces
### [Interface Name]
- **Input**: [Schema/Params]
- **Output**: [Response]
- **Errors**: [Status Codes]

## 5. Context
- Files: [Path to relevant files]
- Current behavior: [Description]

## 6. Acceptance Criteria & Validation
- AC-001: [User-observable result]
- VAL-001: [Command/Action to verify AC-001]

## 7. Examples & Edge Cases
- [Positive Example]
- [Edge Case: Empty/Null input]
""",
    "blueprint": """# [Title]

## 1. Goal
- One sentence: what capability or outcome?
- One measurable completion signal.

## 2. Requirements
- REQ-001: [Requirement]
- REQ-002: [Requirement]
- SEC-001: [Security requirement]
- PERF-001: [Performance requirement]

## 3. Constraints
- CON-001: [Constraint]

## 4. Interfaces
### [Interface Name]
- **Input**: [Schema/Params]
- **Output**: [Response]
- **Errors**: [Status Codes]

## 5. Context
- Files: [Path to relevant files]
- Architecture: [Description]

## 6. Acceptance Criteria & Validation
- AC-001: [User-observable result]
- VAL-001: [Command/Action to verify AC-001]

## 7. Examples & Edge Cases
- [Positive Example]
- [Edge Case: Concurrent requests]
- [Edge Case: Timeouts]

## 8. Notes & Risks
- RISK-001: [Potential issue]
- NOTE-001: [Rollout/Migration note]
""",
}

DOMAIN_SNIPPETS = {
    "api": {
        "requirements": """
- SEC-101: All requests MUST include a valid Bearer token in the Authorization header.
- REQ-101: The API MUST return JSON payloads for all successful and error responses.
""",
        "interfaces": """
**Standard error cases (include in every endpoint):**
- `400 Bad Request`: Invalid schema or missing required fields.
- `401 Unauthorized`: Missing or invalid authentication token.
- `503 Service Unavailable`: Downstream dependency failure or timeout.
""",
    },
    "cli": {
        "requirements": """
- REQ-201: The tool MUST support a `--json` flag for machine-readable output.
- REQ-202: The tool MUST exit with a non-zero code on failure.
- COMP-201: The tool MUST be compatible with POSIX-compliant shells.
""",
        "interfaces": "",
    },
}


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a new specification template."
    )
    parser.add_argument(
        "--level",
        choices=["sketch", "contract", "blueprint"],
        default="contract",
        help="Spec maturity level",
    )
    parser.add_argument(
        "--domain", choices=["api", "cli"], help="Inject domain-specific snippets"
    )
    parser.add_argument("--goal", help="One-sentence goal to pre-fill")
    args = parser.parse_args()

    template = TEMPLATES[args.level]

    if args.goal:
        template = template.replace(
            "One sentence: what capability or outcome?", args.goal
        )

    if args.domain:
        snippets = DOMAIN_SNIPPETS[args.domain]
        req_snippet = snippets.get("requirements", "")
        iface_snippet = snippets.get("interfaces", "")
        if req_snippet and "## 2. Requirements" in template:
            template = template.replace(
                "## 2. Requirements", f"## 2. Requirements\n{req_snippet}"
            )
        if iface_snippet and "## 4. Interfaces" in template:
            template = template.replace(
                "## 4. Interfaces", f"## 4. Interfaces\n{iface_snippet}"
            )

    print(template)


if __name__ == "__main__":
    main()
