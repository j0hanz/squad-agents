# Class Diagrams (DDD): Boundary Heuristics

Focus on aggregate boundaries, invariants, and ubiquitous language. Do not model getters/setters, basic types, or standard data structures.

---

## Pattern: Bounded Contexts & Aggregates

When modeling a multi-domain system, visually separate **Bounded Contexts** and **Aggregates** to show where transactional boundaries live:

```mermaid
classDiagram
    namespace OrderContext {
        class Order {
            <<entity>>
            <<aggregate root>>
            -orderId: UUID
            -customerId: UUID
            -items: OrderLine[]
            -status: OrderStatus
            +place(): void
            +cancel(): void
        }
        
        class OrderLine {
            <<entity>>
            -lineId: UUID
            -orderId: UUID
            -productId: UUID
            -quantity: int
            -price: Money
        }
        
        class OrderStatus {
            <<value object>>
            -status: string
            -timestamp: DateTime
        }
        
        class Money {
            <<value object>>
            -amount: decimal
            -currency: string
        }
        
        Order *-- OrderLine
        Order *-- OrderStatus
        OrderLine *-- Money
        
        Order : Invariant: status always valid
        Order : Invariant: items always non-empty
        Order : Boundary: Only OrderRoot accessed externally
    }
    
    namespace PaymentContext {
        class Payment {
            <<entity>>
            <<aggregate root>>
            -paymentId: UUID
            -orderId: UUID
            -amount: Money
            -status: PaymentStatus
            +charge(): void
            +refund(): void
        }
        
        class PaymentStatus {
            <<value object>>
            -status: string
        }
        
        Payment *-- PaymentStatus
        Payment *-- Money
    }
    
    namespace InventoryContext {
        class Inventory {
            <<entity>>
            <<aggregate root>>
            -inventoryId: UUID
            -productId: UUID
            -quantity: int
            +reserve(qty): void
            +release(qty): void
        }
    }
    
    %% Cross-Context References (by ID only, never direct object ref)
    Order --> Payment : references by orderId
    Order --> Inventory : references by productId
    Payment -.publish.-> OrderEventPublished : domain event
    
    class OrderEventPublished {
        <<domain event>>
        -orderId: UUID
        -eventType: string
        -timestamp: DateTime
    }
```

**Key Visual Patterns**:

- `<<aggregate root>>` — Only entry point to aggregate from outside
- `*--` — Composition (owned by aggregate root, strong lifecycle dependency)
- `-->` — Weak association (reference by ID, cross-aggregate)
- `<<domain event>>` — Published by aggregates, consumed by others
- Namespace boxes — Separate bounded contexts

---

## Decision Tree: Entities vs. Value Objects

When determining how to model a domain concept:

- **Condition**: Does the concept's identity persist even if all its attributes change? (e.g., A User, An Order).
  - **Action**: Model as `<<entity>>`.
- **Condition**: Does the concept only matter because of its attributes, and is it immutable? (e.g., A Money amount, an Address, a Date Range).
  - **Action**: Model as `<<value object>>`.
- **Trap**: Modeling everything as an entity creates bloated, tightly coupled domain models that look like database schemas.

## Heuristic: Defining Aggregate Roots

- **Trap**: Allowing any entity to reference any other entity directly (creating a web of doom and destroying transactional boundaries).
- **Expert Move**: Identify the transactional consistency boundary. The Aggregate Root is the ONLY entry point. For example, an `OrderLine` should NEVER be accessed directly by a `PaymentService`; it must go through the `Order` aggregate.
- **Action**: Use strict composition (`*--`) from the Root to its internal entities. Use weak association (`-->`) when referencing other Aggregate Roots (and only refer to them by ID, not by object reference).

## Heuristic: The Anti-Corruption Layer (ACL)

When integrating with legacy systems or 3rd party domains:

- Do NOT pollute the core domain model with external concepts.
- Model an explicit `<<service>>` or `<<adapter>>` that acts as the Anti-Corruption Layer. Show how it translates the external model into the internal ubiquitous language.
- Use stereotypes like `<<acl>>` to make this architectural intent visually obvious.

## Heuristic: Modeling Domain Events

If the domain uses Domain Events to communicate between aggregates:

- Model the event as a `<<domain event>>` class.
- Show the Aggregate Root publishing it using a dependency arrow (`..>`).
- This bridges the gap between static structure and dynamic event-driven behavior.
