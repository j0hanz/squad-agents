# Example: Minimal SDD Cycle

A complete spec-driven development cycle for a small but non-trivial feature.

## Scenario

> "Add rate limiting to the `/api/login` endpoint — 5 attempts per IP per minute."

---

## Step 1 — Scope Clarification

**What is being built?** Per-IP rate limiting on the login endpoint.
**In scope**: counting attempts, returning 429 with `Retry-After`, resetting counts after 60 s.
**Out of scope**: CAPTCHA, account lockout, admin bypass.
**Constraints**: Existing Redis instance; no new infrastructure.
**Maturity level**: Contract (ready to build, testable in staging).

---

## Step 2 — Specification Gate (`create-specs`)

`create-specs` produces `spec-login-rate-limit.md` containing:

```
REQ-001  The system MUST reject login requests exceeding 5 per IP per 60-second window.
REQ-002  The system MUST return HTTP 429 with a Retry-After header on rejection.
REQ-003  The system MUST use Redis for attempt counting with TTL = 60 s.

AC-001   Given 6 POST /api/login from 192.0.2.1 within 60 s, the 6th returns 429.
AC-002   The 429 response includes header: Retry-After: <seconds_remaining>.
AC-003   After 60 s, the same IP may log in successfully.

VAL-001  pytest tests/test_rate_limit.py -k "test_429_on_sixth_attempt"
VAL-002  pytest tests/test_rate_limit.py -k "test_retry_after_header"
VAL-003  pytest tests/test_rate_limit.py -k "test_window_reset"
```

`validate_spec.py` → **0 errors**.

---

## Step 3 — Planning Gate (`create-plan`)

`create-plan` produces `plan-login-rate-limit.md`:

```
PHASE-001  Infrastructure
  TASK-001  Add redis_client fixture to conftest.py
             Depends on: none
             Validate: pytest tests/conftest.py --collect-only | grep redis_client
             Expected: 1 fixture collected

PHASE-002  Core Logic
  TASK-002  Implement RateLimiter class in src/auth/rate_limiter.py
             Depends on: TASK-001
             Validate: python -c "from src.auth.rate_limiter import RateLimiter; print('ok')"
             Expected: ok

  TASK-003  Wire RateLimiter into POST /api/login handler
             Depends on: TASK-002
             Validate: VAL-001 (pytest test_429_on_sixth_attempt)
             Expected: 1 passed

PHASE-003  Acceptance
  TASK-004  Verify Retry-After header and window reset
             Depends on: TASK-003
             Validate: VAL-002, VAL-003
             Expected: 2 passed
```

`validate_plan.py` → **0 errors**.

---

## Step 4 — Implementation (Tracer Bullet)

Execute TASK-001 first. Run its Validate command. Confirm `redis_client` is collected.

Then proceed task-by-task through PHASE-002 and PHASE-003.

---

## Step 5 — Acceptance Validation

Run all three `VAL-###` commands. Confirm each `AC-###` is observable in the running system.

> "Does the system now do what the spec says it must do?" → Yes → Done.

---

## Key Takeaways from This Example

- The spec took ~15 minutes to write via the Spec Interview. The plan took ~10 minutes via `create-plan`.
- Total pre-implementation time: ~25 minutes. Implementation time: ~45 minutes — but zero rework, because the design was settled before the first line of code.
- The `Retry-After` header requirement (REQ-002 / AC-002) was discovered during the Spec Interview, not during implementation. Without the spec, it would have been a post-merge bug.
