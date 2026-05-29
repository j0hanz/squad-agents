# Seams by Example

A **seam** is a boundary where behavior can be altered without editing code in place. This guide shows good and bad seams with real code examples.

---

## Example 1: Authentication Seam (Good)

**Bad seam** — logic scattered across files:

```typescript
// auth.ts
import * as bcrypt from "bcrypt";
import { db } from "./db";

export async function login(email: string, password: string) {
  const user = await db.users.findOne({ email });
  if (!user) throw new Error("Not found");
  const match = await bcrypt.compare(password, user.hash);
  if (!match) throw new Error("Invalid password");
  return { token: jwt.sign({ userId: user.id }) };
}

// middleware.ts
import * as jwt from "jsonwebtoken";
app.use((req, res, next) => {
  const token = req.headers.authorization?.split(" ")[1];
  const decoded = jwt.verify(token, SECRET);
  req.userId = decoded.userId;
  next();
});

// routes.ts
import { login } from "./auth";
app.post("/login", async (req, res) => {
  const result = await login(req.body.email, req.body.password);
  res.json(result);
});
```

**What's wrong?**

- Password hashing logic is mixed with user lookup
- JWT generation is in a middleware file (not with login logic)
- Routes directly call domain logic without abstraction
- Testing `login()` requires a database
- Circular dependencies possible (middleware imports from auth, routes import auth)

**Good seam** — logic centralized with clear boundaries:

```typescript
// auth/password.ts (pure domain)
export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(
  password: string,
  hash: string,
): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

// auth/tokens.ts (pure domain)
export function generateToken(userId: string): string {
  return jwt.sign({ userId }, process.env.JWT_SECRET);
}

export function verifyToken(token: string): { userId: string } {
  return jwt.verify(token, process.env.JWT_SECRET) as { userId: string };
}

// auth/authenticate.ts (orchestrator, still domain)
import { verifyPassword, hashPassword } from "./password";
import { generateToken } from "./tokens";
import { User } from "./types"; // Define User type here

export class AuthenticationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthenticationError";
  }
}

export async function login(
  user: User, // User object passed in (no db coupling)
  passwordAttempt: string,
): Promise<{ token: string }> {
  const isValid = await verifyPassword(passwordAttempt, user.passwordHash);
  if (!isValid) throw new AuthenticationError("Invalid password");
  return { token: generateToken(user.id) };
}

export async function register(
  email: string,
  password: string,
): Promise<{ token: string }> {
  const hash = await hashPassword(password);
  return { hash, token: generateToken(email) };
}

// auth/index.ts (seam: adapters go here)
export * from "./authenticate";
export * from "./password";
export * from "./tokens";

// infra/auth-middleware.ts (adapter)
import { verifyToken } from "../auth";

export function createAuthMiddleware() {
  return (req, res, next) => {
    try {
      const token = req.headers.authorization?.split(" ")[1];
      const decoded = verifyToken(token);
      req.userId = decoded.userId;
      next();
    } catch (e) {
      res.status(401).json({ error: "Unauthorized" });
    }
  };
}

// infra/users-repository.ts (adapter)
import { db } from "./db";
import { login } from "../auth";

export async function loginUser(email: string, password: string) {
  const user = await db.users.findOne({ email });
  if (!user) throw new Error("User not found");
  return login(user, password); // Auth domain doesn't know about DB
}

// routes/auth-routes.ts (handler)
import { loginUser } from "../infra/users-repository";

app.post("/login", async (req, res) => {
  try {
    const result = await loginUser(req.body.email, req.body.password);
    res.json(result);
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});
```

**What's better?**

- Password logic is pure and testable without bcrypt knowledge
- Token logic is pure and testable without database or Express
- Domain `login()` function takes a user object (not a database call)
- Adapters bridge between domain and infrastructure
- One adapter (`users-repository.ts`) calls the database, then passes user to domain logic
- Tests can mock user objects without database

**The seam**: Between `auth/` (domain) and `infra/` (adapters). Domain doesn't import infra. Infra imports domain.

---

## Example 2: Payment Processing Seam (Circular Dependency Violation)

**Bad seam** — circular coupling:

```typescript
// order/order-service.ts
import { processPayment } from "../payment/payment-service";

export async function createOrder(items) {
  const total = calculateTotal(items);
  const payment = await processPayment(total); // Order → Payment
  return { orderId: newId(), paymentId: payment.id };
}

// payment/payment-service.ts
import { notifyOrderCreated } from "../order/order-service";

export async function processPayment(amount) {
  const result = await chargeCard(amount);
  await notifyOrderCreated(result.orderId); // Payment → Order (CYCLE!)
  return result;
}
```

**Problem**: Order depends on Payment, Payment depends on Order. You can't:

- Test Order without Payment
- Test Payment without Order
- Split them into separate services
- Reuse Payment for other features

**Good seam** — dependency flows one direction:

```typescript
// domain/order/order.ts (pure domain)
export type OrderCreated = { orderId: string; paymentRequired: number };

export function createOrder(items: Item[]): OrderCreated {
  return {
    orderId: generateId(),
    paymentRequired: calculateTotal(items),
  };
}

// domain/payment/payment.ts (pure domain)
export type PaymentProcessed = { transactionId: string; amount: number };

export async function processPayment(
  amount: number,
): Promise<PaymentProcessed> {
  return {
    transactionId: generateId(),
    amount,
  };
}

// infra/order-workflow.ts (orchestrator, NOT domain)
import { createOrder } from "../domain/order/order";
import { processPayment } from "../domain/payment/payment";
import { db } from "./db";

export async function createOrderWorkflow(items: Item[]) {
  // Step 1: Create order (pure domain)
  const orderCreated = createOrder(items);

  // Step 2: Process payment (pure domain)
  const payment = await processPayment(orderCreated.paymentRequired);

  // Step 3: Persist (infrastructure)
  const order = await db.orders.create({
    id: orderCreated.orderId,
    paymentId: payment.transactionId,
    items,
  });

  // Step 4: Emit event (infrastructure, decouples workflow from listeners)
  await eventBus.emit("order.created", { orderId: order.id });

  return order;
}

// routes/orders.ts
import { createOrderWorkflow } from "../infra/order-workflow";

app.post("/orders", async (req, res) => {
  const order = await createOrderWorkflow(req.body.items);
  res.json(order);
});
```

**The seam**: Between domain modules (order, payment) and orchestrator (order-workflow). Each domain module is testable in isolation. Workflow composes them.

---

## Example 3: Repository Seam (Shallow vs. Deep)

**Shallow seam** — wrapper adds little value:

```typescript
// repositories/user-repository.ts
export class UserRepository {
  findById(id: string) {
    return db.users.findOne({ id });
  }
  findByEmail(email: string) {
    return db.users.findOne({ email });
  }
  create(email: string, hash: string) {
    return db.users.create({ email, passwordHash: hash });
  }
  update(id: string, data: any) {
    return db.users.update(id, data);
  }
}
```

**Why it's shallow**: The interface is nearly as complex as the implementation. Callers still know about the database. Deletion test: if we deleted this class, logic would just move to the caller.

**Deep seam** — abstraction captures domain logic:

```typescript
// domain/user/user.ts
export type User = {
  id: string;
  email: string;
  passwordHash: string;
  lastLogin?: Date;
};

// domain/user/user-repository.ts (abstract)
export interface IUserRepository {
  findUserByEmail(email: string): Promise<User | null>;
  storeNewUser(email: string, passwordHash: string): Promise<User>;
}

// infra/postgres-user-repository.ts (concrete adapter)
import { IUserRepository } from "../domain/user/user-repository";
import { db } from "./db";

export class PostgresUserRepository implements IUserRepository {
  async findUserByEmail(email: string): Promise<User | null> {
    return db.users.findOne({ email });
  }

  async storeNewUser(email: string, passwordHash: string): Promise<User> {
    return db.users.create({ email, passwordHash });
  }
}

// infra/in-memory-user-repository.ts (alternative adapter for testing)
import { IUserRepository } from "../domain/user/user-repository";

export class InMemoryUserRepository implements IUserRepository {
  private store: Map<string, User> = new Map();

  async findUserByEmail(email: string): Promise<User | null> {
    return [...this.store.values()].find((u) => u.email === email) || null;
  }

  async storeNewUser(email: string, passwordHash: string): Promise<User> {
    const user = { id: generateId(), email, passwordHash };
    this.store.set(user.id, user);
    return user;
  }
}

// domain/auth/authenticate.ts (uses interface, not concrete impl)
export async function register(
  repo: IUserRepository,
  email: string,
  password: string,
): Promise<User> {
  const existing = await repo.findUserByEmail(email);
  if (existing) throw new Error("Already registered");

  const hash = await hashPassword(password);
  return repo.storeNewUser(email, hash);
}

// test/auth.test.ts
import { register } from "../domain/auth/authenticate";
import { InMemoryUserRepository } from "../infra/in-memory-user-repository";

test("register creates new user", async () => {
  const repo = new InMemoryUserRepository();
  const user = await register(repo, "test@example.com", "password123");
  expect(user.email).toBe("test@example.com");
  // No database needed!
});
```

**Why it's deep**:

- Interface hides database details from domain logic
- Callers (auth logic) don't know whether repository is in-memory or Postgres
- Tests can use in-memory repo, production uses Postgres
- Adding a cache adapter doesn't require changing domain code
- Deletion test: if we deleted the repository abstraction, logic would bleed everywhere

**The seam**: Between domain code (authenticate.ts) and infrastructure adapters (PostgresUserRepository, InMemoryUserRepository).

---

## Seam Test Checklist

When evaluating a seam:

- [ ] Can business logic be tested without infrastructure (database, HTTP, filesystem)?
- [ ] Does the interface name describe what it does, not how it works?
- [ ] Can you swap the implementation without changing callers?
- [ ] Does deletion move complexity, not eliminate it?
- [ ] Are dependencies flowing in one direction (or not circular)?

If any answer is "no," the seam is drawn at the mechanism layer, not the domain layer. Redraw it.
