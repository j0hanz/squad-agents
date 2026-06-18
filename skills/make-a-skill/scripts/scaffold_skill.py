#!/usr/bin/env python3
"""scaffold_skill.py — Emit a new <name>/SKILL.md skeleton.

Usage:
    python scaffold_skill.py <name> [--dir .claude/skills] [--scripts]
                                     [--references] [--evals] [--force]

Default output dir is `.claude/skills` — the standard Claude Code location
for project-level skills. Pass `--dir skills` when scaffolding a skill that
ships inside a plugin's own `skills/` directory (as this skill does).

Every body section, and the frontmatter `description` field, is written as a
bracketed `{{FILL: ...}}` placeholder. `name` is written for real — the
directory name is already known at scaffold time. Filling in the real
description is a deliberate later step (after the body is drafted, so the
description reflects what the skill actually does), gated by
`validate_skill.py` rejecting any leftover `{{FILL` marker.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SKILL_TEMPLATE = """\
---
name: {name}
description: "{{{{FILL: One line, third person. What it's for and when NOT to use it \
(point to the sibling skill that should be used instead, if any). End with: \
Trigger on: 'phrase one', 'phrase two', '{name}'.}}}}"
disable-model-invocation: false
---

# {name}

{{{{FILL: One paragraph — what this skill does and why it exists as its own skill \
rather than folded into an existing one.}}}}

## Process Flow

{{{{FILL: Either a numbered step list, or a ```dot``` digraph (see \
$CLAUDE_PLUGIN_ROOT/skills/refactor/SKILL.md for a short example). Delete this \
section if the skill is a single linear procedure with no branches.}}}}

## Step 1: {{{{FILL: short step name}}}}

{{{{FILL: what to do in this step, and which tool/script to invoke.}}}}

## Step 2: {{{{FILL: short step name}}}}

{{{{FILL: what to do in this step.}}}}

## NEVER

- **NEVER** {{{{FILL: thing to avoid}}}}. **WHY:** {{{{FILL: reason}}}}. **FIX:** {{{{FILL: alternative}}}}.

**next skills:**

- `{{{{FILL: skill-name}}}}`: {{{{FILL: when to hand off to it}}}}.
"""

_CHECKLIST_STUB = """\
# {name} — validation checklist

{{{{FILL: human-readable mirror of the rules validate_skill.py enforces for this \
skill, if it has any beyond the generic make-a-skill rule set. Delete this file if \
not needed — it's optional.}}}}
"""

_SCRIPT_STUB = '''\
#!/usr/bin/env python3
"""{{{{FILL: one-line purpose}}}}"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="{{{{FILL: purpose}}}}")
    args = parser.parse_args()
    raise NotImplementedError("{{{{FILL: implement {name}}}}}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{{Path(__file__).name}}: {{e}}", file=sys.stderr)
        sys.exit(1)
'''


def _evals_stub(name: str) -> dict:
    return {
        "skill_name": name,
        "evals": [
            {
                "id": 1,
                "prompt": "FILL: a realistic user prompt that should trigger this skill",
                "expected_output": "FILL: one sentence describing the expected shape of a good response",
                "files": [],
                "assertions": [
                    "FILL: a specific, checkable assertion about the response"
                ],
            }
        ],
    }


def scaffold(
    name: str,
    out_dir: str | Path = ".claude/skills",
    with_scripts: bool = False,
    with_references: bool = False,
    with_evals: bool = False,
    force: bool = False,
) -> list[Path]:
    """Write a new skill skeleton. Returns the list of paths created."""
    if (
        "/" in name
        or "\\" in name
        or name.startswith(".")
        or "\x00" in name
        or name != name.lower()
    ):
        raise ValueError(
            f"Invalid name {name!r}: must be a lowercase, plain directory name "
            "with no path separators (kebab-case, e.g. 'make-a-skill')"
        )

    skill_dir = Path(out_dir).resolve() / name
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists() and not force:
        raise FileExistsError(f"{skill_md} already exists. Use --force to overwrite.")

    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md.write_text(_SKILL_TEMPLATE.format(name=name), encoding="utf-8")
    created = [skill_md]

    if with_scripts:
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        script_path = scripts_dir / f"{name.replace('-', '_')}.py"
        if not script_path.exists() or force:
            script_path.write_text(_SCRIPT_STUB.format(name=name), encoding="utf-8")
            created.append(script_path)

    if with_references:
        references_dir = skill_dir / "references"
        references_dir.mkdir(exist_ok=True)
        checklist_path = references_dir / "checklist.md"
        if not checklist_path.exists() or force:
            checklist_path.write_text(
                _CHECKLIST_STUB.format(name=name), encoding="utf-8"
            )
            created.append(checklist_path)

    if with_evals:
        evals_dir = skill_dir / "evals"
        evals_dir.mkdir(exist_ok=True)
        evals_path = evals_dir / "evals.json"
        if not evals_path.exists() or force:
            evals_path.write_text(
                json.dumps(_evals_stub(name), indent=2) + "\n", encoding="utf-8"
            )
            created.append(evals_path)

    return created


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new skills/<name>/SKILL.md skeleton."
    )
    parser.add_argument("name", help="Skill name, kebab-case (e.g. 'make-a-skill')")
    parser.add_argument(
        "--dir",
        default=".claude/skills",
        metavar="DIR",
        help="Skills root (default: .claude/skills/; use 'skills' for plugin-authored skills)",
    )
    parser.add_argument(
        "--scripts", action="store_true", help="Also stub scripts/<name>.py"
    )
    parser.add_argument(
        "--references", action="store_true", help="Also stub references/checklist.md"
    )
    parser.add_argument(
        "--evals", action="store_true", help="Also stub evals/evals.json"
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")

    args = parser.parse_args()
    created = scaffold(
        args.name,
        out_dir=args.dir,
        with_scripts=args.scripts,
        with_references=args.references,
        with_evals=args.evals,
        force=args.force,
    )
    for path in created:
        print(f"Created: {path}")
    print(
        f"\nNext: fill in every {{{{FILL: ...}}}} placeholder in {created[0]}, then run:"
    )
    print(f"  python validate_skill.py {args.name}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"scaffold_skill.py: {e}", file=sys.stderr)
        sys.exit(1)
