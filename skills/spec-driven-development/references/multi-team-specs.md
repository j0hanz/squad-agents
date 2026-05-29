# Spec-Driven Development Across Multiple Teams

When your feature depends on other teams' work (backend API, data schema, infrastructure),
this guide explains how to coordinate specs and timelines.

## Interface Discovery

**Step 1**: Identify what your feature depends on.

```
My feature: User dashboard with real-time data
Depends on:
  - Backend team: GET /api/analytics endpoint (data schema TBD)
  - Data team: Snowflake query (performance target: <1s)
  - DevOps: Snowflake VPC connectivity (not yet provisioned)
```

**Step 2**: Find the owner's spec.

For each dependency, ask:
- Does the owning team have a spec for this?
- If yes, get a copy
- If no, ask them to create one before you finalize yours

**Step 3**: Align interfaces.

```
Their spec (Backend team):
  GET /api/analytics?metric={metric}&window={hours}
  Returns: { metric_name, value, timestamp, unit }

Your spec (Dashboard):
  REQ: Dashboard MUST display metrics in real-time
  Depends on: Backend API (schema matches spec-analytics-api v1.0)
```

If your requirements don't match their interface:
- Option A: Adjust your requirements
- Option B: Ask them to extend their spec
- Option C: Add a translation layer (adapter)

---

## Timeline Coordination

In the Planning phase, model dependencies explicitly:

```
PHASE-001: Infrastructure
  TASK-001: Request Snowflake VPC from DevOps
           Depends on: (external) spec-devops-snowflake
           Owner: DevOps team
           ETA: 2026-05-30

PHASE-002: Core Dashboard
  TASK-002: Build dashboard UI
           Depends on: TASK-001 (VPC ready)
           Your team

  TASK-003: Integrate with /api/analytics
           Depends on: TASK-002, (external) spec-analytics-api
           Your team
           Blocked until: Backend team ships spec-analytics-api (ETA: 2026-05-25)
```

**If external ETA slips**: Your plan automatically flags the risk.

---

## Breaking Changes

If your spec requires a breaking change to an existing interface:

1. **Document as REQ**:
   ```
   REQ-X: Requires v2 of spec-analytics-api (breaking change from v1)
   ```

2. **Coordinate timeline**:
   - When will owning team ship v2?
   - When is v1 deprecated?

3. **Plan for contingency**:
   ```
   TASK-Y: Support both /api/analytics/v1 and v2 (adapter)
           Until: v1 is deprecated (date TBD)
   ```

---

## Spec Synchronization

Keep specs in sync across teams:

**Weekly**: 
- Link to dependency specs in your spec (comments or cross-references)
- Alert if dependencies have changed

**Before implementation**: 
- Confirm dependency specs are validated and stable
- Document interface versions

**After changes**: 
- Update dependent specs to reflect new interfaces
- Notify teams who depend on you
