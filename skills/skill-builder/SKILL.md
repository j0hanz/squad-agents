---
name: skill-builder
description: Build, test, improve Claude Agent Skills. Trigger on 'make skill', 'build skill', 'skill not working', 'turn workflow into skill', 'run evals', 'optimize skill', SKILL.md feedback.
disable-model-invocation: false
---

# Skill Builder

| Intent                             | Starting Point                                                    |
| :--------------------------------- | :---------------------------------------------------------------- |
| "I want to make a skill for X"     | [Interview and Draft](#interview-and-draft)                       |
| "Turn this workflow into a skill"  | Extract steps, confirm, then [Draft](#write-the-skillmd)          |
| "Help me improve my skill"         | [Improving the Skill](#improving-the-skill)                       |
| "My skill is inconsistent"         | Ask for bad-output example, then [Diagnose](#improving-the-skill) |
| "Build quickly, skip formal evals" | Draft directly, skip formal eval loop                             |

**Quick draft mode:** Draft immediately. Skip `evals/evals.json`, formal workspace, and baseline runs. Still enforce all NEVER items and frontmatter constraints. Propose 2-3 test prompts verbally at the end.

---

## NEVER List

- **NEVER** optimize description before logic is stable. Even if the user insists, confirm stable eval scores first.
- **NEVER** skip baseline runs — required for measuring added value. Even if the user insists, explain why and offer faster alternatives (fewer evals, parallel runs).
- **NEVER** overfit to test cases; prefer general logic over rigid constraints.
- **NEVER** use conversational filler; provide direct, imperative instructions.
- **NEVER** defer producing a SKILL.md when a constraint violation is detected (e.g., invalid name with spaces). Apply the correction inline, note it with one sentence, and produce the complete SKILL.md immediately without asking for confirmation.
- **NEVER** produce a SKILL.md with `disable-model-invocation: true` in the `skills:` preload list of another skill — that flag means the skill cannot be preloaded; attempting it silently fails.
- **NEVER** put multi-line prose paragraphs in a skill body — skills are scanned by the model under time pressure; use imperative bullets, tables, and code blocks only.

---

## Communication

- Use technical terms (eval, JSON, assertion) only if the user is familiar.
- Explain technical rationale (e.g., why baseline runs or assertions matter).
- Be concise.

---

## Creating a skill

### Interview and Draft

1. **Extract from conversation:**
   - Tools, step sequence, corrections.
   - Input/output formats, success criteria, edge cases.
2. **Research:** Check available MCPs for data/tools. Use subagents in parallel.
3. **Draft immediately:** Write `SKILL.md`. Mark uncertainties with `[USER TO CONFIRM: X]`.

**draft-immediately:** all 3 criteria met — annotate assumptions inline
**ask-first:** any criterion missing — ask targeted questions first

- [ ] Domain/purpose is clear
- [ ] At least one example trigger phrase is known
- [ ] Expected output format is known (even roughly)

For users new to skill-building, add one orienting sentence before the draft.

### Write the SKILL.md

**Before producing any SKILL.md, validate all fields:**

1. `name` — must be kebab-case (lowercase, digits, hyphens only), max 64 chars. If invalid (spaces, uppercase), convert immediately and note inline. Do not ask for confirmation.
2. `description` — must have no angle brackets (`<` or `>`), max 1024 chars.
3. **MANDATORY**: Dispatch a `general-purpose` subagent to audit the draft. Call `Agent(subagent_type: "general-purpose", description: "Audit SKILL.md prompt quality", prompt: "SCOPE: Review SKILL.md frontmatter and body for triggering effectiveness, clarity, and completeness. OBJECTIVE: Identify vague instructions, missing examples, or weak trigger phrases. CONTEXT: Skill name and description. CONSTRAINTS: Focus on language clarity and trigger phrase strength; do not evaluate logic. OUTPUT: JSON with fields {issues: [{severity, description, location}], pass: bool, summary: string}")`. Note findings and remediations.
4. Skill body — imperative form throughout. No "you should", "you might", "maybe".

Fill in these components based on the interview:

- **name**: Unique skill identifier. **Constraints:** kebab-case (lowercase, digits, hyphens), max 64 chars, no leading/trailing hyphens, no consecutive hyphens.
- **description**: When to trigger and what it does. This is the primary triggering mechanism. **Mandate:** Make descriptions "pushy" to ensure reliable triggering (e.g., "Use this whenever the user mentions X, Y, or Z, even if not explicitly requested"). **Constraints:** No angle brackets (`<` or `>`), max 1024 chars.
- **compatibility**: Tools/dependencies (optional).
- **Instructions**: The core logic.

### Skill Design Standards

#### Structure

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Deterministic/repetitive task code
    ├── references/ - Context-loaded docs
    └── assets/     - Output files (templates, icons)
```

#### Progressive Disclosure

1. **Metadata** (name + description) — Always in context.
2. **SKILL.md body** — Loaded on trigger (target: < 500 lines).
3. **Bundled resources** — Loaded as needed.

- Move details to `references/` if `SKILL.md` exceeds 500 lines.
- Use clear pointers to bundled files.
- Large reference files (>300 lines) require a Table of Contents.
- Organize multi-variant domains (e.g., AWS vs. GCP) into separate files in `references/`.

#### Writing Patterns

- **Imperative Form**: "Do X", not "You should do X".
- **Output Formats**: Define explicit structures (e.g., `# [Title]`, `## Summary`).
- **Examples**: Use clear Input/Output pairs.
- **File Editing**: Sequential edits only. One edit per turn per file.
- **Code Generation**: Output complete, functional blocks. No placeholders.

### Test Cases

1. Propose 2-3 realistic test prompts to the user.
2. Save to `evals/evals.json`. Omit assertions initially.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

**Required Reference:** Read `references/schemas.md` for full schema definitions.

## Running and Evaluating Test Cases

Follow this sequence. Do NOT use `/skill-test`.

**Workspace:** `<skill-name>-workspace/iteration-<N>/eval-<ID>/` (relative to CWD, e.g., `./skill-builder-workspace/iteration-1/eval-0/`). Output files go under `run-N/outputs/` — not directly under the config directory.

### 0. Setup Workspace (Recommended)

```bash
python scripts/init_eval.py --skill-name <name> --eval-id <ID> --prompt "<prompt>"
```

### 1. Spawn Runs (With-Skill & Baseline)

Spawn two subagents per test case in parallel:

1. **With-Skill**: Point to current skill path.
2. **Baseline**:
   - **New Skill**: No skill path (pure model).
   - **Improve Mode**: Point to a snapshot of the previous skill version.

**Task (per subagent):**

- **Task:** `<eval prompt>`
- **Save outputs to:** `<workspace>/[with_skill|without_skill|old_skill]/outputs/`
- **Outputs to save:** Specific relevant artifacts.

**Metadata:** Write `eval_metadata.json` for each test case.

```json
{ "eval_id": 0, "eval_name": "descriptive-name", "prompt": "Prompt", "assertions": [] }
```

### 2. Draft Assertions

While runs execute:

1. Draft objectively verifiable assertions for each test case.
2. Update `evals/evals.json` and `eval_metadata.json`.
3. Explain to the user what these verify.

### 3. Capture Timing Data

Save `total_tokens` and `duration_ms` from the completion notification to `timing.json` in the run directory.

```json
{ "total_tokens": 123, "duration_ms": 456, "total_duration_seconds": 0.456 }
```

### 4. Grade, Aggregate, and Review

1. **Grade**: Dispatch a `general-purpose` subagent to evaluate assertions against outputs. Call `Agent(subagent_type: "general-purpose", description: "Grade eval results", prompt: "SCOPE: Evaluate test case outputs against recorded assertions. OBJECTIVE: Determine pass/fail for each assertion with evidence. CONTEXT: Assertions list and actual outputs. CONSTRAINTS: Objective scoring only; boolean pass/fail per assertion. OUTPUT: JSON with {assertions_evaluated: int, passed: int, failed: int, details: [{assertion, passed: bool, evidence}]}")`. Save to `grading.json`.
2. **Aggregate**:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
3. **Analyze**: Dispatch a `general-purpose` subagent to identify patterns and outliers. Call `Agent(subagent_type: "general-purpose", description: "Analyze skill quality", prompt: "SCOPE: Analyze eval results for patterns, outliers, and statistical significance. OBJECTIVE: Compute pass-rate delta and determine if improvement is significant. CONTEXT: Grading results and baseline comparison. CONSTRAINTS: Apply 95% CI significance threshold; reject deltas where CI includes 0. OUTPUT: JSON with {pass_rate_with_skill: float, pass_rate_baseline: float, delta: float, pass_rate_significant: bool, patterns: [str], recommendations: [str]}")`. Report the pass-rate delta WITH its significance verdict (`pass_rate_significant`); never present a delta as "the skill helps" if the 95% CI includes 0 — increase runs first.
4. **Launch Viewer**:
   ```bash
   python -u "<skill-builder-dir>/eval-viewer/generate_review.py" \
     "<workspace>/iteration-N" \
     --skill-name "my-skill" \
     --benchmark "<workspace>/iteration-N/benchmark.json" \
     [--previous-workspace "<workspace>/iteration-N-1"] \
     > /tmp/viewer.log 2>&1 &
   ```
5. **Report**: Provide the URL as a clickable link.

### 5. Read Feedback

Read `feedback.json` after user review. Focus on specific critiques.

---

## Improving the Skill

1. **Diagnose**: Identify root causes (e.g., missing template). Propose specific fixes.
2. **Generalize**: Avoid overfitting. Bundle repetitive logic into `scripts/`.
3. **Refine Prompt**: Remove unproductive steps. State the _why_ for generalization.
4. **Iterate**: Apply fixes and rerun the full test cycle in a new `iteration-<N+1>/` directory.

---

## Advanced: Blind Comparison

For rigorous testing, invoke two agents in sequence:

1. Call `Agent(subagent_type: "general-purpose", description: "Compare eval results", prompt: "SCOPE: Perform blind A/B comparison of with-skill vs baseline eval outputs. OBJECTIVE: Identify which outputs are better, worse, or equivalent without knowing assignment. CONTEXT: Paired outputs from both conditions. CONSTRAINTS: Blinded scoring only; no confidence score, only preference. OUTPUT: JSON with {comparisons: [{better_output, worse_output, reasoning}], overall_preference: string}")`.

2. Call `Agent(subagent_type: "general-purpose", description: "Analyze skill quality", prompt: "SCOPE: Synthesize comparison and grading results. OBJECTIVE: Determine overall significance of skill improvement. CONTEXT: Blind comparison and grading results. CONSTRAINTS: Use statistical evidence, not anecdotes. OUTPUT: JSON with {recommendation: string, significance_verdict: bool}")` .

---

## Description Optimization

Wait until logic is stable.

1. **Eval Set**: Generate 20 queries (10 should-trigger, 10 should-not-trigger).
2. **User Review**: Confirm set with user. Save to `<workspace>/trigger-eval.json`.
3. **Optimize**:
   ```bash
   python '<skill-dir>/scripts/run_loop.py' \
     --eval-set <workspace>/trigger-eval.json \
     --skill-path <path-to-skill> \
     --model <current-session-model-id> \
     --max-iterations 5 --verbose
   ```
4. **Apply**: Update `SKILL.md` frontmatter with `best_description`.

---

## Packaging

If `present_files` is available:

```bash
python '<skill-dir>/scripts/package_skill.py' <path/to/skill-folder>
```

---

## Environment Notes

### Claude.ai

- Run test cases serially.
- Review results inline.
- Skip description optimization/blind comparison.

### Cowork / Headless

- **MANDATORY: Read `references/cowork.md`**.
- Use `--static` for viewer. Headless environments cannot serve the eval viewer — `--static` generates a standalone HTML file that opens directly without a server.

---

## Reference Map

- `references/schemas.md`: JSON schema definitions. Grading, blind-comparison, and analysis criteria are embedded directly in the `Agent()` prompts above (Sections 4 and "Advanced: Blind Comparison").
- `references/cowork.md`: Headless environment workflow.
