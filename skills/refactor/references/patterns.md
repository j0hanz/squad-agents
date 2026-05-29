# Structural Refactoring Patterns

When to use each pattern, and what the before/after looks like. These are not templates to copy — they're recipes to adapt.

---

## Strategy

**When to use:** A function has a large if/switch on a "type" field and each branch does a similar-shaped thing. New variants are expected over time.

**Before:**

```ts
function calculateShipping(order: Order, method: string): number {
  if (method === "standard") return order.total > 50 ? 0 : 5.99;
  if (method === "express") return order.total > 100 ? 9.99 : 14.99;
  if (method === "overnight") return 29.99;
  throw new Error("Unknown method");
}
```

**After:**

```ts
interface ShippingStrategy {
  calculate(order: Order): number;
}

const strategies: Record<string, ShippingStrategy> = {
  standard: { calculate: (o) => (o.total > 50 ? 0 : 5.99) },
  express: { calculate: (o) => (o.total > 100 ? 9.99 : 14.99) },
  overnight: { calculate: () => 29.99 },
};

function calculateShipping(order: Order, method: string): number {
  const strategy = strategies[method];
  if (!strategy) throw new Error(`Unknown method: ${method}`);
  return strategy.calculate(order);
}
```

**Payoff:** Adding a new shipping method = adding one entry to the map. No existing code changes.

---

## Null Object

**When to use:** Code is full of `if (x !== null)` guards around an optional object. The absent case has a default/no-op behavior.

**Before:**

```ts
function renderUser(user: User | null) {
  if (user === null) {
    return "<Anonymous>";
  }
  return `${user.firstName} ${user.lastName}`;
}

function getUserPermissions(user: User | null): string[] {
  if (user === null) return [];
  return user.permissions;
}
```

**After:**

```ts
const ANONYMOUS_USER: User = {
  firstName: "Anonymous",
  lastName: "",
  permissions: [],
};

function renderUser(user: User) {
  return `${user.firstName} ${user.lastName}`.trim() || "Anonymous";
}

function getUserPermissions(user: User): string[] {
  return user.permissions;
}

// Callers pass ANONYMOUS_USER instead of null
```

**Payoff:** Eliminates null checks at callsites. The "absent" case is explicit and typed.

---

## Builder

**When to use:** An object has many optional fields; constructors with many arguments that are often partially null; test setup code that's hard to read.

**Before:**

```ts
const report = new Report(
  "Q4 Summary",
  new Date("2024-10-01"),
  new Date("2024-12-31"),
  true,
  null,
  "pdf",
  ["sales", "marketing"],
  null,
);
```

**After:**

```ts
const report = Report.builder("Q4 Summary")
  .dateRange(new Date("2024-10-01"), new Date("2024-12-31"))
  .includeCharts(true)
  .format("pdf")
  .sections(["sales", "marketing"])
  .build();
```

**Payoff:** Self-documenting, optional fields are explicit, easy to read in tests.

---

## Command

**When to use:** Operations need to be queued, logged, undone, or retried. Logic is currently inline and hard to test in isolation.

**Before:**

```ts
// Scattered across UI handlers
async function onSave() {
  await db.update(user);
  await audit.log("user.update", user);
  await cache.invalidate(`user:${user.id}`);
}
```

**After:**

```ts
interface Command {
  execute(): Promise<void>;
  undo(): Promise<void>;
}

class UpdateUserCommand implements Command {
  constructor(
    private db: DB,
    private audit: Audit,
    private cache: Cache,
    private user: User,
  ) {}

  async execute() {
    await this.db.update(this.user);
    await this.audit.log("user.update", this.user);
    await this.cache.invalidate(`user:${this.user.id}`);
  }

  async undo() {
    /* restore previous state */
  }
}
```

**Payoff:** Testable, composable, undoable. Decouples "what to do" from "when to do it."

---

## Chain of Responsibility

**When to use:** A sequence of checks/filters where each can handle or pass along a request. Validation pipelines, middleware, permission checks.

**Before:**

```ts
function validate(user: User): string[] {
  const errors: string[] = [];
  if (!user.email) errors.push("Email required");
  else if (!isValidEmail(user.email)) errors.push("Invalid email");
  if (!user.name) errors.push("Name required");
  if (user.age < 18) errors.push("Must be 18+");
  if (user.country === "blocked") errors.push("Country not supported");
  return errors;
}
```

**After:**

```ts
type Validator = (user: User) => string | null;

const validators: Validator[] = [
  (u) => (!u.email ? "Email required" : null),
  (u) => (u.email && !isValidEmail(u.email) ? "Invalid email" : null),
  (u) => (!u.name ? "Name required" : null),
  (u) => (u.age < 18 ? "Must be 18+" : null),
  (u) => (u.country === "blocked" ? "Country not supported" : null),
];

function validate(user: User): string[] {
  return validators.map((v) => v(user)).filter((e): e is string => e !== null);
}
```

**Payoff:** Each rule is independently testable and readable. Adding a rule = adding one entry.

---

## Observer / Event Bus

**When to use:** An action in one place needs to trigger reactions in several unrelated places. Tight coupling via direct calls is making the code brittle.

**Before:**

```ts
async function createOrder(data: OrderData) {
  const order = await db.orders.create(data);
  await emailService.sendConfirmation(order);
  await inventoryService.reserve(order.items);
  await analyticsService.track("order.created", order);
  return order;
}
```

**After:**

```ts
async function createOrder(data: OrderData) {
  const order = await db.orders.create(data);
  await eventBus.emit("order.created", order);
  return order;
}

// Each listener registered independently:
eventBus.on("order.created", (order) => emailService.sendConfirmation(order));
eventBus.on("order.created", (order) => inventoryService.reserve(order.items));
eventBus.on("order.created", (order) =>
  analyticsService.track("order.created", order),
);
```

**Payoff:** `createOrder` doesn't need to know what reacts. New side effects add without changing the core.

**Caution:** Over-use leads to "magic" behavior that's hard to trace. Use when the decoupling is genuinely valuable, not just to avoid an import.
