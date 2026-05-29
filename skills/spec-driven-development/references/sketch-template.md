# Sketch Spec Template

Use for one-file changes, clear bug fixes, or small features.  
**Max 1 page. Write time: 15–30 min.**

---

## [Feature/Fix Name]

**Goal**: [One sentence describing what and why]

Example: _"Add rate limiting to /api/login to prevent brute force attacks"_

---

## Acceptance Criteria

- [ ] AC-1: [Observable outcome 1]
- [ ] AC-2: [Observable outcome 2]
- [ ] AC-3: [Observable outcome 3]

Example:
- AC-1: Requests >5 per IP per 60s return HTTP 429
- AC-2: Response includes Retry-After header with seconds remaining
- AC-3: Counter resets after 60s of no requests

---

## Validation

How will we test that this is done?

- [ ] Command or test: [VAL-1]
- [ ] Command or test: [VAL-2]

Example:
- `pytest tests/test_rate_limit.py -k "test_429_on_sixth_attempt"`
- `pytest tests/test_rate_limit.py -k "test_retry_after_header"`

---

**Timeline**: [Days / Hours]  
**Estimated effort**: [Small / Medium / Large]

---

**Done?** Proceed directly to **Implementation Governance** (references/implementation-governance.md).

For multi-file features, use **Contract** maturity instead (full spec via create-specs skill).
