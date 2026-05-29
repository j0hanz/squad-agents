# C4 Model: Heuristics & Decision Trees

Do not explain what C4 is. Apply these heuristics to solve modeling ambiguities and architectural tangles.

---

## ANTI-PATTERN: The God Diagram (>20 Nodes)

**Early Detection** — Before designing any C4 diagram, count the components:

- **Red flags** (indicates >20 nodes):
  - User lists >15 microservices
  - User mentions "all services connect to a central [database/message bus]"
  - User says "I want to show the entire architecture"
  - System has both frontend/backend/infrastructure AND databases for each

- **Action**: If you detect >20 nodes, IMMEDIATELY propose splitting into **L1 Context + multiple L2 Container diagrams**.
  - **Do not ask permission**; splitting is mandatory.
  - Output: "This architecture has 25+ components. I'll split this into:
    1. **Context Diagram** (high-level view with Person + main Systems only)
    2. **Component Diagram 1: Order Processing** (Order microservices + dependencies)
    3. **Component Diagram 2: Payment** (Payment services + Stripe integration)
    4. **Component Diagram 3: Inventory** (Stock management + sync)"

- **Context Diagram** (Level 1) should show ONLY:
  - `Person` (the user)
  - `[Your System]` (the primary application)
  - External Systems (Stripe, Auth0, Twilio, etc.)
  - High-level data flows between them

- **Container Diagrams** (Level 2, multiple) should show:
  - One domain/bounded context per diagram
  - <10 components per diagram
  - Internal microservices, databases, queues within that domain
  - Clear interfaces to other domains

**Example**:

```
Architecture has 28 components. Auto-split:

CONTEXT (L1):
  Person → [SaaS App] ← Stripe, Auth0, Twilio, S3

ORDER PROCESSING (L2):
  API Gateway → OrderService → OrderDB
                            → PaymentQueue → [to Payment domain]
                            → InventoryQueue → [to Inventory domain]

PAYMENT (L2):
  PaymentQueue → PaymentService → Stripe
                              → PaymentDB

INVENTORY (L2):
  InventoryQueue → InventoryService → InventoryDB
```

---

## Decision Tree: Boundary Strategies

When mapping out an architecture, determine the boundary strategy based on system scale:

- **Condition**: The system has < 10 deployable units.
  - **Action**: Use a single C4 Container diagram. Group related components in logical boundaries.
- **Condition**: The system has > 10 but < 30 deployable units.
  - **Action**: Create a C4 System Context diagram first. Group microservices into `System` boundaries (e.g., `Billing System`, `Fulfillment System`).
- **Condition**: The system has > 30 microservices.
  - **Action**: NEVER draw this in one diagram. Create a Context diagram of the core domains. Then, offer to generate separate Container diagrams for each specific domain.

## Heuristic: Handling API Gateways and BFFs

- **Trap**: Showing every single microservice connecting directly to the frontend, resulting in overlapping spaghetti.
- **Expert Move**: Model the BFF (Backend For Frontend) or API Gateway as a distinct Container. Route UI traffic through it. If the Gateway performs aggregation, rate limiting, or auth validation, explicitly note it in the container's description field.

## Heuristic: Resolving Ambiguous "Databases"

- **Trap**: Modeling a single massive `Database` node that every service connects to (The Monolithic Database Anti-Pattern).
- **Expert Move**: If microservices share a database, represent the database node once but clearly show multiple services accessing it (highlighting the coupling). If the architecture is strictly decoupled (database-per-service), verify that each service has its own dedicated datastore node. Ask the user to clarify if the datastore is shared or isolated before drawing if it is ambiguous.

## Pattern: CQRS Separation

When a system handles heavy reads and complex writes:

1. Split the Container diagram into `Write Path` and `Read Path` boundaries.
2. Explicitly model the synchronization mechanism (e.g., Kafka event bus, Debezium CDC) between the write datastore and the read-optimized projection.
3. Show the UI explicitly calling the Command API for mutations and the Query API for reads.
