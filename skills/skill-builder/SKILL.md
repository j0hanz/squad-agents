---
name: skill-builder
description: |
  Build, test, and iteratively improve Claude Agent Skills — from first draft through description optimization and benchmarked iteration. Use this skill whenever the user says things like "I want to make a skill for X", "help me build a skill", "my skill isn't triggering / isn't working", "turn this workflow into a skill", "run evals on my skill", "improve my existing skill", or "optimize my skill's description". Also invoke when someone hands you a SKILL.md and asks for feedback, or when you're designing a new skill from scratch and want a rigorous testing loop.
disable-model-invocation: false
---

# Skill Builder

Progress the user through the skill development lifecycle:

| Intent | Starting Point |
| :--- | :--- |
| "I want to make a skill for X" | [Interview and Draft](#interview-and-draft) |
| "Turn this workflow into a skill" | Extract steps, confirm, then [Draft](#write-the-skillmd) |
| "Help me improve my skill" | [Diagnose before rewriting](#diagnose-before-rewriting) |
| "My skill is inconsistent" | Ask for bad-output example, then [Diagnose](#diagnose-before-rewriting) |
| "Just vibe with me (no evals)" | Draft directly, skip formal eval loop |

---

## NEVER List

- **NEVER** optimize description before logic is stable.
- **NEVER** skip baseline runs — required for measuring added value.
- **NEVER** overfit to test cases; prefer general logic over rigid constraints.
- **NEVER** use conversational filler; provide direct, imperative instructions.

---

## Communicating with the User

- Use technical terms (eval, JSON, assertion) only if the user is familiar.
- Explain technical rationale (e.g., why baseline runs or assertions matter).
- Err toward concise explanation.

---

## Creating a skill

### Interview and Draft

1. **Extract from conversation:**
   - Tools, step sequence, corrections.
   - Input/output formats, success criteria, edge cases.
2. **Research:** Check available MCPs for data/tools. Use subagents in parallel.
3. **Draft immediately:** Write `SKILL.md`. Mark uncertainties with `[USER TO CONFIRM: X]`.

**When to ask vs. draft:** If the user's message provides all three of the following, draft immediately and annotate any assumptions inline. If any is missing, ask targeted questions first.

- [ ] Domain/purpose is clear
- [ ] At least one example trigger phrase is known
- [ ] Expected output format is known (even roughly)

For users who identify as new to skill-building, add one orienting sentence before the draft.

### Write the SKILL.md

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

**Guidelines:**
- If `SKILL.md` exceeds 500 lines, move details to `references/`.
- Use clear pointers to bundled files.
- Large reference files (>300 lines) require a Table of Contents.
- Organize multi-variant domains (e.g., AWS vs. GCP) into separate files in `references/`.

#### Writing Patterns

- **Imperative Form**: Use "Do X", not "You should do X".
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

**Workspace:** `<skill-name>-workspace/iteration-<N>/eval-<ID>/`

### 0. Setup Workspace (Recommended)
Run the initialization script to scaffold the directory structure and metadata:
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

Upon task completion, save `total_tokens` and `duration_ms` from the notification to `timing.json` in the run directory.
```json
{ "total_tokens": 123, "duration_ms": 456, "total_duration_seconds": 0.456 }
```

### 4. Grade, Aggregate, and Review

1. **Grade**: **MANDATORY: Read `agents/grader.md`**. evaluate assertions against outputs. Save to `grading.json`.
2. **Aggregate**:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
3. **Analyze**: **MANDATORY: Read `agents/analyzer.md`**. Identify patterns and outliers.
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
3. **Refine Prompt**: Remove unproductive steps. State the *why* for generalization.
4. **Iterate**: Apply fixes and rerun the full test cycle in a new `iteration-<N+1>/` directory.

---

## Advanced: Blind Comparison

For rigorous testing: **MANDATORY: Read `agents/comparator.md` and `agents/analyzer.md`**.

---

## Description Optimization

Wait until logic is stable.

1. **Eval Set**: Generate 20 queries (10 should-trigger, 10 should-not-trigger).
2. **User Review**: Confirm set with user. Save to `<workspace>/trigger-eval.json`.
3. **Optimize**:
   ```bash
   python -m scripts.run_loop \
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
python -m scripts.package_skill <path/to/skill-folder>
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

- `agents/grader.md`: Grading pass/fail criteria.
- `agents/comparator.md`: Blind A/B analysis.
- `agents/analyzer.md`: Benchmark data interpretation.
- `references/schemas.md`: JSON schema definitions.
- `references/cowork.md`: Headless environment workflow.
