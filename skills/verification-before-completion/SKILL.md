---
name: verification-before-completion
description: "Evidence-based operational correctness verification. Mandatory execution check before task completion. Trigger on: 'ready to merge', 'looks good', 'mark as done', 'verification-before-completion', 'smoke test', 'manual verification'."
disable-model-invocation: false
---

# verification-before-completion

Guarantee operational correctness through execution evidence. **NEVER** confirm based on reading code alone.

## Process Flow

```dot
digraph verification_before_completion {
  rankdir=TB;
  node [shape=box, style=rounded, fontname="Helvetica"];
  edge [fontname="Helvetica", fontsize=10];

  Start [label="Start: Ready to Complete", shape=diamond];

  Checklist [label="1. Mandatory Checklist\n(Tests, Manual, Sweep, Diff)"];
  Evidence [label="2. Gather Evidence\n(Runner output / Exercise log)"];

  Logic [label="3. Decision Logic", shape=diamond];
  Diagnose [label="Handoff:\ndiagnose"];
  Blocked [label="State: Blocked/Incomplete"];
  Review [label="Handoff:\nrequest-code-review"];

  Start -> Checklist -> Evidence -> Logic;
  Logic -> Diagnose [label="regression found"];
  Logic -> Blocked [label="no test suite /\nCI-only"];
  Logic -> Review [label="verified clean"];
}
```

**trigger:** user says "ready", "mark as done", "looks good", or task is complete.
**constraint:** never confirm based on reading code alone.
**output:** verification evidence (test results or manual log).

## 1. Mandatory Checklist

**action:** Verify all items before completion.

- [ ] **Tests:** Targeted tests and regression suite pass. Paste actual runner output (exit code + pass/fail counts) — a claim without pasted output is not evidence.
- [ ] **Manual:** Documented inputs/outputs if no automation.
- [ ] **Bug Fix:** Confirm reproduction failure then confirm success.
- [ ] **Clean:** `grep` sweep for debug logs/tags (`debugger`, `pdb`, `TODO`).
- [ ] **Lint:** No new unused imports or variables.
- [ ] **Diff:** Audit every change for intent.

## 2. Decision Logic

| Status             | Action                                            |
| :----------------- | :------------------------------------------------ |
| **CI-Only**        | Stop. Report: "Blocked by CI. Wait for pipeline." |
| **No Test Suite**  | Mark as **INCOMPLETE**. Document rationale.       |
| **Regression**     | Stop. Invoke `diagnose`.                          |
| **Verified Clean** | Transition to `request-code-review`.              |

## 3. Manual Verification Template

**action: Gather Evidence**
If no automated pass/fail signal exists, propose a manual test plan via `AskUserQuestion`:

1. ✅ **Recommended** — [Test Plan] based on [feature scope and risk].
2. **Alternative** — [Lighter Test] + justification.
3. **Other** — Custom verification.

**format:**

```markdown
### Manual Verification

**input:** [Specific values]
**expected:** [Observed side-effect]
**observed:** [Actual behavior]
**status:** PASS/FAIL
```

## 4. Critical Failure Modes

**avoid:**

- **Confidence:** "It should work" is not evidence.
- **Green-Wash:** Mocks hiding actual logic or missing assertions.
- **Shadow Regressions:** Distant modules broken by global state changes.

## 5. Expert Patterns

**action:** Use the N-1 test (Revert → Fail → Fix → Pass, see [`test-driven-development`](../test-driven-development/SKILL.md#n-1-test-false-green-elimination)) to eliminate false greens.
**action:** Test `null`, `undefined`, empty collections, and boundary cases to ensure robust coverage.

**next skills:**

- `request-code-review`: Once all verification items are satisfied and behavior is confirmed clean through execution evidence.

## Transition

**next:** Invoke `request-code-review` for all non-trivial changes.
