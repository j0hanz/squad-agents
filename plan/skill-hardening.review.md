# skill-hardening — Quality Audit Review (Pass 2)

Reviewed: 2026-06-02
Spec: `plan/skill-hardening.specs.md`
Plan: `plan/skill-hardening.plan.md`
Previous review: 2026-06-02 (Pass 1 — 3 blockers raised)

---

## Resolved Blockers

The following three blockers from Pass 1 are confirmed fixed:

| ID          | Fix confirmed                                                                                                |
| ----------- | ------------------------------------------------------------------------------------------------------------ |
| BLOCKER-001 | VAL-003 now uses `[ "$(ls ... &#124; wc -l)" -ge 13 ] && echo PASS &#124;&#124; echo FAIL` — self-verifying. |
| BLOCKER-002 | TASK-006 validate now uses `! grep -qn ...` — exits 1 when the forbidden pattern is present.                 |
| BLOCKER-003 | TASK-003 Files field now points at `tests/skill-triggering/prompts/` with `[UNVERIFIED — new directory]`.    |

---

## BLOCKER Issues (cause execution failure)

No new blockers found.

---

## WARN Issues (quality gaps, do not block execution)

### WARN-001 — Goal has two bullet points instead of one sentence

**Location:** Spec §1, Goal
**Issue:** The goal is expressed as two bullets; the second is a multi-clause completion signal that duplicates §6. Preferred form is a single sentence. Current form is acceptable but creates redundancy with Acceptance Criteria.
**Recommendation:** Merge into one sentence or move the completion signal entirely to §6.

### WARN-002 — Skill names in REQ-003 may not match routing table

**Location:** Spec §2, REQ-003; Plan TASK-003 Action
**Issue:** REQ-003 names 13 skills including `github-automation` and `agents-maintainer`. Neither name is cross-referenced against the actual SKILL.md routing table in the spec or plan. If the routing table uses different canonical names (e.g. `github-ops`), the prompt filenames derived by `run-all.sh` will not match, causing all affected tests to fail.
**Recommendation:** Cite the exact canonical names from the routing table, or add a note that filenames must match the routing table's skill-name column verbatim.

### WARN-003 — VAL-001 and VAL-002 verify presence only, not structure or position

**Location:** Spec §6, VAL-001 / VAL-002
**Issue:** `grep -q "<SUBAGENT-STOP>"` confirms the string exists but not that it is positioned immediately after frontmatter (REQ-001). `grep -q "EXTREMELY-IMPORTANT"` confirms the tag exists but not that the rebuttal table is inside it (REQ-002). No runnable check enforces the structural constraints in the corresponding REQs.
**Recommendation:** Add a secondary positional check, or accept this as a known gap and note it in the spec.

### WARN-004 — TASK-002 Action adds scope not in REQ-002

**Location:** Plan TASK-002, Action field
**Issue:** "at least two additional ones sourced from obra/superpowers' red-flags table" — REQ-002 only requires replacing existing prose with a two-column table. The additional rows expand scope. If obra/superpowers is unavailable the task cannot be completed as written.
**Recommendation:** Either add the expanded obligation to REQ-002, or remove the "at least two additional" clause from TASK-002's Action.

### WARN-005 — TASK-003 Validate is not a pass/fail gate (diverges from fixed VAL-003)

**Location:** Plan TASK-003, Validate field
**Issue:** The plan's TASK-003 Validate still reads `ls tests/skill-triggering/prompts/*.txt | wc -l`, which prints a bare count with no assertion. The spec's VAL-003 was fixed to `[ "$(ls ... | wc -l)" -ge 13 ] && echo PASS || echo FAIL`. TASK-003's validate was not updated to match: an executor running the task's validate command sees a number like `5` and cannot determine pass/fail without manual interpretation.
**Recommendation:** Replace TASK-003 Validate with the fixed VAL-003 expression from the spec.

### WARN-006 — TASK-007 composite validate inherits unasserted count

**Location:** Plan TASK-007, Validate field
**Issue:** The TASK-007 composite command embeds `ls tests/skill-triggering/prompts/*.txt | wc -l` mid-pipeline. This outputs a number to stdout but does not gate execution: if only 5 files exist, the pipeline continues and `echo ALL_PASS` is still reached. The composite therefore cannot reliably verify AC-003 (13 files present).
**Recommendation:** Replace the bare `wc -l` segment with `[ "$(ls tests/skill-triggering/prompts/*.txt 2>/dev/null | wc -l)" -ge 13 ]` so the composite exits non-zero when the file count is wrong.

### WARN-007 — TASK-006 Validate is an over-approximation of the SEC-001 obligation

**Location:** Plan TASK-006, Validate field; Spec SEC-001
**Issue:** SEC-001 permits `--dangerously-skip-permissions` inside a conditional block gated on `$SKIP_PERMISSIONS`. TASK-006's validate uses a bare `! grep -qn` which exits 1 if the string appears _anywhere_, including inside a valid conditional. A compliant implementation (flag present but gated) would cause TASK-006 to FAIL. The action description says "outside a conditional block" but the validate command cannot distinguish that.
**Recommendation:** Add a comment to TASK-006 noting that the grep check is a conservative heuristic and a manual inspection of the conditional context is required, or restate the obligation so the grep is sufficient (i.e., the flag MUST NOT appear at all; the env-var gate constructs the string dynamically).

### WARN-008 — VAL-001 and VAL-002 are asymmetric with VAL-003/VAL-005

**Location:** Spec §6, VAL-001 / VAL-002
**Issue:** VAL-003 and VAL-005 both print `PASS` on success and `FAIL` on failure (or are silent on failure). VAL-001 and VAL-002 print `PASS` on success but only exit non-zero on failure — no `FAIL` is printed. An automated executor reading stdout will see no output on failure and may log a false pass if it only scans for `PASS`.
**Recommendation:** Append `|| echo FAIL` to VAL-001 and VAL-002 for symmetry.

### WARN-009 — Constraints CON-001 and CON-003 are not traced to any task's Satisfies field

**Location:** Spec §3 CON-001, CON-003; Plan all tasks
**Issue:** `CON-001` (do not alter routing table) and `CON-003` (POSIX bash) are implementation constraints with no corresponding task that claims them in its Satisfies field. If an executor only checks Satisfies coverage, these constraints will not be verified at task level.
**Recommendation:** Add `CON-001` to TASK-002's Satisfies and `CON-003` to TASK-004/TASK-005's Satisfies, or add a lint task that confirms both.

### WARN-010 — CON-002 restates an acceptance criterion

**Location:** Spec §3, CON-002
**Issue:** "`npm run validate` MUST pass after all file changes" duplicates AC-004/VAL-004. Constraints should exclude an approach or side-effect, not restate what must be true. Carried forward from Pass 1 WARN-007.
**Recommendation:** Rephrase as a constraint on scope (e.g., "file changes MUST NOT add new top-level keys to plugin.json") or remove and rely on AC-004.

---

## Summary Table

| ID       | Severity | Location                     | Short description                                                |
| -------- | -------- | ---------------------------- | ---------------------------------------------------------------- |
| WARN-001 | WARN     | Spec §1                      | Goal is two bullets; redundant with §6                           |
| WARN-002 | WARN     | Spec REQ-003 + Plan TASK-003 | Skill names not cross-referenced to routing table                |
| WARN-003 | WARN     | Spec VAL-001 / VAL-002       | Presence-only check; no structural or positional verification    |
| WARN-004 | WARN     | Plan TASK-002 Action         | "Two additional rows" expands scope beyond REQ-002               |
| WARN-005 | WARN     | Plan TASK-003 Validate       | Bare `wc -l` — not a pass/fail gate; diverges from fixed VAL-003 |
| WARN-006 | WARN     | Plan TASK-007 Validate       | Composite allows ALL_PASS with fewer than 13 files               |
| WARN-007 | WARN     | Plan TASK-006 Validate       | Over-approximation: flags compliant conditional use as violation |
| WARN-008 | WARN     | Spec VAL-001 / VAL-002       | No `echo FAIL` branch; asymmetric with VAL-003 / VAL-005         |
| WARN-009 | WARN     | Plan all tasks               | CON-001 and CON-003 not traced to any Satisfies field            |
| WARN-010 | WARN     | Spec §3 CON-002              | Constraint duplicates acceptance criterion AC-004                |

---

```yaml
ready_for_execution: true

Blockers: none

Open warnings (10): quality gaps that do not prevent execution.
Highest-priority warnings to address before implementation:
  WARN-005 — TASK-003 Validate should be updated to match the fixed VAL-003 (self-asserting count check).
  WARN-006 — TASK-007 composite validate should gate on file count, not just print it.
  WARN-002 — Confirm skill names in REQ-003 match the routing table before writing prompt files.
```
