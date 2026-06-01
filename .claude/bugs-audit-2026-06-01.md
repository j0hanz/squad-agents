# Internal Bug Tracking (2026-06-01)

| ID | Title | Severity | Location | Root Cause | Fix Direction |
|----|-------|----------|----------|------------|---------------|
| BUG #1 | Graph cycle detection misses self-loops | Minor | `skills/architecture/scripts/utils/graph.mjs` | `findCycles` filter `component.length > 1` skips single-node components. | Update filter to `>= 1` and add explicit self-import check. |
| BUG #2 | Explorer replay timestamp null-safety | Important | `hooks/handlers/explorer.mjs` | Constructing `Date` from `entry.ts` without validation can produce "Invalid Date". | Add try-catch and `isNaN(date.getTime())` check. |
| BUG #3 | Diagnose-nudge threshold logic | Critical | `hooks/handlers/diagnose-nudge.mjs` | Counted failures from small tail (50) and used exact equality (`===`). | Count from larger tail (200), use `>=` and session-scoped flag. |
| BUG #4 | Brainstorm nudge session null-safety | Important | `hooks/handlers/brainstorm-nudge.mjs` | Comparing session IDs without checking if `r.session` exists. | Add `r.session &&` guard to `.some()` check. |
| BUG #5 | Format handler silent timeout | Important | `hooks/handlers/format.mjs` | Logs success even if `sh()` fails or times out. | Check `sh()` result before logging success; log timeout otherwise. |
| BUG #6 | Spec validation regex false positives | Minor | `skills/create-specs/scripts/validate_spec.py` | `_REQ_STMT_RE` too loose, matches indented YAML. | Stiffen regex to match only start-of-line or minimal indent. |
| BUG #7 | YAML frontmatter Windows line endings | Critical | `skills/create-agent/scripts/validate_agent.py` | Regex expects `\n`, fails on `\r\n`. | Update regex to use `\r?\n`. |
| BUG #8 | Plugin validation silent skips | Critical | `bin/validate-plugin.mjs` | `fs.readdirSync()` calls are naked; fail silently on permission errors. | Wrap in try-catch and report errors explicitly. |
| BUG #9 | Hook runner stdin resource limit | Minor | `hooks/utils.mjs` | `process.stdin` consumption is unbounded. | Add 10MB limit and track cumulative chunk size. |
| BUG #10 | Git timeout handling in session | Minor | `hooks/handlers/session.mjs` | Silently omits data when git commands timeout. | Add fallback marker e.g., "[git status timed out]". |
