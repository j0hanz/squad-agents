# Architecture Patterns Reference

## Layered Architecture

- **Best for**: CRUD-heavy apps where domain logic follows a linear flow.
- **Expert Trade-off**: High speed initially, but prone to "Lava Layering" where business logic leaks into the UI or DB layers over time.
- **Failure Mode**: The "Anemic Domain Model" — where service classes are just pass-throughs for DB entities, leading to logic scattered everywhere.

## Ports and Adapters / Hexagonal Architecture

- **Best for**: Long-lived systems where the framework/DB is likely to change or where testing complex logic without a database is critical.
- **Expert Trade-off**: Physical separation of Domain from Infrastructure. Provides the highest testability but requires 2x the boilerplate (mapping between Domain and DB types).
- **Failure Mode**: Over-abstraction. Creating interfaces for things that will never have a second implementation (e.g., a "ClockInterface" when standard `Date` is fine).

## Clean Architecture (Uncle Bob)

- **Best for**: Enterprise scale, highly complex business rules that must be completely isolated from external agencies (web, DB, UI).
- **Expert Trade-off**: Very strict Dependency Rule (dependencies only point inward toward Entities). Maximum testability and decoupling, at the cost of massive indirection and DTO mapping across boundaries.
- **Failure Mode**: Using it for simple CRUD. Over-engineering simple data access into Use Cases and Gateways when active record would suffice.

## Feature-Based Modularization (Vertical Slices)

- **Best for**: Systems where features are independent and team ownership is split by business capability.
- **Expert Trade-off**: Minimizes cross-feature coupling. If you delete a feature folder, nothing else breaks. Leads to code duplication (which is often better than the wrong shared abstraction).
- **Failure Mode**: The "Shared Data" trap. Features often need the same data; if they share the same DB table, the boundary is an illusion.

## Event-Driven Architecture

- **Best for**: Decoupling side-effects (e.g., "When OrderPaid, send Email, update Inventory, notify Shipping").
- **Expert Trade-off**: High scalability and decoupling. However, it introduces "Distributed Complexity" — it's harder to trace a single business flow across multiple event handlers.
- **Failure Mode**: Event Spaghetti. Events triggering other events in a circular or non-deterministic way, making the system impossible to debug.

## CQRS (Command Query Responsibility Segregation)

- **Best for**: High-traffic systems where the Read model (e.g., a complex dashboard) is radically different from the Write model (e.g., a simple state transition).
- **Expert Trade-off**: Allows independent scaling and optimization of reads. Costs: Double the code, eventual consistency issues, and higher cognitive load.
- **Failure Mode**: Applying CQRS to simple CRUD. If your read model is just a "SELECT \* FROM Table", CQRS is pure overhead.

## Event Sourcing

- **Best for**: Systems requiring complete auditability, temporal querying, or complex state reconstruction (e.g., Banking, Shopping Carts).
- **Expert Trade-off**: State is derived from a log of facts (events) rather than mutated in place. Incredible debuggability and time-travel querying, but massive cognitive shift and data migration complexity.
- **Failure Mode**: Storing structurally unstable events. Changing an event schema later is notoriously difficult in an append-only log.

## Modular Monolith

- **Best for**: 90% of professional projects. Clear boundaries within a single deployment unit.
- **Expert Trade-off**: Provides microservices-level boundary discipline without the "Network Tax" (latency, distributed transactions, deployment complexity).
- **Failure Mode**: "Import Sprawl." Developers importing internal types from other modules because "it's all in one repo," eventually turning it into a Big Ball of Mud.
