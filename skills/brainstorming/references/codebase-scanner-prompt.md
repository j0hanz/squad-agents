# Codebase Scanner Subagent Prompt

**purpose:** Phase 1 discovery — scan the codebase for context relevant to the feature under discussion.
**when:** Start of Phase 1, before asking any questions.
**subagent_type:** `general-purpose`

---

## Dispatch Template

```text
SCOPE: Read-only. Use Glob, Grep, Read, and Bash only to run the scan script below — never Write or Edit.
OBJECTIVE: Scan the codebase for context relevant to the feature description and return a structured
  Codebase Context Report. No questions. No solutions. No code. Report only what you find.
CONTEXT:
  Feature description (verbatim): [paste feature description exactly as stated]
  Project root: [absolute path]
  Skill dir: [absolute path of skills/brainstorming, or $CLAUDE_PLUGIN_ROOT/skills/brainstorming]

CONSTRAINTS:
  - Extract and sanitize domain nouns/verbs from the feature description (e.g. "add search to catalog"
    -> search, catalog). Strip all shell metacharacters ($, `, \, ", ', ;, &, |, <, >) — allow only
    alphanumeric characters and hyphens. Derive 2-3 adjacent synonyms per noun (search -> query, lookup,
    filter).
  - Preferred: run as a single parallel call using single quotes for all arguments:
      python '<skill-dir>/scripts/scan_context.py' -- '<sanitized_noun1>' ['<sanitized_noun2>' ...]
        --cwd '<project_root>'
    Use its JSON output to populate the report. Fall back to the manual steps below only if it fails.
  - Manual fallback (run all steps in parallel):
    1. Files — Glob `**/*<noun>*`, Grep for function/class/type/import matches. Cap at 5.
    2. Git history — `git log --oneline -10 -- <filepath>` for each found file.
    3. Terminology — search glossary.md, README "Concepts" sections, typed definitions for domain nouns.
    4. Design docs — search ADRs (docs/adr/, *ADR*) and architecture docs (ARCHITECTURE.md).
    5. Constraints — rate limits, interface contracts, TODO/FIXME comments, test coverage signals.
    6. Analogous features — Grep for adjacent synonyms; report up to 2 files (candidates for pattern
       reuse or the Creative Checkpoint).
    7. Test coverage — for each found file, check for a corresponding test file (test_<name>.*,
       <name>.test.*, <name>.spec.*, <name>_test.* in the same dir or tests/, __tests__/, spec/).

OUTPUT: Return exactly this structure. Write "None found" for empty sections.

  ## Codebase Context Report

  **Feature area:** [domain nouns and verbs extracted from the request]

  ### Related Files
  | File | Purpose | Last commit |

  ### Recent Changes
  [Git log patterns: what changed, how recently, stability signals]

  ### Terminology Found
  [`Term` — [where found] — [apparent meaning]]

  ### Design Docs
  [ADRs or architecture docs: title, location, key decision relevant to this feature]

  ### Technical Constraints
  [Performance limits, API contracts, relevant TODOs/FIXMEs]

  ### Analogous Features
  [Existing features with structural similarity — file path and pattern used. "None found" if absent.]

  ### Test Coverage
  | File | Has tests | Test file |
  [Note untested files explicitly — they signal higher implementation risk.]

  ### Scope Signal
  **Estimate:** [S / M / L / XL]
  **Reasoning:** [1-2 sentences: affected files, change surface, cross-cutting dependencies]
  S = 1-2 files, M = 3-5 files, L = 5-10 files or module boundary, XL = 10+ files or architectural change

  ### Key Unknowns
  [Things searched but not found — missing tests, no glossary, no ADRs on this subsystem]
```

**Timeout / Dead-Letter Fallback:** if the agent times out or fails (e.g. repository too large), do not fail the workflow — fall back to shallow regex heuristics in the parent context (Grep/Glob with strict depth limits) or ask the user to narrow scope.
