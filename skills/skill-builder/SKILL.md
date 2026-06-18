---
name: skill-builder
description: "Build, test, and optimize Agent Skills. Lifecycle management including eval-driven iteration. Trigger on: 'make skill', 'build skill', 'skill not working', 'optimize skill', 'skill-builder', 'run evals', 'benchmark skill'."
disable-model-invocation: false
---

# skill-builder

Lifecycle management for Claude Agent Skills. Optimized for performance and triggering reliability.

## Process Flow

```dot
digraph skill_builder {
  rankdir=TB;
  node [shape=box, style=rounded, fontname="Helvetica"];
  edge [fontname="Helvetica", fontsize=10];

  Start [label="Start: Skill Request", shape=diamond];
  Route [label="0. Intent Routing\n(New / Improve / Workflow)"];

  Draft [label="1. Interview & Draft\n(SKILL.md, description, audit)"];
  Test [label="2. Test Definition\n(evals.json, negative cases)"];

  EvalLoop [label="3. Eval Loop", shape=ellipse];
  Init [label="Setup\n(init_eval.py)"];
  Execute [label="Parallel Run\n(with_skill vs baseline)"];
  Grade [label="Grading\n(aggregate_benchmark)"];
  Review [label="Viewer\n(generate_review.py)"];

  Improve [label="4. Improvement Loop\n(Diagnose & Refine)"];
  Done [label="Skill Published", shape=doublecircle];

  Start -> Route -> Draft -> Test -> EvalLoop;
  EvalLoop -> Init -> Execute -> Grade -> Review;
  Review -> Improve -> Draft [label="re-iterate"];
  Review -> Done [label="passing"];
}
```

## 0. Intent Routing

- **New Skill:** [Interview and Draft](#step-1-interview--draft)
- **Workflow to Skill:** Extract steps, then [Draft](#step-1-interview--draft)
- **Improve/Fix:** [Diagnosis & Iteration](#step-3-eval-loop)
- **Quick Build:** Draft directly, skip formal evals.

## Step 1: Interview & Draft

**action: Draft Skill**
Extract requirements and confirm the skill draft via `AskUserQuestion`:

1. ✅ **Recommended** — [SKILL.md draft] based on [tools, sequence, and I/O formats].
2. **Alternative** — [Alternative approach] + reason.
3. **Other** — Custom draft.

4. **Audit:** Dispatch `general-purpose` agent to check triggering effectiveness, using the [subagent-contract](../multi-agent-dispatch/references/subagent-contract.md) (SCOPE/OBJECTIVE/CONTEXT/CONSTRAINTS/OUTPUT SCHEMA).
   - **Red Flags:** Vague triggers, tool overlap with existing skills, nested loops in instructions, missing I/O contracts.

## Step 2: Test Definition

Save cases to `evals/evals.json`.

**Baseline Guidance:**

- **Runs:** Minimum 3 runs per eval case to account for variance.
- **Temperature:** Set `0.0` for deterministic flows, `0.7` for creative drafting.
- **Diversity:** Include at least one \"negative\" case (where skill should NOT trigger).

## Step 3: Eval Loop (Iteration N)

1. **Setup:** `python scripts/init_eval.py --skill-name <name> --eval-id <ID>`
2. **Execute:** Spawn `with_skill` and `baseline` subagents in parallel, using the [subagent-contract](../multi-agent-dispatch/references/subagent-contract.md) for each prompt. **Max 5 concurrent agents per batch** — if more than 5 eval cases run together, batch the rest sequentially.
3. **Metrics:** Capture `total_tokens` and `duration_ms` into `timing.json`.
4. **Grade:** Dispatch agent to score assertions against the OUTPUT SCHEMA's `EVIDENCE` field. Save to `grading.json`.
5. **Aggregate:** `python -m scripts.aggregate_benchmark <workspace>/iteration-N`
6. **Viewer:** Launch `generate_review.py`. Provide clickable link.

**Error Recovery:**

- **Timeout:** If subagent hangs, check `run_log.txt` in worktree. Rerun with `--timeout 300`.
- **Disk Full:** `skill-builder` creates worktrees. Run `git worktree prune` if space is low.
- **Grading Fail:** If grading agent is hallucinating, manually override `grading.json` and aggregate.

## Step 4: Improvement Loop

1. **Diagnose:** Identify root causes of failures.
2. **Generalize:** Bundle repetitive logic into `scripts/`.
3. **Refine Prompt:** Remove noise; clarify steps.
4. **Rerun:** Execute next iteration in new directory.

**next skills:**

- `verification-before-completion`: Once the skill passes evals, to perform a final "sanity check" manual run in a real project environment.

## Skill Design Standards

- **Progressive Disclosure:** Headers → Bullets → References.
- **Reference Fences:** Move details to `references/` if body > 500 lines.
- **Imperative Voice:** Commands only. Zero prose explanations.
- **No speculative features:** Justify every line with a requirement.

## Mandatory Rules

- **NEVER** optimize description before logic is stable.
- **NEVER** skip baseline runs for new skills.
- **NEVER** use prose paragraphs in the skill body.
- **NEVER** preload skills with `disable-model-invocation: true`.
- **Subagent isolation:** Use `worktree` for writes.
