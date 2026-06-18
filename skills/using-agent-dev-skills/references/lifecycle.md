# Agent-Dev Lifecycle

## Lifecycle Chain

```mermaid
graph TD
    Start((Start)) --> G1{Gate 1: Defined?}
    G1 -- No/Vague --> B[brainstorming]
    G1 -- Needs Plan --> P[planning]
    G1 -- Yes --> G2{Gate 2: Scope?}

    B --> P
    P --> G2

    G2 -- Systemic --> ARC[architecting]
    G2 -- Localized --> REF[refactor]
    G2 -- Debugging --> DIAG[diagnose]
    G2 -- Feature --> G3{Gate 3: Strategy}

    ARC --> G3
    REF --> G3
    DIAG --> G3

    G3 -- Parallel --> MAD[multi-agent-dispatch]
    G3 -- Sequential --> MDEV[multi-agent-development]
    G3 -- "Mixed DAG" --> MDEV
    G3 -- Standard --> TDD[test-driven-development]

    MAD --> V[verification-before-completion]
    MDEV --> V
    TDD --> V

    V --> RCR[request-code-review]
    RCR -- PASS --> GH[github-automation]
    RCR -- FAIL --> RECV[receive-code-review]
    RECV -- "Tier 1/2" --> DIAG
    RECV -- "Tier 4" --> REF
    TDD -- "GREEN failure escalation" --> DIAG
    TDD -- "spec ambiguous" --> P
```

## Transition States

- **TDD Escalation:** If TDD fails to pass after 3 attempts, it must return to `diagnose` or `planning`. This path is not yet reflected in `SKILL.md`'s Gate 3 text — treat it as authoritative until the main file is updated.
- **Review Failure:** `receive-code-review` analyzes the failure level and routes back to the appropriate corrective skill, using `request-code-review`'s Tier classification (`references/patterns.md` in that skill): Tier 1 = Security, Tier 2 = Correctness, Tier 3 = Performance, Tier 4 = Reuse/hygiene. Tier 1/2 findings route to `diagnose`; Tier 4 routes to `refactor`; Tier 3 findings are non-blocking and require no escalation. `SKILL.md`'s Gate 4 describes this same routing using "blocking issue"/"hygiene issue" wording rather than tier numbers — both describe the same logic.
