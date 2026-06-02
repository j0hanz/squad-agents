# Implementation Governance

Follow these procedures strictly during the implementation phase (after Spec and Plan are validated).

## 1. The Tracer Bullet

Before executing the full plan, implement the first unblocked task from PHASE-001.

```text
PICK:      First task with Depends on: none
IMPLEMENT: Write minimal code satisfying the task's Action field only
VALIDATE:  Run the task's exact Validate command
OBSERVE:   Confirm the task's Expected result appears
```

This is your tracer bullet — it proves the end-to-end path works before committing to the full plan.

**Handling External Dependencies in the Tracer Bullet:**
If the first task involves external systems (e.g., a database that isn't provisioned, a 3rd-party API without credentials):

- Do NOT skip the task or write mocked code unless explicitly directed by the spec.
- Ask the user to provide the necessary credentials, or provision the required infrastructure.
- Validate the connection/integration before moving to the next task.

## 2. The Incremental Loop

For each remaining task in plan order:

```text
PICK:      Next task where all dependencies are completed
IMPLEMENT: Minimal code for this task's Action only — nothing beyond it
VALIDATE:  Run this task's Validate command
OBSERVE:   Confirm Expected result matches
```

**Rules:**

- **One task at a time.**
- **Do not implement ahead** of the current task, even if the next step seems obvious.
- **If a Validate command fails**, fix the implementation before moving on. NEVER skip a failed gate. If you attempt a fix 3 times without success, escalate to the user and re-evaluate the plan.

## 3. Detecting Spec Drift

If implementation reveals a gap between the code and the spec, you must stop.

**Stop-work triggers** (full list: [anti-patterns.md](anti-patterns.md)):

- Implementation requires a new API endpoint, database column, or library not in the spec.
- You discover a missing error case, race condition, or auth failure state.
- You find yourself writing "just in case" code that doesn't map to a specific `AC-###`.

**Resolution:**

1. Stop coding immediately.
2. Update the `spec-*.md` file with the new requirement or edge case.
3. Re-run `sync.py` to update plan stubs, then `validate.py --cross` to confirm coverage.
4. Resume implementation from the updated plan.
