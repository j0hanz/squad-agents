# Advanced Layout: Wrassling the Renderer

When architectural diagrams scale, default rendering engines produce spaghetti. Use these heuristics to force readability and handle edge cases.

## Heuristic: Forcing the ELK Engine

- **Condition**: The diagram represents a heavily interconnected microservice mesh, or a complex graph with returning loops and criss-crossing lines.
- **Action**: You MUST inject the ELK rendering directive at the top of the Mermaid block. Dagre (the default) will fail.

```mermaid
---
config:
  layout: elk
  elk:
    mergeEdges: true
    nodePlacementStrategy: BRANDES_KOEPF
---
```

## Heuristic: Breaking Circular Dependencies

- **Trap**: ELK fails to render, or produces a massive vertical line because of a dependency cycle.
- **Expert Move**:
  1. Identify the cycle (e.g., A -> B -> C -> A).
  2. Abstract one of the components into a higher-level subgraph OR use an invisible link (`~~~`) to force horizontal alignment without drawing an edge, then use a dashed line for the back-reference to indicate a weak or async callback.

## Heuristic: Subgraph Overlap Fixes

- When subgraphs cross over each other chaotically:
  - Define ALL nodes and internal relationships completely _inside_ their respective subgraphs first.
  - Define inter-subgraph relationships at the very bottom of the file.
  - Use `direction LR` inside a specific subgraph to force it to render horizontally, while the rest of the diagram flows vertically (`TB`). This dramatically reduces the overall vertical footprint and untangles nested flows.
