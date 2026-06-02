# auth

## 1. Goal

- Enable users to authenticate with JWT tokens.
- Completion signal: Users can obtain a JWT and access protected endpoints.

## 2. Requirements

- `REQ-001`: The system MUST issue a signed JWT on successful login.
- `REQ-002`: The system MUST reject requests missing a valid Bearer token with HTTP 401.

## 3. Constraints

- `CON-001`: The solution MUST NOT store tokens in plaintext.

## 4. Interfaces

The system exposes the following interfaces:

### POST /auth/login

**Input:**

- `email` (string, required): user email
- `password` (string, required): user password

**Output:**

- `token` (string): signed JWT

**Errors:**

- `400`: Missing fields
- `401`: Invalid credentials
- `500`: Internal error

## 5. Context

- Files: [src/auth.ts](src/auth.ts)
- Current behavior: No authentication exists yet.
- Conventions: Express middleware, TypeScript strict mode.

## 6. Acceptance Criteria & Validation

- `AC-001`: A valid login request returns HTTP 200 with a JWT token.
- `VAL-001`: `npm test -- auth.test.ts`

## 7. Examples & Edge Cases

- Valid credentials → 200 + token
- Wrong password → 401
