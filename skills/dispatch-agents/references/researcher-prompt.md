# Researcher Subagent Prompt

**purpose:** Conduct read-only investigation, find code locations, patterns, or analyze files.
**when:** Phase 1. Read-only tasks.

## Dispatch Template

```text
SCOPE:
  Files/dirs IN scope:     [directories or files to read and search]
  Files/dirs OUT of scope: [must NOT be modified]

OBJECTIVE:
  [Paste query or research objective verbatim. What concrete answers are needed.]

CONTEXT:
  Codebase root: [absolute path]
  Relevant files or prior search directions:
    [prior grep queries or files of interest]

CONSTRAINTS:
  - Read-only: Do NOT write or edit any files.
  - Do NOT commit or stage changes.
  - Use read, find, or grep tools only.

OUTPUT SCHEMA:
  VERDICT: [SUCCESS | FAILURE | BLOCKED | NEEDS_CONTEXT]
  FILES_TOUCHED: [list of files read/analyzed, or "none"]
  SUMMARY: [2-4 sentences summarizing findings and answers]
  EVIDENCE: [exact file paths, grep results, or file:line citations supporting the findings]
  BLOCKER: [if BLOCKED: what resource or info was missing. Otherwise: none.]
  QUESTION: [if NEEDS_CONTEXT: specific clarifying question. Otherwise: none.]
```
