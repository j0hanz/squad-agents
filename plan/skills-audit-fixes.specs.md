# skills-audit-fixes

## 1. Goal

- Fix the 9 consolidated findings from the skills audit ([SKILLS_AUDIT_VERIFIED.md](../skills/SKILLS_AUDIT_VERIFIED.md) §3) so every skill in `skills/` is free of text corruption, internal contradictions, and undeclared failure-routing gaps.
- Completion signal: all 9 findings closed, `validate.py --cross` passes, and a manual diff review confirms each fix matches its finding exactly with no unrelated changes.

## 2. Requirements

- `REQ-001`: Remove the corrupted duplicate sentence fragment at the end of `skills/brainstorming/SKILL.md`'s Troubleshooting section (lines 282-283).
- `REQ-002`: Remove the duplicated Reference Map entries in `skills/skill-builder/SKILL.md` (lines 274-276) and fix the missing leading backtick left by the corruption.
- `REQ-003`: Change `skills/multi-agent-development/SKILL.md` (lines 199, 215) so it no longer tells the agent to auto-invoke `github-automation`; it MUST instead prompt the user to run `/github-automation` manually, matching the pattern already used in `code-review:228` and `verification-before-completion:60`.
- `REQ-004`: Move `skills/multi-agent-development/evals.json` to `skills/multi-agent-development/evals/evals.json` to match the convention used by all other 15 skills.
- `REQ-005`: Add a named failure transition in `skills/verification-before-completion/SKILL.md`: if a regression or failing test is found during verification, the skill MUST instruct the agent to invoke `diagnose` before re-attempting completion.
- `REQ-006`: Change `skills/code-review/SKILL.md`'s FAIL path (line 229) from the unnamed "route back to implementation" to a concrete tiered target: correctness/security issues → `diagnose`, structural issues → `refactor`, otherwise → the originating implementation skill.
- `REQ-007`: Add an attempt cap to `skills/diagnose/SKILL.md`'s re-diagnose loop (around lines 148-152), mirroring `multi-agent-development`'s "2 attempts → BLOCKED → surface to user" pattern.
- `REQ-008`: Resolve the orphaned `skills/architecture/scripts/estimate_risk.py` — either wire it into `skills/architecture/SKILL.md` (Phase 1 or Step 4) or delete it if it is confirmed obsolete. Decision deferred to a clarifying question during planning (see Constraints).
- `REQ-009`: Align the stated threshold for "how many hypotheses justify parallel dispatch vs. sequential testing" between `skills/diagnose/SKILL.md` Phase 3 and `skills/multi-agent-dispatch/SKILL.md`'s dispatch gate, standardizing on multi-agent-dispatch's existing "a single domain you already fully understand → stay sequential" language.

## 3. Constraints

- `CON-001`: Edits MUST be minimal and targeted — do not rewrite or restructure any section beyond what each finding requires (no incidental rewording, no added abstractions).
- `CON-002`: Do not touch any skill file not named in the 9 findings above.
- `CON-003`: REQ-008's wire-in-vs-delete decision for `estimate_risk.py` requires a one-time human choice before that task can be executed; default to **delete** if no response is given, since the script is unreferenced and an architecture skill maintainer can re-add it from git history if it turns out to be needed.

## 4. Interfaces

N/A — this is a documentation/skill-definition maintenance task. All "interfaces" are markdown/JSON file edits within `skills/`; there is no runtime API, CLI, or UI surface.

## 5. Context

- Files: see `Files:` line on each task in `skills-audit-fixes.plan.md`.
- Current behavior: documented in [SKILLS_AUDIT.md](../skills/SKILLS_AUDIT.md) and [SKILLS_AUDIT_VERIFIED.md](../skills/SKILLS_AUDIT_VERIFIED.md).
- Conventions: each skill lives at `skills/<name>/SKILL.md`; eval fixtures live at `skills/<name>/evals/evals.json`; cross-skill handoffs are expressed as plain-text "invoke `<skill-name>`" instructions inside the SKILL.md body, not as code.

## 6. Acceptance Criteria & Validation

- `AC-001`: `skills/brainstorming/SKILL.md` Troubleshooting section ends cleanly with no duplicate/truncated fragment.
  `VAL-001`: `grep -n "daries clear" skills/brainstorming/SKILL.md` returns no match.
- `AC-002`: `skills/skill-builder/SKILL.md`'s Reference Map lists each entry exactly once, valid markdown.
  `VAL-002`: `grep -c "agents/analyzer.md" skills/skill-builder/SKILL.md` returns `1`.
- `AC-003`: `multi-agent-development/SKILL.md` no longer instructs direct auto-invocation of `github-automation`.
  `VAL-003`: `grep -n "invoke github-automation" skills/multi-agent-development/SKILL.md` returns no match; a prompt-the-user instruction is present instead.
- `AC-004`: eval fixture relocated.
  `VAL-004`: `test -f skills/multi-agent-development/evals/evals.json && test ! -f skills/multi-agent-development/evals.json`
- `AC-005`: verification-before-completion names `diagnose` on regression.
  `VAL-005`: `grep -n "diagnose" skills/verification-before-completion/SKILL.md` returns at least one match.
- `AC-006`: code-review FAIL path names concrete targets.
  `VAL-006`: `grep -n "diagnose\|refactor" skills/code-review/SKILL.md | grep -i fail` returns at least one match near the FAIL section.
- `AC-007`: diagnose has a numeric attempt cap.
  `VAL-007`: `grep -nE "[0-9]+ (attempt|fix attempt)" skills/diagnose/SKILL.md` returns at least one match.
- `AC-008`: `estimate_risk.py` is either referenced in `architecture/SKILL.md` or no longer present in `skills/architecture/scripts/`.
  `VAL-008`: `grep -q "estimate_risk.py" skills/architecture/SKILL.md && test -f skills/architecture/scripts/estimate_risk.py` (wired) `||` `test ! -f skills/architecture/scripts/estimate_risk.py` (deleted) — exactly one branch true.
- `AC-009`: diagnose and multi-agent-dispatch agree on the sequential-vs-parallel threshold wording.
  `VAL-009`: manual diff review — both files use equivalent "single domain you already understand → sequential" framing.

## 7. Examples & Edge Cases

**Positive example (REQ-003):**

```
Before: "5. invoke github-automation to open PR"
After:  "5. Prompt the user to run `/github-automation` to open the PR — it requires user invocation and cannot be triggered automatically."
```

**Edge cases:**

- REQ-008: if `estimate_risk.py` turns out to be referenced by an external tool outside `skills/architecture/SKILL.md` (e.g. a CI script), deleting it would break that — task includes a repo-wide grep for the filename before deleting.
- REQ-004: any tooling that currently reads `skills/multi-agent-development/evals.json` directly (not via the `evals/` convention) needs a check — task includes a repo-wide grep for the old path before moving.
