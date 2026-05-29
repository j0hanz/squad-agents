# Starting Spec-Driven Development with Existing Code

Many projects have partial implementations, prototypes, or code from other teams.  
This guide explains how to apply SDD when code already exists.

## The Core Principle

**Do NOT retrofit a spec from existing code.** This creates a "Retrofitted Spec" — 
an anti-pattern where requirements are written to match already-present behavior, 
making the spec redundant rather than authoritative.

## Two Paths

### Path 1: Code is Mostly Correct (Minor Changes Needed)

If the existing code is ~90% correct and you only need to add/fix edge cases:

**Do not redo the whole thing.** Instead:

1. **Create a spec for remaining work only**
   - Scope: "Complete the user dashboard feature" (not "build dashboard")
   - Goal: What's still missing or broken?
   - Include only new REQ/AC/VAL items
   - Reference existing code as the baseline

2. **Create a plan for remaining tasks**
   - Tasks are only for new work
   - Validation commands test integration with existing code

3. **Implement and validate** the remaining work

4. **Document the existing code** (separate from SDD cycle)
   - Add comments explaining design decisions
   - Create architecture doc for reference

### Path 2: Code Needs Major Rework (50%+ is wrong)

If the existing code is significantly off or you discovered major issues:

**Start over.** Don't patch code to match a retrofitted spec.

1. **Do NOT copy-paste old code into design discussions**
2. **Clarify scope** as if building from scratch
3. **Create a fresh spec** (ignore old implementation)
4. **Create a fresh plan**
5. **Implement from the plan**
6. **Mark old code as deprecated** (git history preserves it)

## How to Decide (Decision Tree)

```
Does the existing code work correctly?
  ├─ YES, mostly correct (1–2 bugs)
  │   └─ Follow Path 1 (incremental)
  │
  ├─ PARTIALLY (some features work, some don't)
  │   └─ Check: How many AC items fail?
  │       ├─ 1–2: Follow Path 1
  │       └─ 3+: Follow Path 2 (rework)
  │
  └─ NO, fundamentally broken
      └─ Follow Path 2 (fresh start)
```

## Examples

### Example 1 — Path 1 (Incremental)

Existing: User login works, but:
- (Missing) TOTP 2FA support
- (Bug) Password reset emails don't include reset link

**Spec for remaining work**:
```
Goal: Complete user authentication with 2FA and fix password reset

New REQ:
- REQ-1: System MUST support TOTP 2FA (Google Authenticator, Authy)
- REQ-2: Password reset email MUST include secure reset link valid for 24h

New AC:
- AC-1: User can enable/disable TOTP in settings
- AC-2: Login with TOTP prompt after password verification
- AC-3: Password reset link is 64-char random token

New VAL:
- pytest tests/test_2fa.py
- pytest tests/test_password_reset.py
```

### Example 2 — Path 2 (Rework)

Existing: Dashboard has hardcoded data, no real API calls, auth is missing.

**Spec for complete dashboard**:
```
(Write as if building from scratch; ignore existing code.)
```

---

## Red Flags (These indicate Path 2)

- [ ] Existing code has no tests
- [ ] Architecture is tangled (hard to find where to add feature)
- [ ] 50%+ of spec requirements are unmet
- [ ] Code comments say "TODO: fix this properly"
- [ ] You find yourself writing workarounds

If any are true: Use Path 2 (fresh start).

---

## Committing Incrementally (Path 1)

If using Path 1, structure commits as:

```
Commit 1: Baseline (existing working code, no changes)
Commit 2: Add 2FA support
Commit 3: Fix password reset
```

This preserves history and makes reviews clearer.
