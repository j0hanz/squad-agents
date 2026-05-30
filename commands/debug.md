---
description: Debug a problem using the diagnose skill's structured root-cause methodology.
argument-hint: [symptom or error description]
---

# Debug: $ARGUMENTS

Invoke the `diagnose` skill for the problem described in `$ARGUMENTS`.

If no description is provided, ask:

> "What is the symptom? Describe the unexpected behavior, error message, or failure."

## discipline

`diagnose` is a **rigid** skill — follow its methodology exactly. Do not jump to fixes before the root cause is documented. The phases are:

1. **Reproduce** — confirm you can see the failure
2. **Gather** — collect logs, diffs, error messages
3. **Hypothesize** — list 2–3 ranked root-cause candidates
4. **Test** — eliminate hypotheses with targeted evidence
5. **Fix** — apply minimal fix once root cause is confirmed
6. **Prevent** — add a regression test so it cannot recur silently

---

<!-- Usage: /debug login fails after password reset -->
<!-- Usage: /debug npm test throws ENOENT on CI -->
