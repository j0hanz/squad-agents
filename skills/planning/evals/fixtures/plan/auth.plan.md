# auth

Spec: [auth.specs.md](auth.specs.md)

## Goal

Enable users to authenticate with JWT tokens.

## PHASE-001: Implementation

### TASK-001: Implement REQ-001

Depends on: none
Files: [src/auth.ts](src/auth.ts)
Symbols: [issueJwt](src/auth.ts#L1)
Satisfies: REQ-001
Action: Implement JWT issuance on successful login in the auth handler.
Validate: `npm test -- auth.test.ts`
Expected result: POST /auth/login returns 200 with a signed JWT for valid credentials.

### TASK-002: Implement REQ-002

Depends on: [TASK-001](#task-001-implement-req-001)
Files: [src/middleware/auth.ts](src/middleware/auth.ts)
Symbols: [requireAuth](src/middleware/auth.ts#L1)
Satisfies: REQ-002
Action: Implement Bearer token middleware that rejects missing or invalid tokens with 401.
Validate: `npm test -- auth.test.ts`
Expected result: Requests without a valid Bearer token receive HTTP 401.

## PHASE-END: Acceptance

### TASK-003: Final acceptance verification

Depends on: [TASK-002](#task-002-implement-req-002)
Files: none
Symbols: none
Satisfies: AC-001
Action: Verify all Acceptance Criteria from spec are observable in the running system.
Validate: `npm test -- auth.test.ts`
Expected result: All AC items confirmed observable.
