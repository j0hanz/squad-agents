# Scope Interview

Complete this interview at Step 1 of the SDD workflow. Conduct in order; take notes as you go.

## Interview Flow (15–30 minutes)

### 1. The Goal (2 min)

Ask: _"What is being built and why? Give me one sentence."_
Document: One clear sentence.

### 2. The Boundaries (5 min)

Ask: _"What's explicitly IN scope? What's OUT of scope?"_
Document: Two lists (in scope / out of scope).

### 3. The Constraints (5 min)

Ask: _"What limits do we have? Deadline? Tech stack? Team size? Compliance?"_
Document: Constraints as a list.

### 4. The Success Criteria (5 min)

Ask: _"How will we know this is done? What metrics matter?"_
Document: 3–5 measurable criteria.

### 5. The Maturity Level (2 min)

Use the decision tree below to choose: Sketch / Contract / Blueprint.

---

## Maturity Level Decision Tree

```
Is this a ONE-FILE CHANGE (typo fix, small utility)?
  → Use SKETCH (write a one-page spec directly, 15–30 min)

Is this a MULTI-FILE FEATURE (new API endpoint, UI component, DB change)?
  → Use CONTRACT (full spec via create-specs, plan via create-plan, 1–2 hours)

Is this a PLATFORM/INFRASTRUCTURE CHANGE (new service, deployment, scaling)?
  → Use BLUEPRINT (Contract + ops runbook + monitoring, 2+ hours)

UNSURE?
  → Default to CONTRACT (sweet spot for most work)
```

### Maturity Definitions

**Sketch Maturity**:
- One-page spec (Goal + Acceptance Criteria only)
- 15–30 minute write time
- Does NOT require create-specs or create-plan sub-skills
- Use for: one-file changes, clear bug fixes, local tools, POC features
- Template: See [sketch-template.md](sketch-template.md)
- Proceed directly to Implementation Governance after writing

**Contract Maturity**:
- Full spec with REQ, AC, VAL, interfaces
- 1–2 hour write time (via create-specs skill)
- Plan via create-plan skill
- Use for: multi-file features, API changes, user-facing work
- **Default choice when uncertain**

**Blueprint Maturity**:
- Contract + architecture, deployment, monitoring, rollback plans
- 2+ hour write time
- Requires architecture documentation
- Use for: infrastructure, platform changes, compliance-critical work

---

## Scope Definition Examples

### Example 1 — Bad Scope

- Goal: "Improve authentication"
  Problem: Too broad. Which aspect? (UX, security, performance?)
- In scope: User login, password reset, 2FA, SAML, OAuth, session management
  Problem: Too much for one spec. Breaks into 3+ specs minimum.

### Example 1 — Good Scope

- Goal: "Add rate limiting to /api/login to defend against brute force"
- In scope: Count attempts per IP, return HTTP 429, reset after 60s
- Out of scope: CAPTCHA, account lockout, admin bypass, IP whitelisting
- Constraints: Use existing Redis instance; no new infrastructure
- Maturity: Contract (testable in staging)

### Example 2 — Bad Scope

- Goal: "Allow users to upload files"
  Problem: Missing constraints. Storage limit? File types? Max size? Where stored?

### Example 2 — Good Scope

- Goal: "Allow users to upload profile photos to their account"
- In scope: JPG/PNG, max 5MB, store in S3, visible only to user
- Out of scope: Batch uploads, photo cropping, CDN caching
- Constraints: Existing S3 bucket available; no cost increase allowed
- Maturity: Contract

---

## Red Flags in Scope

Ask follow-up questions if you see:

- Goal is vague ("improve X") → Ask: What specific behavior/metric changes?
- Scope has OR statements ("do X or Y") → Ask: Which is priority? Or do we need both?
- No constraints mentioned → Ask: Timeline? Tech stack? Budget?
- Acceptance criteria missing → Ask: How will we know it's done?

---

## Post-Interview Checklist

Before proceeding to the Specification Gate, verify:

- [ ] Goal is stated in one clear sentence
- [ ] In-scope and out-of-scope items are listed (at least 3 each)
- [ ] All constraints are identified (deadline, tech stack, team, compliance)
- [ ] Success criteria are measurable (not "look good")
- [ ] Maturity level is chosen (Sketch / Contract / Blueprint)
- [ ] (Recommended) Share your notes with a colleague to validate scope
