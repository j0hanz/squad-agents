# Interface Shapes: From Problem to Proposal

When deepening a module, you'll propose a "new interface shape." This guide shows what that means with concrete examples.

---

## What is an Interface Shape?

An **interface shape** describes:

- **What callers can ask the module to do** (methods, functions, exported types)
- **What data flows in and out** (types, invariants, error modes)
- **What callers DON'T need to know** (internal implementation)

---

## Example 1: Extracting Auth from Scattered Files

### Current State (Scattered, Bad Shape)

**Problem**: Auth logic is split across three files. Callers have to know about all of them.

```typescript
// auth.ts
export async function login(email: string, password: string) { ... }

// middleware.ts
export function authMiddleware() { ... }

// utils.ts
export function hashPassword(password: string) { ... }
export function verifyPassword(password: string, hash: string) { ... }
```

**Caller has to know about**:

- Where to import login from (auth.ts)
- That middleware needs to be wired into Express
- That there are utility functions they might need
- How to compose these pieces

**Interface shape is SHALLOW**: Caller's knowledge of how to use auth is as complex as auth's actual implementation.

---

### Proposed Shape (Centralized, Good)

**What the refactoring proposes**:

- Auth becomes ONE module with a clear boundary
- Callers only see domain-level operations (login, register, verify)
- Infrastructure concerns (Express middleware, password libraries) are hidden

```typescript
// auth/index.ts — THE INTERFACE
export type Credentials = { email: string; password: string };
export type Token = string;

export interface IUserLookup {
  findByEmail(email: string): Promise<User | null>;
}

export async function authenticate(
  lookup: IUserLookup,
  credentials: Credentials,
): Promise<Token>;

export async function register(
  lookup: IUserLookup,
  credentials: Credentials,
): Promise<{ user: User; token: Token }>;

export async function verifyToken(token: Token): Promise<{ userId: string }>;

// Internal (not exported)
// - Password hashing logic
// - JWT generation logic
// - All bcrypt, jsonwebtoken details

// Adapter (infra layer)
// - Express middleware that calls verifyToken
// - Database lookup that calls authenticate
```

**Caller now only needs to know**:

```typescript
import { authenticate } from "./auth";

const token = await authenticate(databaseLookup, {
  email: "user@example.com",
  password: "secret",
});
```

**Interface shape is DEEP**: Caller's knowledge is much simpler than the implementation.

**Leverage**: The caller went from knowing 3 things (login, middleware, hashPassword) to knowing 1 thing (authenticate). The auth module handles password complexity internally.

---

## Example 2: Breaking Up a God Module

### Current State (God Module, Bad Shape)

**Problem**: One 400-line `order.ts` does everything: validation, calculation, persistence, notification.

```typescript
// order.ts (EVERYTHING)
export async function createOrder(items: Item[], userId: string) {
  // Validation
  if (items.length === 0) throw new Error("...");

  // Calculation
  const subtotal = items.reduce((sum, item) => sum + item.price, 0);
  const tax = subtotal * 0.08;
  const total = subtotal + tax;

  // Database write
  const order = await db.orders.create({
    userId,
    items,
    subtotal,
    tax,
    total,
    createdAt: new Date(),
  });

  // Notification
  await emailQueue.publish("order.created", { orderId: order.id });

  // Logging
  logger.info(`Order ${order.id} created`);

  return order;
}
```

**Callers see all the concerns**: validation, calculation, persistence, side effects. Testing requires mocking database, email queue, and logger.

---

### Proposed Shape (Separated Concerns)

**The refactoring splits into DOMAIN MODULES**:

```typescript
// domain/order/order.ts — CALCULATION ONLY
export type OrderItem = { skuId: string; quantity: number; unitPrice: number };
export type PricedOrder = {
  subtotal: number;
  tax: number;
  total: number;
};

export function calculateOrderPrice(items: OrderItem[]): PricedOrder {
  const subtotal = items.reduce(
    (sum, item) => sum + item.unitPrice * item.quantity,
    0,
  );
  const tax = subtotal * 0.08;
  return { subtotal, tax, total: subtotal + tax };
}

export function validateItems(items: OrderItem[]): void {
  if (!items || items.length === 0) throw new Error("Order must have items");
  items.forEach((item) => {
    if (item.quantity <= 0) throw new Error("Quantity must be positive");
    if (item.unitPrice < 0) throw new Error("Price cannot be negative");
  });
}

// domain/order/order-repository.ts — INTERFACE (no implementation)
export interface IOrderRepository {
  save(order: {
    userId: string;
    items: OrderItem[];
    pricing: PricedOrder;
  }): Promise<Order>;
}

// domain/order/index.ts — WHAT THE CALLER SEES
export async function createOrder(
  repository: IOrderRepository,
  userId: string,
  items: OrderItem[],
): Promise<Order> {
  validateItems(items);
  const pricing = calculateOrderPrice(items);
  return repository.save({ userId, items, pricing });
}

export { validateItems, calculateOrderPrice };
export type { OrderItem, PricedOrder };
```

```typescript
// infra/postgres-order-repository.ts — INFRASTRUCTURE ADAPTER
import { IOrderRepository } from "../domain/order/order-repository";
import { db } from "./db";

export class PostgresOrderRepository implements IOrderRepository {
  async save(order: {
    userId: string;
    items: OrderItem[];
    pricing: PricedOrder;
  }): Promise<Order> {
    return db.orders.create({
      userId: order.userId,
      items: order.items,
      subtotal: order.pricing.subtotal,
      tax: order.pricing.tax,
      total: order.pricing.total,
      createdAt: new Date(),
    });
  }
}

// infra/order-workflow.ts — ORCHESTRATOR
import { createOrder } from "../domain/order";
import { PostgresOrderRepository } from "./postgres-order-repository";
import { emailQueue } from "./email-queue";
import { logger } from "./logger";

export async function createOrderWorkflow(userId: string, items: OrderItem[]) {
  const repository = new PostgresOrderRepository();
  const order = await createOrder(repository, userId, items);

  // Side effects (logging, notifications) happen HERE, not in domain
  await emailQueue.publish("order.created", { orderId: order.id });
  logger.info(`Order ${order.id} created`);

  return order;
}
```

**Caller sees simple interface**:

```typescript
import { createOrder } from "./domain/order";
import { PostgresOrderRepository } from "./infra/postgres-order-repository";

const repository = new PostgresOrderRepository();
const order = await createOrder(repository, userId, items);
```

**Tests see pure domain**:

```typescript
import {
  createOrder,
  validateItems,
  calculateOrderPrice,
} from "../domain/order";
import { IOrderRepository } from "../domain/order/order-repository";

class MockRepository implements IOrderRepository {
  async save(order) {
    return { id: "123", ...order };
  }
}

test("calculateOrderPrice adds tax correctly", () => {
  const price = calculateOrderPrice([
    { skuId: "A", quantity: 2, unitPrice: 10 },
  ]);
  expect(price.tax).toBe(1.6); // 20 * 0.08
  expect(price.total).toBe(21.6);
});

test("createOrder fails if items is empty", async () => {
  const repo = new MockRepository();
  await expect(createOrder(repo, "user1", [])).rejects.toThrow(
    "Order must have items",
  );
});
```

---

## Example 3: Adding a Seam for Adapters

### Current State (Coupled, Bad Shape)

**Problem**: Billing directly calls Stripe. Hard to test, hard to swap payment providers.

```typescript
import Stripe from "stripe";

export async function charge(amount: number, customerId: string) {
  const stripe = new Stripe(API_KEY);
  const charge = await stripe.charges.create({
    amount: Math.round(amount * 100),
    currency: "usd",
    customer: customerId,
  });
  return { transactionId: charge.id, status: charge.status };
}
```

**Caller knows about Stripe**: If we want to switch to PayPal, code changes everywhere.

---

### Proposed Shape (Seam for Adapters)

**The refactoring introduces a PAYMENT INTERFACE**:

```typescript
// domain/payment/payment.ts — WHAT CALLERS DEPEND ON
export type ChargeRequest = {
  amount: number;
  customerId: string;
  description?: string;
};

export type ChargeResult = {
  transactionId: string;
  status: "pending" | "succeeded" | "failed";
};

export interface IPaymentProcessor {
  charge(request: ChargeRequest): Promise<ChargeResult>;
}

export async function charge(
  processor: IPaymentProcessor,
  request: ChargeRequest,
): Promise<ChargeResult> {
  if (request.amount <= 0) throw new Error("Amount must be positive");
  return processor.charge(request);
}

// domain/payment/index.ts
export { charge };
export type { ChargeRequest, ChargeResult };
export { IPaymentProcessor };
```

```typescript
// infra/stripe-processor.ts — STRIPE ADAPTER
import Stripe from "stripe";
import {
  IPaymentProcessor,
  ChargeRequest,
  ChargeResult,
} from "../domain/payment";

export class StripeProcessor implements IPaymentProcessor {
  private stripe: Stripe;

  constructor(apiKey: string) {
    this.stripe = new Stripe(apiKey);
  }

  async charge(request: ChargeRequest): Promise<ChargeResult> {
    const result = await this.stripe.charges.create({
      amount: Math.round(request.amount * 100),
      currency: "usd",
      customer: request.customerId,
    });
    return {
      transactionId: result.id,
      status: result.status as "pending" | "succeeded" | "failed",
    };
  }
}

// infra/paypal-processor.ts — PAYPAL ADAPTER (same interface)
import paypalSdk from "@paypal/checkout-server-sdk";
import {
  IPaymentProcessor,
  ChargeRequest,
  ChargeResult,
} from "../domain/payment";

export class PayPalProcessor implements IPaymentProcessor {
  // ... similar implementation
}
```

**Caller is unaffected by processor choice**:

```typescript
import { charge } from "./domain/payment";
import { StripeProcessor } from "./infra/stripe-processor";
// or
import { PayPalProcessor } from "./infra/paypal-processor";

const processor = new StripeProcessor(apiKey);
// or new PayPalProcessor(...)

const result = await charge(processor, {
  amount: 99.99,
  customerId: "cust_123",
});
```

**Tests can use a mock processor**:

```typescript
class MockProcessor implements IPaymentProcessor {
  async charge(request) {
    return { transactionId: "mock_123", status: "succeeded" };
  }
}

test("order finalizes when payment succeeds", async () => {
  const result = await charge(new MockProcessor(), {
    amount: 50,
    customerId: "test",
  });
  expect(result.status).toBe("succeeded");
});
```

**Swapping Stripe for PayPal**:

```typescript
// Before: everywhere imports 'stripe'
// After: one line changes
const processor = new PayPalProcessor(apiKey); // was StripeProcessor
```

---

## Interface Shape Checklist

When proposing a new shape, ask:

- [ ] **Can I test the domain without the infrastructure?** (use mocks/adapters)
- [ ] **Do callers need to import from multiple files?** (should be one or two)
- [ ] **Are infrastructure details hidden?** (callers don't see Stripe, database, Express)
- [ ] **Can I swap adapters without touching domain code?** (new processor = new implementation of interface)
- [ ] **Do types describe intent, not mechanism?** (ChargeRequest, not StripeChargeParams)
- [ ] **Is the interface smaller than the implementation?** (yes = deep, no = shallow)

If any answer is "no," the shape needs adjustment.
