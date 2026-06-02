# auth-jwt

## 1. Goal

- Enable users to authenticate with JWT tokens.
- Completion signal: Users can obtain a JWT and access protected endpoints with it.

## 2. Requirements

- `REQ-001`: The system MUST issue a signed JWT on successful login with valid credentials.
- `REQ-002`: The system MUST reject requests with a missing or expired Bearer token with HTTP 401.
- `SEC-001`: Tokens MUST expire after 3600 seconds and MUST be signed with HS256.

## 3. Constraints

- `CON-001`: The solution MUST NOT store plaintext passwords or tokens in the database.

## 4. Interfaces

The system exposes the following interfaces:

### POST /auth/login

**Input:**

- `email` (string, required): User email address
- `password` (string, required): User password

**Output:**

- `token` (string): Signed JWT valid for 3600 seconds

**Errors:**

- `400`: Missing or invalid fields
- `401`: Invalid credentials
- `500`: Internal server error

## 5. Context

- Files: [src/auth.ts](src/auth.ts)
- Current behavior: No authentication exists; all endpoints are public.
- Conventions: Express middleware pattern; async/await; TypeScript strict mode.

## 6. Acceptance Criteria & Validation

- `AC-001`: A POST /auth/login with valid credentials returns HTTP 200 and a non-empty JWT token.
- `AC-002`: A request to a protected endpoint without a Bearer token returns HTTP 401.
- `VAL-001`: `npm test -- auth.test.ts`

## 7. Examples & Edge Cases

**Positive example:**

```
Input:  POST /auth/login { "email": "user@example.com", "password": "secret" }
Output: 200 { "token": "<jwt>" }
```

**Edge cases:**

- Wrong password → 401
- Missing email field → 400
- Expired token on protected endpoint → 401
