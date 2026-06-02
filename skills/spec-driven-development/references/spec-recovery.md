# Recovering from Spec Misalignment

When implementation reveals the spec was incomplete or wrong,
this guide explains how to fix it without losing work.

## Impact Assessment

When you discover the spec is missing requirements:

**Question 1: Does this change the architecture?**

- Interfaces change (new endpoints, new tables)
- Dependencies shift (now need a new service)
- Data model is wrong
  → This is a "major" change

**Question 2: How many AC items does this affect?**

- 1–2: "minor" change
- 3+: "major" change (impacts plan)

---

## Minor Change (1–2 AC items, no architecture shift)

**Time impact**: 1–2 hours

**Process**:

1. Update the spec with the missing REQ/AC/VAL
2. Run `validate_spec.py` again (should still pass)
3. Update the plan (incremental change, edit affected tasks)
4. Implement only the changed task(s)
5. Run the validation command for the changed task(s)

**Example**: Missing "password reset timeout is 24h" → add AC, update test, implement.

---

## Major Change (3+ AC items, or architecture shift)

**Time impact**: 4–8 hours (depends on scope)

**Process**:

1. **Commit current work** (checkpoint)

   ```bash
   git commit -m "WIP: partial implementation of [spec-name]"
   ```

2. **Update the spec** with all discovered issues
   - Add missing REQ items
   - Add missing AC items
   - Update interfaces if they changed

3. **Re-validate the spec**

   ```bash
   python <skill-dir>/scripts/validate.py <name> --spec
   ```

4. **Re-sync and validate the plan** (full regeneration)

   ```bash
   python <skill-dir>/scripts/sync.py <name>.specs.md
   python <skill-dir>/scripts/validate.py <name> --plan --cross
   ```

5. **Evaluate: Continue or Restart?**
   - If tasks 1–3 are still valid: Continue from where you left off
   - If tasks 1–3 are invalidated: Reset and restart from the new plan
     ```bash
     git reset --hard HEAD~N  # Discard WIP commit
     ```

6. **Resume implementation** from the new plan

**Example**: Discover you need multi-tenant isolation (not in original spec) →
update spec, regenerate plan (likely 2–3 new tasks), evaluate if tasks 1–3 still apply.

---

## When to Use This Recovery Process

- ✓ Plan validation fails mid-implementation → Fix spec, regenerate plan, continue
- ✓ QA finds missing edge case → Add to spec, update plan, implement
- ✓ Integration reveals API mismatch → Update spec, regenerate plan
- ✗ Small bug in code → Don't loop through spec; just fix the code
- ✗ Performance tuning → Update code directly; spec is still valid

---

## Preventing Major Changes

To avoid mid-implementation spec drift:

1. **Thorough Spec Interview** (spend 30 min, not 5 min)
2. **Involve stakeholders** (product, architecture, QA in the spec)
3. **Trace REQ → AC → VAL** (validate_spec.py does this automatically)
4. **Run the Tracer Bullet first** (first task proves design before full commitment)
