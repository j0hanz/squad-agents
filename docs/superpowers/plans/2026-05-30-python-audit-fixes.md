# Python Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all confirmed bugs, crashes, and quality issues from the May 2026 Python audit of the agent-dev plugin's 60 source files.

**Architecture:** 13 tasks in three groups — (A) HIGH: runtime crashes confirmed by execution that block CI; (B) MEDIUM: contract and configuration correctness; (C) LOW: code quality. Each task leaves the test suite green. The audit ran on Python 3.14, `utf8_mode=0`, `stdout=cp1252` — making the encoding fixes non-optional on this machine.

**Tech Stack:** Python 3.14 (supports 3.10+), pytest 9.x, stdlib `dataclasses.replace`. No new dependencies. PyYAML is an existing optional dep guarded throughout with `try: import yaml`.

**Baseline test run (before any fixes):** `4 failed, 142 passed`

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ -q -o addopts=""
```

---

## File Map

| Action | Path                                                              | Reason                                                |
| ------ | ----------------------------------------------------------------- | ----------------------------------------------------- |
| Modify | `skills/agent-development/scripts/audit.py`                       | FrozenInstanceError — replace `finding.path = p`      |
| Modify | `skills/agent-development/scripts/lib/agent_parser.py`            | Let `FileNotFoundError` propagate                     |
| Create | `skills/lib/__init__.py`                                          | Package root for shared `spec_parser`                 |
| Create | `skills/lib/spec_parser.py`                                       | Missing module imported by create-plan / create-specs |
| Modify | `skills/skill-builder/scripts/generate_report.py`                 | `encoding="utf-8"` + hoist nested fns                 |
| Modify | `skills/skill-builder/scripts/run_loop.py`                        | `encoding="utf-8"` on 6 write_text calls              |
| Modify | `skills/skill-builder/scripts/improve_description.py`             | `encoding="utf-8"` on write_text                      |
| Modify | `skills/skill-builder/scripts/run_eval.py`                        | `encoding="utf-8"` on read_text                       |
| Modify | `skills/skill-builder/scripts/aggregate_benchmark.py`             | `encoding="utf-8"` on open()                          |
| Modify | `skills/skill-builder/scripts/utils.py`                           | `encoding="utf-8"` on read_text                       |
| Modify | `skills/skill-builder/scripts/quick_validate.py`                  | `encoding="utf-8"` on read_text                       |
| Modify | `skills/skill-builder/scripts/package_skill.py`                   | sys.path fix + ASCII for emoji                        |
| Modify | `skills/agents-maintainer/scripts/run.py`                         | ASCII for ❌/✅ + fix FAIL:WARN:                      |
| Modify | `skills/agent-development/scripts/simulate.py`                    | ASCII for ✅/⚠️/❌                                    |
| Modify | `skills/spec-driven-development/scripts/diagnose_dependencies.py` | ASCII for ✓/✗                                         |
| Modify | `skills/agent-development/scripts/telemetry_dashboard.py`         | `encoding="utf-8"` on open()                          |
| Modify | `skills/agent-development/scripts/visualize_policy.py`            | `encoding="utf-8"` on open()                          |
| Modify | `skills/skill-builder/eval-viewer/generate_review.py`             | `encoding="utf-8"` on bare read_text                  |
| Modify | `skills/github-automation/scripts/lint.py`                        | Multi-line `run:` injection tracking                  |
| Modify | `skills/agent-development/scripts/cost.py`                        | Import constants; add type hint                       |
| Modify | `skills/agent-development/scripts/diff.py`                        | Import constants; add type hint                       |
| Modify | `skills/agent-development/scripts/compile.py`                     | Add `AgentSpec` type hints                            |
| Modify | `skills/agent-development/scripts/recommend.py`                   | Add `AgentSpec` type hint                             |
| Create | `skills/skill-builder/tests/__init__.py`                          | Make pytest discover the package                      |
| Create | `skills/skill-builder/tests/conftest.py`                          | sys.path for `from scripts.X import Y`                |
| Create | `skills/skill-builder/tests/test_aggregate_benchmark.py`          | Smoke tests                                           |
| Create | `skills/skill-builder/tests/test_generate_report.py`              | Smoke tests                                           |
| Modify | `.simulate/observer.py`                                           | Wrap in main() + error handling                       |
| Modify | `skills/agent-development/scripts/.simulate/observer.py`          | Wrap in main() + error handling                       |

---

## GROUP A — HIGH: Runtime Crashes

---

### Task 1: Fix FrozenInstanceError in audit.py

`Finding` is `frozen=True` but `audit()` assigns `finding.path = p` at lines 268 and 273.
This crashes for any cc_subagent or skill-composition finding, breaking 3 tests.

**Files:**

- Modify: `skills/agent-development/scripts/audit.py`
- Test: `skills/agent-development/scripts/tests/test_audit.py` (existing — currently FAILING)

- [ ] **Step 1: Verify the 3 tests are currently red**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/test_audit.py -k "ccsa001 or ccsa002 or skill001" -v -o addopts=""
```

Expected output contains: `FAILED ... test_ccsa001 ... FAILED ... test_ccsa002 ... FAILED ... test_skill001`

- [ ] **Step 2: Add `import dataclasses` to audit.py**

Open `skills/agent-development/scripts/audit.py`. The existing imports block at lines 8–19 currently has no `dataclasses` import. Add it:

```python
from __future__ import annotations
import argparse
import dataclasses
import re
import sys
from pathlib import Path
from typing import List, Dict, Any
```

- [ ] **Step 3: Replace the two frozen-mutation sites with `dataclasses.replace`**

Replace lines 264–274 in `skills/agent-development/scripts/audit.py`:

```python
    # Detect agent kind and route to subagent-specific checks
    kind = detect_agent_kind(spec.raw_frontmatter)
    if kind == "cc_subagent":
        for finding in check_cc_subagent_specific(
            spec.raw_frontmatter, spec.system_prompt
        ):
            findings.append(dataclasses.replace(finding, path=p))

    # Append skill composition check to findings (works for both managed and cc_subagent)
    for finding in check_skill_composition(spec.raw_frontmatter, spec.system_prompt):
        findings.append(dataclasses.replace(finding, path=p))
```

- [ ] **Step 4: Run the 3 previously-failing tests**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/test_audit.py -k "ccsa001 or ccsa002 or skill001" -v -o addopts=""
```

Expected: all 3 PASS

- [ ] **Step 5: Run the full test suite to confirm no regression**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ -q -o addopts=""
```

Expected: `1 failed, 144 passed` (the `test_missing_file_raises` failure remains — fixed in Task 2)

- [ ] **Step 6: Commit**

```bash
git add skills/agent-development/scripts/audit.py
git commit -m "fix(audit): replace frozen Finding mutation with dataclasses.replace

FrozenInstanceError crashed audit.py on any cc_subagent or skill-composition
finding. dataclasses.replace() creates a new instance instead of mutating.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 2: Fix FileNotFoundError contract in agent_parser.py

`parse_agent()` documents `Raises: FileNotFoundError` but catches `OSError` (which includes `FileNotFoundError`) and re-raises as `ParseError`. `test_missing_file_raises` asserts `FileNotFoundError` but gets `ParseError`.

**Files:**

- Modify: `skills/agent-development/scripts/lib/agent_parser.py`
- Test: `skills/agent-development/scripts/tests/test_agent_parser.py` (existing — currently FAILING)

- [ ] **Step 1: Verify the test is currently red**

```bash
.venv/Scripts/python.exe -m pytest "skills/agent-development/scripts/tests/test_agent_parser.py::TestParseAgent::test_missing_file_raises" -v -o addopts=""
```

Expected: `FAILED` — `ParseError` raised instead of `FileNotFoundError`

- [ ] **Step 2: Fix the except clause to let FileNotFoundError propagate**

In `skills/agent-development/scripts/lib/agent_parser.py`, replace lines 74–77:

```python
    try:
        content = path_obj.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    except (OSError, UnicodeDecodeError) as e:
        raise ParseError(f"Failed to read agent file at {path}: {e}") from e
```

- [ ] **Step 3: Run the fixed test**

```bash
.venv/Scripts/python.exe -m pytest "skills/agent-development/scripts/tests/test_agent_parser.py::TestParseAgent::test_missing_file_raises" -v -o addopts=""
```

Expected: `PASSED`

- [ ] **Step 4: Run the full suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ -q -o addopts=""
```

Expected: `0 failed, 146 passed`

- [ ] **Step 5: Commit**

```bash
git add skills/agent-development/scripts/lib/agent_parser.py
git commit -m "fix(agent_parser): let FileNotFoundError propagate from parse_agent

The docstring promised FileNotFoundError for missing files but the broad
OSError catch re-raised it as ParseError, breaking the documented contract.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 3: Create missing spec_parser module

`skills/create-plan/scripts/generate_plan.py` and `skills/create-specs/scripts/validate_spec.py` both do:

```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from spec_parser import parse_spec
```

`parent.parent.parent / "lib"` resolves to `skills/lib/`, which doesn't exist. Both scripts crash with `ModuleNotFoundError` on import.

**Files:**

- Create: `skills/lib/__init__.py`
- Create: `skills/lib/spec_parser.py`

- [ ] **Step 1: Confirm both scripts are currently broken**

```bash
.venv/Scripts/python.exe skills/create-plan/scripts/generate_plan.py --help 2>&1 | tail -3
.venv/Scripts/python.exe skills/create-specs/scripts/validate_spec.py --help 2>&1 | tail -3
```

Expected: both print `ModuleNotFoundError: No module named 'spec_parser'`

- [ ] **Step 2: Create the `skills/lib/` package root**

Create `skills/lib/__init__.py` (empty file):

```python

```

- [ ] **Step 3: Create `skills/lib/spec_parser.py`**

```python
"""Parse a spec.md document into a SpecDocument.

Shared by skills/create-plan and skills/create-specs scripts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SpecDocument:
    """Parsed representation of a spec markdown file."""

    sections: dict[str, str] = field(default_factory=dict)
    reqs: set[str] = field(default_factory=set)
    acs: set[str] = field(default_factory=set)
    vals: set[str] = field(default_factory=set)
    cons: set[str] = field(default_factory=set)
    raw_lines: list[str] = field(default_factory=list)


_HEADING_RE = re.compile(r"^(#+)\s+(?:\d+\.\s+)?(.+)$")
_REQ_RE = re.compile(r"\b(REQ|SEC|PERF|COMP)-\d+\b")
_AC_RE = re.compile(r"\bAC-\d+\b")
_VAL_RE = re.compile(r"\bVAL-\d+\b")
_CON_RE = re.compile(r"\bCON-\d+\b")


def parse_spec(path: str | Path) -> SpecDocument:
    """Parse a spec markdown file.

    Args:
        path: Path to the spec .md file.

    Returns:
        SpecDocument with sections, reqs, acs, vals, cons, raw_lines populated.

    Raises:
        FileNotFoundError: If the path doesn't exist.
        OSError: If the file cannot be read.
    """
    content = Path(path).read_text(encoding="utf-8")
    lines = content.splitlines()

    doc = SpecDocument(raw_lines=lines)
    current_section: str | None = None
    section_lines: list[str] = []

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            if current_section is not None:
                doc.sections[current_section] = "\n".join(section_lines).strip()
            current_section = m.group(2).strip()
            section_lines = []
        elif current_section is not None:
            section_lines.append(line)

        for rm in _REQ_RE.finditer(line):
            doc.reqs.add(rm.group(0))
        for am in _AC_RE.finditer(line):
            doc.acs.add(am.group(0))
        for vm in _VAL_RE.finditer(line):
            doc.vals.add(vm.group(0))
        for cm in _CON_RE.finditer(line):
            doc.cons.add(cm.group(0))

    if current_section is not None:
        doc.sections[current_section] = "\n".join(section_lines).strip()

    return doc
```

- [ ] **Step 4: Verify both scripts now import correctly**

```bash
.venv/Scripts/python.exe skills/create-plan/scripts/generate_plan.py --help 2>&1 | tail -3
.venv/Scripts/python.exe skills/create-specs/scripts/validate_spec.py --help 2>&1 | tail -3
```

Expected: both print usage/help text (not a traceback)

- [ ] **Step 5: Smoke-test spec parsing end-to-end**

```bash
.venv/Scripts/python.exe - <<'EOF'
import sys
sys.path.insert(0, "skills/lib")
from spec_parser import parse_spec, SpecDocument
from pathlib import Path
import tempfile, textwrap

spec_text = textwrap.dedent("""
    # Test Spec
    ## 1. Goal
    Build a thing.
    ## 2. Requirements
    - REQ-001: Must work.
    - SEC-001: Must be secure.
    ## 3. Constraints
    - CON-001: No new deps.
    ## 6. Acceptance Criteria & Validation
    - AC-001: Output is correct.
    - VAL-001: Run pytest.
""")

with tempfile.NamedTemporaryFile(suffix=".md", mode="w", encoding="utf-8", delete=False) as f:
    f.write(spec_text)
    tmp = f.name

doc = parse_spec(tmp)
assert "Goal" in doc.sections, f"sections: {doc.sections.keys()}"
assert "REQ-001" in doc.reqs, f"reqs: {doc.reqs}"
assert "SEC-001" in doc.reqs, f"reqs: {doc.reqs}"
assert "CON-001" in doc.cons, f"cons: {doc.cons}"
assert "AC-001" in doc.acs, f"acs: {doc.acs}"
assert "VAL-001" in doc.vals, f"vals: {doc.vals}"
print("PASS: spec_parser works correctly")
EOF
```

Expected: `PASS: spec_parser works correctly`

- [ ] **Step 6: Run the full test suite (no regression)**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ -q -o addopts=""
```

Expected: `0 failed, 146 passed`

- [ ] **Step 7: Commit**

```bash
git add skills/lib/__init__.py skills/lib/spec_parser.py
git commit -m "fix(spec_parser): create missing shared module for create-plan and create-specs

Both generate_plan.py and validate_spec.py imported from skills/lib/spec_parser.py
which did not exist, causing ModuleNotFoundError on import.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 4: Fix UnicodeEncodeError — file writes and reads

On Windows with `utf8_mode=0` (default), `write_text()` and `open()` without `encoding=` use cp1252. Files that write HTML containing ✓/✗, or JSON with emoji, crash with `UnicodeEncodeError`.

This task fixes all missing `encoding="utf-8"` on file I/O across the codebase. Console glyph crashes are fixed in Task 5.

**Files to modify (all file read/write sites):**

- `skills/skill-builder/scripts/generate_report.py` (line 350)
- `skills/skill-builder/scripts/run_loop.py` (lines 196, 344, 381, 385, 391)
- `skills/skill-builder/scripts/improve_description.py` (line 207)
- `skills/skill-builder/scripts/run_eval.py` (line 268)
- `skills/skill-builder/scripts/aggregate_benchmark.py` (lines 386, 392)
- `skills/skill-builder/scripts/utils.py` (line 9)
- `skills/skill-builder/scripts/quick_validate.py` (line 57)
- `skills/agent-development/scripts/telemetry_dashboard.py` (line 28)
- `skills/agent-development/scripts/visualize_policy.py` (line 42)
- `skills/skill-builder/eval-viewer/generate_review.py` (line 212)

- [ ] **Step 1: Confirm the crash is real**

```bash
.venv/Scripts/python.exe - <<'EOF'
from pathlib import Path
import tempfile
p = Path(tempfile.gettempdir()) / "enc_test.html"
try:
    p.write_text("<td>✓</td>")
    print("UNEXPECTED: no error")
except UnicodeEncodeError as e:
    print(f"CONFIRMED CRASH: {e}")
EOF
```

Expected: `CONFIRMED CRASH: 'charmap' codec can't encode character '✓'`

- [ ] **Step 2: Fix `skills/skill-builder/scripts/generate_report.py` line 350**

Change:

```python
        Path(args.output).write_text(html_output)
```

To:

```python
        Path(args.output).write_text(html_output, encoding="utf-8")
```

- [ ] **Step 3: Fix `skills/skill-builder/scripts/run_loop.py` — 6 write_text calls**

Line 196 — live report partial write:

```python
            live_report_path.write_text(
                generate_html(partial_output, auto_refresh=True, skill_name=name),
                encoding="utf-8",
            )
```

Line 344 — initial placeholder HTML:

```python
        live_report_path.write_text(
            "<html><body><h1>Starting optimization loop...</h1><meta http-equiv='refresh' content='5'></body></html>",
            encoding="utf-8",
        )
```

Line 381 — results JSON:

```python
        (results_dir / "results.json").write_text(json_output, encoding="utf-8")
```

Line 385 — final report:

```python
        live_report_path.write_text(
            generate_html(output, auto_refresh=False, skill_name=name),
            encoding="utf-8",
        )
```

Line 391 — results dir report:

```python
        (results_dir / "report.html").write_text(
            generate_html(output, auto_refresh=False, skill_name=name),
            encoding="utf-8",
        )
```

- [ ] **Step 4: Fix `skills/skill-builder/scripts/improve_description.py` line 207**

Change:

```python
        log_file.write_text(json.dumps(transcript, indent=2))
```

To:

```python
        log_file.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
```

- [ ] **Step 5: Fix `skills/skill-builder/scripts/run_eval.py` line 268**

Change:

```python
    eval_set = json.loads(Path(args.eval_set).read_text())
```

To:

```python
    eval_set = json.loads(Path(args.eval_set).read_text(encoding="utf-8"))
```

- [ ] **Step 6: Fix `skills/skill-builder/scripts/aggregate_benchmark.py` — two open() calls**

Lines 386–387:

```python
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(benchmark, f, indent=2)
```

Lines 392–393:

```python
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(markdown)
```

- [ ] **Step 7: Fix `skills/skill-builder/scripts/utils.py` line 9**

Change:

```python
    content = (skill_path / "SKILL.md").read_text()
```

To:

```python
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")
```

- [ ] **Step 8: Fix `skills/skill-builder/scripts/quick_validate.py` line 57**

Change:

```python
    content = skill_md.read_text()
```

To:

```python
    content = skill_md.read_text(encoding="utf-8")
```

- [ ] **Step 9: Fix `skills/agent-development/scripts/telemetry_dashboard.py` line 28**

Change:

```python
    with open(TELEMETRY_FILE, "r") as f:
```

To:

```python
    with open(TELEMETRY_FILE, "r", encoding="utf-8") as f:
```

- [ ] **Step 10: Fix `skills/agent-development/scripts/visualize_policy.py` line 42**

Change:

```python
        with open(policy_file, "r") as f:
```

To:

```python
        with open(policy_file, "r", encoding="utf-8") as f:
```

- [ ] **Step 11: Fix `skills/skill-builder/eval-viewer/generate_review.py` line 212**

The text branch currently uses `path.read_text(errors="replace")` without `encoding=`. Change:

```python
        try:
            content = path.read_text(errors="replace")
```

To:

```python
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
```

- [ ] **Step 12: Verify write_text no longer crashes**

```bash
.venv/Scripts/python.exe - <<'EOF'
from pathlib import Path
import tempfile
p = Path(tempfile.gettempdir()) / "enc_test2.html"
p.write_text("<td>✓</td>", encoding="utf-8")
assert p.read_text(encoding="utf-8") == "<td>✓</td>"
print("PASS: write_text with encoding='utf-8' works")
EOF
```

Expected: `PASS: write_text with encoding='utf-8' works`

- [ ] **Step 13: Run the full test suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ -q -o addopts=""
```

Expected: `0 failed, 146 passed`

- [ ] **Step 14: Commit**

```bash
git add \
  skills/skill-builder/scripts/generate_report.py \
  skills/skill-builder/scripts/run_loop.py \
  skills/skill-builder/scripts/improve_description.py \
  skills/skill-builder/scripts/run_eval.py \
  skills/skill-builder/scripts/aggregate_benchmark.py \
  skills/skill-builder/scripts/utils.py \
  skills/skill-builder/scripts/quick_validate.py \
  skills/agent-development/scripts/telemetry_dashboard.py \
  skills/agent-development/scripts/visualize_policy.py \
  skills/skill-builder/eval-viewer/generate_review.py
git commit -m "fix(encoding): add encoding='utf-8' to all bare file reads and writes

On Windows with default cp1252 locale, write_text() and open() without
encoding= crash when content contains non-ASCII characters (HTML reports,
YAML, JSON with unicode). Adds explicit encoding='utf-8' to 10 files.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 5: Fix UnicodeEncodeError — console glyph output

Five files print emoji or Unicode glyphs (✓, ✗, ❌, ✅, 📦, 🔍) directly to stdout. On this machine (`stdout=cp1252`), these raise `UnicodeEncodeError` when output is piped.

**Files to modify:**

- `skills/agents-maintainer/scripts/run.py` (lines 537, 539)
- `skills/agent-development/scripts/simulate.py` (lines 244–249)
- `skills/skill-builder/scripts/package_skill.py` (lines 60, 62, 71, 72, 77, 103, 128)
- `skills/spec-driven-development/scripts/diagnose_dependencies.py` (lines 83, 89, 99, 103)

- [ ] **Step 1: Confirm the crash**

```bash
.venv/Scripts/python.exe -c "print('✅ done')" | cat
```

Expected: `UnicodeEncodeError: 'charmap' codec can't encode character '✅'`

- [ ] **Step 2: Fix `skills/agents-maintainer/scripts/run.py` lines 537–539**

Replace:

```python
        print("❌ Audit failed with one or more errors.")
        return 1
    print("✅ Audit passed. Plugin is healthy.")
```

With:

```python
        print("FAIL: Audit failed with one or more errors.")
        return 1
    print("PASS: Audit passed. Plugin is healthy.")
```

- [ ] **Step 3: Fix FAIL:WARN: prefix bug in `run.py` (same file, same commit)**

The `validate-skills` case at line 609–615 blindly prefixes `FAIL:` to all errors, producing `FAIL: WARN: ...` for length warnings. Replace:

```python
        case "validate-skills":
            valid, errors = validate_skill_files(root / "skills")
            for err in errors:
                print(f"FAIL: {err}", file=sys.stderr)
            if valid:
                print("PASS: Skills are valid.")
            return 0 if valid else 1
```

With:

```python
        case "validate-skills":
            valid, errors = validate_skill_files(root / "skills")
            for err in errors:
                prefix = "WARN" if err.startswith("WARN") else "FAIL"
                print(f"{prefix}: {err}", file=sys.stderr)
            if valid:
                print("PASS: Skills are valid.")
            return 0 if valid else 1
```

- [ ] **Step 4: Verify run.py validate-skills no longer prints FAIL: WARN:**

```bash
.venv/Scripts/python.exe skills/agents-maintainer/scripts/run.py validate-skills 2>&1 | head -5
```

Expected: lines like `WARN: agent-development/SKILL.md is long (>150 lines)` (not `FAIL: WARN: ...`)

- [ ] **Step 5: Fix `skills/agent-development/scripts/simulate.py` lines 244–249**

Replace:

```python
            status = (
                "✅"
                if summary["pass_rate"] == 1.0
                else "⚠️"
                if summary["pass_rate"] > 0
                else "❌"
            )
            print(
                f"- {status} **{case_id}**: {summary['pass_rate'] * 100:.0f}% pass "
```

With:

```python
            status = (
                "PASS"
                if summary["pass_rate"] == 1.0
                else "PARTIAL"
                if summary["pass_rate"] > 0
                else "FAIL"
            )
            print(
                f"- [{status}] **{case_id}**: {summary['pass_rate'] * 100:.0f}% pass "
```

- [ ] **Step 6: Fix `skills/skill-builder/scripts/package_skill.py`**

Replace all emoji with ASCII equivalents:

Line 60: `print(f"❌ Error: Skill folder not found: {skill_path}")` → `print(f"ERROR: Skill folder not found: {skill_path}")`

Line 62: `print(f"❌ Error: Path is not a directory: {skill_path}")` → `print(f"ERROR: Path is not a directory: {skill_path}")`

Line 71: `print("🔍 Validating skill...")` → `print("Validating skill...")`

Line 72: `print(f"❌ Validation failed: {message}")` → `print(f"ERROR: Validation failed: {message}")`

Line 77: `print(f"✅ {message}\n")` → `print(f"OK: {message}\n")`

Line 103: `print(f"✅ Successfully packaged skill to: {skill_filename}")` → `print(f"OK: Successfully packaged skill to: {skill_filename}")`

Line 128: `print(f"📦 Packaging skill: {skill_path}")` → `print(f"Packaging skill: {skill_path}")`

- [ ] **Step 7: Fix `skills/spec-driven-development/scripts/diagnose_dependencies.py`**

Line 83: `print(f"[✗ ERROR] {name}")` → `print(f"[ERROR] {name}")`

Line 89: `status = "✓ OK" if present else "✗ MISSING"` → `status = "OK" if present else "MISSING"`

Line 99: `print("✓ All prerequisites present. Ready to use spec-driven-development.")` → `print("OK: All prerequisites present. Ready to use spec-driven-development.")`

Line 103: `print("✗ Some prerequisites are missing. Fix them above, then retry.")` → `print("FAIL: Some prerequisites are missing. Fix them above, then retry.")`

- [ ] **Step 8: Confirm no more glyph printing in these files**

```bash
grep -nE '[✓✗❌✅⚠️📦🔍]' \
  skills/agents-maintainer/scripts/run.py \
  skills/agent-development/scripts/simulate.py \
  skills/skill-builder/scripts/package_skill.py \
  skills/spec-driven-development/scripts/diagnose_dependencies.py
```

Expected: no output (grep finds nothing)

- [ ] **Step 9: Confirm piped output no longer crashes**

```bash
.venv/Scripts/python.exe skills/agents-maintainer/scripts/run.py validate-skills 2>&1 | cat | tail -3
```

Expected: prints `PASS: Skills are valid.` without UnicodeEncodeError

- [ ] **Step 10: Run the full test suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ -q -o addopts=""
```

Expected: `0 failed, 146 passed`

- [ ] **Step 11: Commit**

```bash
git add \
  skills/agents-maintainer/scripts/run.py \
  skills/agent-development/scripts/simulate.py \
  skills/skill-builder/scripts/package_skill.py \
  skills/spec-driven-development/scripts/diagnose_dependencies.py
git commit -m "fix(encoding): replace emoji/glyph console output with ASCII

On Windows cp1252, printing Unicode glyphs to a pipe raises UnicodeEncodeError.
Replaced all ✅/❌/✓/✗/📦/🔍 in print() calls with ASCII PASS/FAIL/OK/ERROR.
Also fixed FAIL:WARN: double-prefix bug in run.py validate-skills branch.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## GROUP B — MEDIUM: Contract and Configuration Correctness

---

### Task 6: Fix skill-builder test configuration — create missing test directory

`pyproject.toml` lists `skills/skill-builder/tests/` in `testpaths`. This directory does not exist. `npm run test:python` fails with "file or directory not found" and ~2,000 lines of skill-builder scripts have zero coverage.

**Files:**

- Create: `skills/skill-builder/tests/__init__.py`
- Create: `skills/skill-builder/tests/conftest.py`
- Create: `skills/skill-builder/tests/test_aggregate_benchmark.py`
- Create: `skills/skill-builder/tests/test_generate_report.py`

- [ ] **Step 1: Confirm pytest currently errors on the missing path**

```bash
.venv/Scripts/python.exe -m pytest skills/skill-builder/tests/ -q -o addopts="" 2>&1 | head -5
```

Expected: `ERROR: file or directory not found: skills/skill-builder/tests/`

- [ ] **Step 2: Create `skills/skill-builder/tests/__init__.py`** (empty)

- [ ] **Step 3: Create `skills/skill-builder/tests/conftest.py`**

```python
import sys
from pathlib import Path

# Needed because skill-builder scripts use "from scripts.X import Y"
# which requires the skill-builder root on sys.path.
sys.path.insert(0, str(Path(__file__).parent.parent))
```

- [ ] **Step 4: Create `skills/skill-builder/tests/test_aggregate_benchmark.py`**

```python
import pytest
from scripts.aggregate_benchmark import calculate_stats, aggregate_results, generate_markdown


def test_calculate_stats_empty():
    result = calculate_stats([])
    assert result == {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}


def test_calculate_stats_single():
    result = calculate_stats([0.8])
    assert result["mean"] == pytest.approx(0.8)
    assert result["stddev"] == 0.0
    assert result["min"] == pytest.approx(0.8)
    assert result["max"] == pytest.approx(0.8)


def test_calculate_stats_multiple():
    result = calculate_stats([0.5, 0.75, 1.0])
    assert result["mean"] == pytest.approx(0.75)
    assert result["min"] == pytest.approx(0.5)
    assert result["max"] == pytest.approx(1.0)
    assert result["stddev"] > 0


def test_aggregate_results_empty():
    result = aggregate_results({})
    assert result == {}


def test_aggregate_results_single_config():
    runs = [
        {"pass_rate": 1.0, "time_seconds": 5.0, "tokens": 100},
        {"pass_rate": 0.5, "time_seconds": 3.0, "tokens": 80},
    ]
    result = aggregate_results({"with_skill": runs})
    assert "with_skill" in result
    assert result["with_skill"]["pass_rate"]["mean"] == pytest.approx(0.75)
    assert "delta" in result


def test_aggregate_results_two_configs():
    with_runs = [{"pass_rate": 0.9, "time_seconds": 4.0, "tokens": 90}]
    without_runs = [{"pass_rate": 0.6, "time_seconds": 5.0, "tokens": 100}]
    result = aggregate_results({"with_skill": with_runs, "without_skill": without_runs})
    delta = result["delta"]
    assert delta["pass_rate"] == "+0.30"


def test_generate_markdown_has_summary():
    benchmark = {
        "metadata": {
            "skill_name": "test-skill",
            "executor_model": "claude-sonnet-4-6",
            "timestamp": "2026-01-01T00:00:00Z",
            "evals_run": [1, 2],
            "runs_per_configuration": 3,
        },
        "run_summary": {
            "with_skill": {
                "pass_rate": {"mean": 0.9, "stddev": 0.05, "min": 0.8, "max": 1.0},
                "time_seconds": {"mean": 4.0, "stddev": 0.5, "min": 3.0, "max": 5.0},
                "tokens": {"mean": 100, "stddev": 10, "min": 80, "max": 120},
            },
            "without_skill": {
                "pass_rate": {"mean": 0.6, "stddev": 0.1, "min": 0.5, "max": 0.7},
                "time_seconds": {"mean": 5.0, "stddev": 0.5, "min": 4.5, "max": 5.5},
                "tokens": {"mean": 110, "stddev": 10, "min": 100, "max": 120},
            },
            "delta": {"pass_rate": "+0.30", "time_seconds": "-1.0", "tokens": "-10"},
        },
        "notes": [],
    }
    md = generate_markdown(benchmark)
    assert "# Skill Benchmark: test-skill" in md
    assert "## Summary" in md
    assert "Pass Rate" in md
```

- [ ] **Step 5: Create `skills/skill-builder/tests/test_generate_report.py`**

```python
from scripts.generate_report import generate_html


def _minimal_data(description: str = "test description") -> dict:
    return {
        "original_description": "original",
        "best_description": description,
        "best_score": "3/4",
        "iterations_run": 1,
        "holdout": 0.0,
        "train_size": 4,
        "test_size": 0,
        "history": [
            {
                "iteration": 1,
                "description": description,
                "train_passed": 3,
                "train_failed": 1,
                "train_total": 4,
                "train_results": [
                    {"query": "fix bug", "should_trigger": True, "pass": True, "triggers": 2, "runs": 2},
                    {"query": "add feature", "should_trigger": True, "pass": True, "triggers": 2, "runs": 2},
                    {"query": "deploy app", "should_trigger": False, "pass": True, "triggers": 0, "runs": 2},
                    {"query": "write tests", "should_trigger": True, "pass": False, "triggers": 0, "runs": 2},
                ],
                "test_results": None,
                "test_passed": None,
                "test_total": None,
            }
        ],
    }


def test_generate_html_returns_string():
    html = generate_html(_minimal_data())
    assert isinstance(html, str)
    assert len(html) > 100


def test_generate_html_contains_description():
    html = generate_html(_minimal_data("my-test-description"))
    assert "my-test-description" in html


def test_generate_html_escapes_description():
    html = generate_html(_minimal_data('<script>alert("xss")</script>'))
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_generate_html_no_auto_refresh_by_default():
    html = generate_html(_minimal_data())
    assert 'http-equiv="refresh"' not in html


def test_generate_html_auto_refresh_when_requested():
    html = generate_html(_minimal_data(), auto_refresh=True)
    assert 'http-equiv="refresh"' in html


def test_generate_html_skill_name_in_title():
    html = generate_html(_minimal_data(), skill_name="my-skill")
    assert "my-skill" in html
```

- [ ] **Step 6: Run the new tests**

```bash
.venv/Scripts/python.exe -m pytest skills/skill-builder/tests/ -v -o addopts=""
```

Expected: all tests PASS

- [ ] **Step 7: Run `npm run test:python` and confirm it succeeds**

```bash
npm run test:python
```

Expected: exits 0 (all tests pass, no "file or directory not found" error)

- [ ] **Step 8: Commit**

```bash
git add skills/skill-builder/tests/
git commit -m "test(skill-builder): create missing test directory with smoke tests

pyproject.toml and package.json both referenced skills/skill-builder/tests/
which did not exist, breaking npm run test:python. Added conftest.py with
sys.path fix and tests for aggregate_benchmark and generate_report.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 7: Fix lint.py multi-line `run:` injection check

The injection check at `lint.py:44-48` only catches `${{ github.event... }}` on the same line as `run:`. The common `run: |` block scalar form spreads the run body over multiple lines — those lines are completely missed.

**Files:**

- Modify: `skills/github-automation/scripts/lint.py`

- [ ] **Step 1: Write a test fixture that exposes the gap**

```bash
cat > /tmp/test_multiline_injection.yml << 'EOF'
name: test
on: [pull_request]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: risky step
        run: |
          echo "Title: ${{ github.event.pull_request.title }}"
EOF
.venv/Scripts/python.exe skills/github-automation/scripts/lint.py /tmp/test_multiline_injection.yml
```

Expected currently: `Lint OK (1 file(s))` — **BUG: should report injection**

- [ ] **Step 2: Replace the injection check block in `skills/github-automation/scripts/lint.py`**

Replace lines 40–48 (the injection check section):

```python
    # 2. Expression injection — including multi-line run: block scalars
    # github.event.(pull_request|issue|comment|review|head_commit).(title|body|message)
    # github.head_ref
    injection_pattern = r"\$\{\{\s*github\.(event\.(pull_request|issue|comment|review|head_commit)\.(title|body|message)|head_ref|event\.head_commit\.message)"
    in_run_block = False
    run_block_indent: int | None = None

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)

        run_match = re.match(r'^(\s*)run:\s*[|>-]?\s*$', line)
        if run_match:
            in_run_block = True
            run_block_indent = len(run_match.group(1)) + 1
        elif re.match(r'^\s*run:\s+\S', line):
            # Inline run: value (no block scalar)
            in_run_block = False
            run_block_indent = None
            if re.search(injection_pattern, line):
                errors.append(
                    f"L{i + 1}: Possible expression injection — untrusted github.event field inside run:. Use env: instead."
                )
            continue
        elif in_run_block:
            if stripped and current_indent <= run_block_indent:
                in_run_block = False
                run_block_indent = None

        if in_run_block and re.search(injection_pattern, line):
            errors.append(
                f"L{i + 1}: Possible expression injection — untrusted github.event field inside run:. Use env: instead."
            )
```

- [ ] **Step 3: Verify the multi-line case is now caught**

```bash
.venv/Scripts/python.exe skills/github-automation/scripts/lint.py /tmp/test_multiline_injection.yml
```

Expected: output contains `L11: Possible expression injection` (or similar line number)

- [ ] **Step 4: Verify the inline case still works**

```bash
cat > /tmp/test_inline_injection.yml << 'EOF'
name: test
on: [pull_request]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: risky inline
        run: echo "${{ github.event.pull_request.title }}"
EOF
.venv/Scripts/python.exe skills/github-automation/scripts/lint.py /tmp/test_inline_injection.yml
```

Expected: output contains `Possible expression injection`

- [ ] **Step 5: Verify a clean workflow still passes**

```bash
cat > /tmp/test_clean.yml << 'EOF'
name: test
on: [pull_request]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    env:
      PR_TITLE: ${{ github.event.pull_request.title }}
    steps:
      - name: safe step
        run: echo "$PR_TITLE"
EOF
.venv/Scripts/python.exe skills/github-automation/scripts/lint.py /tmp/test_clean.yml
```

Expected: `Lint OK (1 file(s))` (no injection warning — env: usage is safe)

- [ ] **Step 6: Run the full test suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ skills/skill-builder/tests/ -q -o addopts=""
```

Expected: `0 failed, 155+ passed`

- [ ] **Step 7: Commit**

```bash
git add skills/github-automation/scripts/lint.py
git commit -m "fix(lint): detect expression injection in multi-line run: block scalars

The previous check only matched \${{ }} on the same line as 'run:'.
Multi-line 'run: |' blocks were missed entirely. Now tracks block scalar
state across lines using indentation.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## GROUP C — LOW: Code Quality

---

### Task 8: Deduplicate token constants and add AgentSpec type hints

`cost.py` and `diff.py` hardcode `// 4` and `// 150` — the same values already defined as `CHARS_PER_TOKEN` and `TOOL_SCHEMA_TOKENS` in `heuristics.py`. Also, five functions in `compile.py`, `cost.py`, `diff.py`, and `recommend.py` accept `spec` without the `AgentSpec` annotation.

**Files:**

- Modify: `skills/agent-development/scripts/cost.py`
- Modify: `skills/agent-development/scripts/diff.py`
- Modify: `skills/agent-development/scripts/compile.py`
- Modify: `skills/agent-development/scripts/recommend.py`

- [ ] **Step 1: Fix `cost.py` — import constants, annotate `spec`**

Add `TOOL_SCHEMA_TOKENS` to the import from `lib.heuristics` at the top of `skills/agent-development/scripts/cost.py`:

```python
from lib.heuristics import estimate_input_tokens, estimate_tokens, TOOL_SCHEMA_TOKENS
```

(The import already has `TOOL_SCHEMA_TOKENS` — verify it's there. If not, add it.)

Add the `AgentSpec` import and annotate `estimate_cost`:

```python
from lib.agent_parser import ParseError, AgentSpec

# ...

def estimate_cost(spec: AgentSpec, runs: int = 3, output_tokens: int = 500) -> dict:
```

Also fix line 65 in `render_human_cost` which re-hardcodes `// 150`:

```python
    tool_count = r["tool_tokens"] // TOOL_SCHEMA_TOKENS if r["tool_tokens"] else 0
```

Add `TOOL_SCHEMA_TOKENS` to the import at the top of cost.py (it already imports from heuristics, just add it to that import line).

- [ ] **Step 2: Fix `diff.py` — import constant, annotate `diff_agents`**

In `skills/agent-development/scripts/diff.py`, add to the existing heuristics import:

```python
from lib.agent_parser import parse_agent, ParseError, AgentSpec
from lib.heuristics import CHARS_PER_TOKEN
```

Add type annotation to `diff_agents`:

```python
def diff_agents(cur: AgentSpec, prop: AgentSpec) -> list:
```

Fix line 160 which uses the hardcoded `// 4`:

```python
        ct_tok = len(cur.system_prompt) // CHARS_PER_TOKEN
        pt_tok = len(prop.system_prompt) // CHARS_PER_TOKEN
```

- [ ] **Step 3: Fix `compile.py` — annotate `validate` and `to_payload`**

In `skills/agent-development/scripts/compile.py`, the existing import is:

```python
from lib.agent_parser import parse_agent, detect_agent_kind, ParseError
```

Add `AgentSpec`:

```python
from lib.agent_parser import parse_agent, detect_agent_kind, ParseError, AgentSpec
```

Annotate the two functions:

```python
def validate(spec: AgentSpec, mode: str) -> list:
```

```python
def to_payload(spec: AgentSpec, mode: str) -> dict:
```

- [ ] **Step 4: Fix `recommend.py` — annotate `recommend`**

In `skills/agent-development/scripts/recommend.py`, add `AgentSpec` to the import:

```python
from lib.agent_parser import parse_agent, ParseError, AgentSpec
```

Annotate:

```python
def recommend(spec: AgentSpec) -> dict:
```

- [ ] **Step 5: Run the full test suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ skills/skill-builder/tests/ -q -o addopts=""
```

Expected: `0 failed, 155+ passed`

- [ ] **Step 6: Commit**

```bash
git add \
  skills/agent-development/scripts/cost.py \
  skills/agent-development/scripts/diff.py \
  skills/agent-development/scripts/compile.py \
  skills/agent-development/scripts/recommend.py
git commit -m "refactor: import token constants; add AgentSpec type hints

cost.py and diff.py hardcoded 4 and 150 — the same values as CHARS_PER_TOKEN
and TOOL_SCHEMA_TOKENS in heuristics.py. Now imports them. Also added
AgentSpec type annotations to spec params in compile, cost, diff, recommend.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 9: Hoist nested functions out of the loop in generate_report.py

`generate_html()` in `skills/skill-builder/scripts/generate_report.py` defines `aggregate_runs()` and `score_class()` inside the `for h in history:` loop (lines 246–270), re-creating the function objects on every iteration.

**Files:**

- Modify: `skills/skill-builder/scripts/generate_report.py`

- [ ] **Step 1: Locate the nested definitions**

```bash
grep -n "def aggregate_runs\|def score_class" skills/skill-builder/scripts/generate_report.py
```

Expected: both appear at lines inside the `for h in history:` loop (around 246–265).

- [ ] **Step 2: Hoist `_aggregate_runs` and `_score_class` to module level**

Add these two functions at module level, just before the `generate_html` function definition (insert after the CSS/imports section, before line where `def generate_html` begins):

```python
def _aggregate_runs(results: list[dict]) -> tuple[int, int]:
    """Compute total correct and total run counts across all results."""
    correct = 0
    total = 0
    for r in results:
        runs = r.get("runs", 0)
        triggers = r.get("triggers", 0)
        total += runs
        if r.get("should_trigger", True):
            correct += triggers
        else:
            correct += runs - triggers
    return correct, total


def _score_class(correct: int, total: int) -> str:
    """Return a CSS class name based on the correct/total ratio."""
    if total > 0:
        ratio = correct / total
        if ratio >= 0.8:
            return "score-good"
        elif ratio >= 0.5:
            return "score-ok"
    return "score-bad"
```

- [ ] **Step 3: Replace the inline definitions inside `generate_html` with calls to the hoisted functions**

Inside the `for h in history:` loop, replace the inline `def aggregate_runs(...)` and `def score_class(...)` blocks plus their calls with:

```python
        train_correct, train_runs = _aggregate_runs(train_results)
        test_correct, test_runs = _aggregate_runs(test_results)

        train_class = _score_class(train_correct, train_runs)
        test_class = _score_class(test_correct, test_runs)
```

- [ ] **Step 4: Run the generate_report tests**

```bash
.venv/Scripts/python.exe -m pytest skills/skill-builder/tests/test_generate_report.py -v -o addopts=""
```

Expected: all tests PASS

- [ ] **Step 5: Run the full test suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ skills/skill-builder/tests/ -q -o addopts=""
```

Expected: `0 failed, 155+ passed`

- [ ] **Step 6: Commit**

```bash
git add skills/skill-builder/scripts/generate_report.py
git commit -m "refactor(generate_report): hoist nested functions out of loop

aggregate_runs and score_class were re-created as closures on every loop
iteration. Hoisted to module-level helpers _aggregate_runs and _score_class.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 10: Fix package_skill.py broken import

`skills/skill-builder/scripts/package_skill.py` line 17 does `from scripts.quick_validate import validate_skill` with no `sys.path` setup, so it fails when run directly (only works if launched as a module from the skill-builder root). Also the docstring still says `utils/package_skill.py`.

**Files:**

- Modify: `skills/skill-builder/scripts/package_skill.py`

- [ ] **Step 1: Confirm the direct-invocation failure**

```bash
.venv/Scripts/python.exe skills/skill-builder/scripts/package_skill.py --help 2>&1 | tail -4
```

Expected: `ModuleNotFoundError: No module named 'scripts'`

- [ ] **Step 2: Add sys.path setup before the import**

In `skills/skill-builder/scripts/package_skill.py`, replace the import at line 17:

```python
from scripts.quick_validate import validate_skill
```

With:

```python
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).parent.parent))
from scripts.quick_validate import validate_skill
```

- [ ] **Step 3: Fix the stale docstring**

Replace the docstring at lines 7–11:

```python
"""
Skill Packager - Creates a distributable .skill file of a skill folder

Usage:
    python utils/package_skill.py <path/to/skill-folder> [output-directory]

Example:
    python utils/package_skill.py skills/public/my-skill
    python utils/package_skill.py skills/public/my-skill ./dist
"""
```

With:

```python
"""
Skill Packager - Creates a distributable .skill file of a skill folder

Usage:
    python scripts/package_skill.py <path/to/skill-folder> [output-directory]

Example:
    python scripts/package_skill.py skills/public/my-skill
    python scripts/package_skill.py skills/public/my-skill ./dist
"""
```

- [ ] **Step 4: Verify direct invocation now works**

```bash
.venv/Scripts/python.exe skills/skill-builder/scripts/package_skill.py --help 2>&1 | tail -4
```

Expected: prints usage/help (not a traceback)

- [ ] **Step 5: Run the full test suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ skills/skill-builder/tests/ -q -o addopts=""
```

Expected: `0 failed, 155+ passed`

- [ ] **Step 6: Commit**

```bash
git add skills/skill-builder/scripts/package_skill.py
git commit -m "fix(package_skill): add sys.path setup for direct invocation; fix docstring

'from scripts.quick_validate import validate_skill' required the skill-builder
root on sys.path. Direct invocation failed with ModuleNotFoundError. Also
corrected stale 'utils/' path in the docstring.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 11: Fix observer.py module-level code — add error handling

Two committed `observer.py` copies run their logic at module level with no error handling. The lib version (`lib/observer.py`) correctly uses a `main()` function with `try/except`. The root `.simulate/observer.py` and `scripts/.simulate/observer.py` do not, violating the "hooks must never disrupt the main Claude process" principle.

**Files:**

- Modify: `.simulate/observer.py`
- Modify: `skills/agent-development/scripts/.simulate/observer.py`

- [ ] **Step 1: Rewrite `.simulate/observer.py`**

Replace the entire file content with:

```python
#!/usr/bin/env python3
"""Observer hook for simulate.py — append hook input to JSONL, exit 0."""

import json
import os
import sys
from pathlib import Path


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    run_id = os.environ.get("SIMULATE_RUN_ID", "default")
    out_dir_str = os.environ.get("SIMULATE_OUT_DIR", ".simulate/runs")

    out_dir = Path(out_dir_str) / run_id
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        log_file = out_dir / "tool-calls.jsonl"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except (OSError, PermissionError):
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Apply the same fix to `skills/agent-development/scripts/.simulate/observer.py`**

Replace the entire file content with the same content as Step 1.

- [ ] **Step 3: Run the full test suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ skills/skill-builder/tests/ -q -o addopts=""
```

Expected: `0 failed, 155+ passed`

- [ ] **Step 4: Commit**

```bash
git add .simulate/observer.py skills/agent-development/scripts/.simulate/observer.py
git commit -m "fix(observer): wrap module-level code in main() with error handling

Both .simulate/observer.py copies ran at module level with no exception
handling. A JSONDecodeError or OS error would crash the hook and disrupt
the main Claude process. Now matches the safe pattern in lib/observer.py.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 12: Fix simulate.py dead agent-file wiring

`run_case()` in `simulate.py` builds a `claude -p` command but never includes the `agent_file` argument. Lines 114–119 contain a `pass` with a comment acknowledging this. The agent under test is silently not selected.

The correct Claude Code CLI flag to use a custom agent is `--system-prompt <file>` (which feeds the system prompt) or `--model`. Since `simulate.py` is testing behaviors by running `claude -p` with hook injection, the practical approach is to prepend the agent's system prompt as a preamble in the prompt, which is what the comment suggests as a workaround.

**Files:**

- Modify: `skills/agent-development/scripts/simulate.py`

- [ ] **Step 1: Read the agent system prompt and prepend it to the prompt**

In `run_case()`, replace lines 113–119:

```python
        cmd = ["claude", "-p", prompt, "--output-format", "json"]
        if agent_file:
            # How to specify the agent? Usually by pointing to its instructions or using it.
            # If it's a subagent file, we might need a specific CLI flag if available.
            # For now, we assume the prompt includes "Use [agent]" if needed.
            pass
```

With:

```python
        if agent_file:
            # claude -p does not have a dedicated --agent-file flag.
            # Inject the agent's system prompt as a preamble so the model
            # runs with the intended persona during simulation.
            try:
                from lib.agent_parser import parse_agent, ParseError
                agent_spec = parse_agent(agent_file)
                system_preamble = f"[SYSTEM PROMPT]\n{agent_spec.system_prompt}\n[END SYSTEM PROMPT]\n\n"
                effective_prompt = system_preamble + prompt
            except Exception:
                effective_prompt = prompt
        else:
            effective_prompt = prompt

        cmd = ["claude", "-p", effective_prompt, "--output-format", "json"]
```

- [ ] **Step 2: Fix the shutil import placement**

`import shutil` at line 27 is mid-module (after `import time`). Move it to the top-level imports block with the other stdlib imports:

```python
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
```

Remove the mid-module `import shutil` from where it currently appears.

- [ ] **Step 3: Run the full test suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ skills/skill-builder/tests/ -q -o addopts=""
```

Expected: `0 failed, 155+ passed`

- [ ] **Step 4: Commit**

```bash
git add skills/agent-development/scripts/simulate.py
git commit -m "fix(simulate): wire agent file into claude invocation; move shutil import

run_case() built a claude -p command but silently ignored agent_file (pass
with a TODO comment). Now extracts the system prompt from the agent spec and
prepends it to the prompt. Also moved shutil import to the top-level block.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 13: Fix frontmatter parsers in skill-builder and agents-maintainer

Three files contain hand-rolled YAML frontmatter parsers that silently mishandle edge cases (quoted strings, multi-key blocks, YAML anchors). The correct yaml-based parser lives in `skills/agent-development/scripts/lib/frontmatter.py`. Since those files can't import across skill boundaries, the fix is to add a PyYAML code path inside each hand-rolled parser, keeping the existing logic as a fallback when PyYAML is absent.

**Files:**

- Modify: `skills/skill-builder/scripts/utils.py`
- Modify: `skills/skill-builder/scripts/quick_validate.py`
- Modify: `skills/agents-maintainer/scripts/run.py`

- [ ] **Step 1: Fix `skills/skill-builder/scripts/utils.py` — `parse_skill_md`**

Replace the `parse_skill_md` function with a version that uses PyYAML when available:

```python
def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")

    match = __import__("re").match(r"^---\n(.*?)\n---\n", content, __import__("re").DOTALL)
    if not match:
        raise ValueError("SKILL.md missing frontmatter")

    frontmatter_text = match.group(1)

    try:
        import yaml
        fm = yaml.safe_load(frontmatter_text) or {}
        name = str(fm.get("name", "")).strip()
        description = fm.get("description", "")
        if isinstance(description, list):
            description = " ".join(description)
        description = str(description).strip()
    except ImportError:
        # Fallback: hand-rolled parser (no PyYAML)
        name = ""
        description = ""
        lines = frontmatter_text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("name:"):
                name = line[len("name:"):].strip().strip('"').strip("'")
            elif line.startswith("description:"):
                value = line[len("description:"):].strip()
                if value in (">", "|", ">-", "|-"):
                    continuation_lines: list[str] = []
                    i += 1
                    while i < len(lines) and (
                        lines[i].startswith("  ") or lines[i].startswith("\t")
                    ):
                        continuation_lines.append(lines[i].strip())
                        i += 1
                    sep = "\n" if value in ("|", "|-") else " "
                    description = sep.join(continuation_lines)
                    continue
                else:
                    description = value.strip('"').strip("'")
            i += 1

    return name, description, content
```

- [ ] **Step 2: Fix `skills/skill-builder/scripts/quick_validate.py` — `_parse_frontmatter`**

Replace the `_parse_frontmatter` function:

```python
def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a flat YAML-style frontmatter block into top-level key/value pairs."""
    try:
        import yaml
        result = yaml.safe_load(text) or {}
        return {k: str(v) for k, v in result.items() if isinstance(k, str)}
    except ImportError:
        pass

    # Fallback: hand-rolled parser for environments without PyYAML
    result: dict[str, str] = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*):\s*(.*)", lines[i])
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value in (">", "|", ">-", "|-", ""):
                i += 1
                block: list[str] = []
                while i < len(lines) and (
                    lines[i].startswith("  ") or lines[i].startswith("\t")
                ):
                    block.append(lines[i].strip())
                    i += 1
                sep = "\n" if value in ("|", "|-") else " "
                result[key] = sep.join(block)
                continue
            else:
                result[key] = value.strip('"').strip("'")
        i += 1
    return result
```

- [ ] **Step 3: Fix `skills/agents-maintainer/scripts/run.py` — `_parse_frontmatter`**

Replace the `_parse_frontmatter` function (lines 141–154):

```python
def _parse_frontmatter(content: str) -> dict[str, str]:
    """Parse YAML frontmatter. Uses PyYAML when available; falls back to line parser."""
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end == -1:
        return {}
    yaml_text = content[3:end]

    try:
        import yaml
        result = yaml.safe_load(yaml_text) or {}
        return {k: str(v) for k, v in result.items() if isinstance(k, str)}
    except ImportError:
        pass

    # Fallback: simple line parser (no PyYAML)
    result: dict[str, str] = {}
    for line in yaml_text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result
```

- [ ] **Step 4: Run the full test suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ skills/skill-builder/tests/ -q -o addopts=""
```

Expected: `0 failed, 155+ passed`

- [ ] **Step 5: Commit**

```bash
git add \
  skills/skill-builder/scripts/utils.py \
  skills/skill-builder/scripts/quick_validate.py \
  skills/agents-maintainer/scripts/run.py
git commit -m "refactor: use PyYAML in frontmatter parsers with hand-rolled fallback

Three files had custom YAML frontmatter parsers that mishandled quoted strings
and block scalars. Each now tries PyYAML first and falls back to the existing
hand-rolled logic when PyYAML is absent.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Final Verification

After completing all 13 tasks:

- [ ] **Run the full Python test suite**

```bash
.venv/Scripts/python.exe -m pytest skills/agent-development/scripts/tests/ skills/skill-builder/tests/ -q -o addopts=""
```

Expected: `0 failed, 155+ passed`

- [ ] **Run `npm run test:python`**

```bash
npm run test:python
```

Expected: exits 0

- [ ] **Confirm audit.py no longer crashes on cc_subagent files**

```bash
.venv/Scripts/python.exe skills/agent-development/scripts/audit.py \
  skills/agent-development/scripts/tests/fixtures/cc-subagent-bad-tools.md \
  --json 2>&1 | head -5
```

Expected: valid JSON array (not a traceback)

- [ ] **Confirm spec scripts are importable**

```bash
.venv/Scripts/python.exe skills/create-plan/scripts/generate_plan.py --help 2>&1 | tail -2
.venv/Scripts/python.exe skills/create-specs/scripts/validate_spec.py --help 2>&1 | tail -2
```

Expected: both print usage text

- [ ] **Confirm piped output no longer crashes**

```bash
.venv/Scripts/python.exe skills/agents-maintainer/scripts/run.py check-all 2>&1 | tail -5
```

Expected: ends with `PASS: Audit passed. Plugin is healthy.` (no UnicodeEncodeError)
