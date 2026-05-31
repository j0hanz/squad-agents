---
description: |
  Author, audit, update, lint, or run evaluations for plugin skills. Modes: create (author new suite), audit (review existing suite), update (refine suite), lint (check suite structure), run (execute evals with or without a baseline).
argument-hint: [create|audit|update|lint|run] [skill-name]
---

# Eval — Skill Evaluation

Author, audit, update, lint, or run evaluations for plugin skills.

**Mode format:** `$ARGUMENTS` = `[mode] [skill-name]`

## Modes

| Mode            | Usage                  | Purpose                                                                  |
| --------------- | ---------------------- | ----------------------------------------------------------------------- |
| `create [name]` | `create brainstorming` | Author a new eval suite from scratch                                     |
| `audit [name]`  | `audit new`            | Audit existing eval suite quality & completeness                        |
| `update [name]` | `update deliver`       | Improve/refine an existing eval suite                                    |
| `lint [name]`   | `lint deliver`         | Lint eval YAML/JSON for syntax and structure                            |
| `run [name]`    | `run explorer`         | Run the skill against its evals (simulation, or benchmark vs a baseline) |

If mode is missing, ask:

> "Do you want to **create**, **audit**, **update**, **lint**, or **run** evaluations? And which skill?"

## Mode: Run [skill-name]

Two ways to run, depending on what the user wants to learn. Expected suite file: `skills/[skill-name]/evals.yaml`. If it's ambiguous which they want, ask:

> "Quick **behavioral simulation** (does the skill fire and follow its steps?), or a full **benchmark vs a baseline** (does it measurably beat plain Claude, with graded outputs and a review UI)?"

### A) Behavioral simulation (fast, no baseline)

Checks that the skill triggers and follows its workflow on each case. Invoke the `skill-builder` skill and run a single with-skill pass over the suite (no baseline, one run per case) — this is its Test & Iterate Workflow with the baseline step skipped. Use this when the question is just "does the skill fire and follow its steps?" rather than "is it measurably better?".

### B) Benchmark vs a baseline (run → grade → review → iterate)

When the question is "is the skill actually worth its context?" or "is the new version better?", run the skill against its evals **and** a baseline, grade the outputs, aggregate a benchmark, and open the review viewer. Invoke the `skill-builder` skill and follow its **Test & Iterate Workflow** (`skills/skill-builder/references/eval-loop.md`) — it drives the with-skill vs baseline runs, grading, `aggregate_benchmark.py`, and `generate_review.py`.

## Mode: Create [skill-name]

Author a new eval suite for the named skill.
Invoke the `skill-builder` skill — it handles suite authoring (cases + assertions + grader specs) as part of its guided workflow.

## Mode: Audit [skill-name]

Audit existing eval suite quality for the named skill.
Invoke the `skill-builder` skill to review and improve the suite.

## Mode: Update [skill-name]

Improve and refine an existing eval suite based on audit findings.
Invoke the `skill-builder` skill to guide the refinement.

## Mode: Lint [skill-name]

Lint the eval suite structure and syntax.

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/skills/skill-builder" \
  python -m scripts.lint_suite skills/[skill-name]/evals.yaml --out lint_report.html
```

Omit `--out` to print findings to stdout, or use `--out report.json` for machine-readable output.

<!-- Usage: /eval run explorer -->
<!-- Usage: /eval audit brainstorming -->
