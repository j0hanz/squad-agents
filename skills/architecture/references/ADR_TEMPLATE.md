# Architecture Decision Record (ADR) Template

Use this template to record architectural decisions that should not be revisited without explicit reasoning.

**When to write an ADR:**

- When rejecting a refactoring for load-bearing reasons (not "not worth it right now")
- When establishing a boundary that future explorations should respect
- When a refactoring contradicts a previous decision

---

## Template

```markdown
# ADR-NNNN: [Short Title]

**Date**: YYYY-MM-DD
**Status**: [Accepted | Superseded | Deprecated]

## Problem

[1-2 sentences describing the architectural tension or constraint that prompted this decision]

Example: "We've been treating order management and payment processing as separate domains, but they're tightly coupled. We need to decide whether to:
1. Merge them into a single OrderPayment module
2. Keep them separate with explicit boundaries and message passing"

## Decision

[Plain English explanation of what we decided]

Example: "Keep Order and Payment as separate domain modules with unidirectional dependency (Order → Payment, never Payment → Order). The orchestrator (order-workflow) composes both without circular coupling."

## Rationale

[Why this decision is better than alternatives. Include trade-offs.]

Example: "Separating these domains lets us test each in isolation, reuse Payment for refunds/disputes, and split into separate services later if needed. The tradeoff is that Order doesn't 'know' the full payment lifecycle — it delegates to an adapter."

## Implications

[What this means for future refactoring, testing, and new feature work]

Example:
- Order logic never imports from Payment
- Payment adapters (Stripe, PayPal, etc.) live in infra/, not domain/
- Any feature touching both Order and Payment must go through order-workflow orchestrator
- Tests can mock payment without a real provider

## Related Issues

[Link to relevant GitHub issues, tickets, or ADRs]

Example: "Supersedes ADR-0003 (merge Order and Payment)"

---

# Examples

## ADR-0001: Auth Domain Boundaries

**Status**: Accepted

**Problem**: Authentication logic is scattered: password hashing in auth.ts, JWT in middleware.ts, user lookup in routes.ts. Every change touches multiple files. Testing is impossible without a database.

**Decision**: Centralize authentication in a domain module with three parts: password (pure functions), tokens (pure functions), and authenticate (orchestrator). All infrastructure adapters (Express middleware, database calls) go in infra/.

**Rationale**: This lets us test password and token logic without any dependencies. Authenticate can be tested with mock user objects. Future auth methods (OAuth, SAML) can be added as new adapters without changing domain code.

**Implications**:
- Domain code never imports Express, database drivers, or external libraries
- All password hashing is tested with bcrypt behavior captured in tests
- Routes import from infra/auth-adapter, not directly from domain/auth
- Middleware is thin and delegates to domain

**Related Issues**: Ticket AUTH-45, ADR-0007 (API layer seams)

---

## ADR-0002: Repository Interfaces for Data Access

**Status**: Accepted

**Problem**: Domain logic imports Prisma directly. To test order logic, we need a Postgres database running. This blocks tests from running in parallel and slows CI.

**Decision**: All data access goes through interfaces. Domain code takes a Repository interface (findUserByEmail, storeNewUser). Concrete repositories (PostgresUserRepository, InMemoryUserRepository) are in infra/. Tests use InMemoryUserRepository.

**Rationale**: Interfaces decouple domain from infrastructure. Tests don't need a database. We can swap Postgres for MongoDB without touching domain code.

**Implications**:
- Domain modules have interfaces (IUserRepository, IOrderRepository)
- Tests instantiate in-memory adapters
- Production wires up concrete database adapters
- New queries don't require database migrations to test

---

## ADR-0003: No Circular Dependencies Between Domain Modules

**Status**: Accepted

**Problem**: Order imports Payment, Payment imports Order (event notifications). We can't test Order without Payment, and the cycle makes future service split difficult.

**Decision**: Dependencies between domain modules flow in one direction (or are eliminated). If two modules need to communicate, use an orchestrator (e.g., order-workflow) or event bus in infrastructure. The event bus is infrastructure, not domain.

**Rationale**: Linear dependencies are easier to reason about, test, and split. Cycles hide coupling and make refactoring risky.

**Implications**:
- No `import { notifyOrderCreated } from '../order'` from within payment
- Orchestrators in infra/ compose domain modules
- Events emitted in infra/ to decouple producers from listeners
- Code review should catch any reverse imports

---

## ADR-0004: Utils Folder is Forbidden

**Status**: Accepted

**Problem**: We had a utils/ folder with 200 functions: date helpers, string formatters, validators, API response builders. No one could find anything. Dependencies were tangled.

**Decision**: Reorganize by domain. Date utilities live in domain/calendar/. Validators in domain/validation/. This makes each module self-contained and improves code locality.

**Rationale**: Domain organization reflects how the code is actually used. Date logic stays with features that use it. New developers can understand a module by reading one folder, not jumping between domain and utils.

**Implications**:
- No more /utils folder
- Duplication is OK if it improves locality (a simple dateToIso function can be defined in two modules)
- Small, focused utility modules are OK if they're in the domain they serve (e.g., order/order-utils.ts)

---
```

## Tips for Writing ADRs

- **Assume the decision will be revisited in 2 years.** Write clearly enough that future-you understands why this was chosen.
- **Distinguish load-bearing reasons from aesthetic ones.** "Testability" is load-bearing. "I prefer this structure" is not.
- **Record the problem, not the solution.** Future teams might solve it differently.
- **Link to related decisions.** If you're superseding another ADR, say so explicitly.
- **Implications are the key.** They tell future explorers what not to do.
