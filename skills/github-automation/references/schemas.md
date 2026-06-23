# JSON Output Schemas

## Workflow Security Auditor Output Contract

When dispatching the `general-purpose` subagent for the audit step (SKILL.md PATH A step 5), instruct it to produce JSON output with the following structure:

```json
{
  "summary": {
    "critical": 0,
    "high": 0,
    "medium": 0
  },
  "clean": true,
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "rule": "rule-name",
      "file": "path/to/workflow.yml",
      "line": 42,
      "evidence": "exact YAML snippet or key path showing the vulnerability"
    }
  ]
}
```

### Field Definitions

- **summary.critical** (int): Count of critical-severity findings (exploit risk, immediate takeover)
- **summary.high** (int): Count of high-severity findings (privilege escalation, token over-scoping)
- **summary.medium** (int): Count of medium-severity findings (configuration risks, hardening gaps)
- **clean** (bool): true if and only if all severity counts are zero
- **findings[]** (array): Array of finding objects; empty array if clean=true
  - **severity** (string): One of `critical`, `high`, `medium`, `low`
  - **rule** (string): Rule identifier (e.g., `unscoped-oidc-trust`, `pull-request-target-injection`)
  - **file** (string): Relative path to the audited workflow file
  - **line** (int): Line number in the YAML file where the finding was detected
  - **evidence** (string): Exact YAML snippet, key path, or inline quote showing the vulnerability
