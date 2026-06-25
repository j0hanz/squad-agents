# Agent-SDLC Lifecycle

## Lifecycle Chain

```mermaid
graph TD
    Start((Start)) --> G0{Gate 0: Onboarded?}
    G0 -- No AGENTS.md --> INIT[codebase-init]
    G0 -- Onboarded --> G1{Gate 1: Defined?}
    INIT --> G1
    G1 -- No/Vague --> B[parallel-brainstorming]
    G1 -- Needs Plan --> P[planning]
    G1 -- Yes --> G2{Gate 2: Scope?}

    B --> P
    P --> G2

    G2 -- Systemic --> ARC[architecting]
    G2 -- Localized --> G3{Gate 3: Strategy}
    G2 -- Debugging --> DIAG[diagnose]
    G2 -- Feature --> G3

    ARC --> G3
    DIAG --> G3

    G3 -- Parallel --> MAD[multi-agent-dispatch]
    G3 -- Sequential --> MDEV[multi-agent-development]
    G3 -- "Mixed DAG" --> MDEV
    G3 -- Standard --> TDD[test-driven-development]

    MAD --> V[verification-before-completion]
    MDEV --> V
    TDD --> V

    V --> RCR[request-code-review]
    RCR -- PASS --> SHIP[pr-workflow]
    RCR -- FAIL --> RECV[receive-code-review]
    RECV -- "Tier 1/2" --> DIAG
    DIAG -- "fix verified" --> RECV
    RECV -- "re-review (max 2 cycles)" --> RCR
    TDD -- "GREEN failure escalation" --> DIAG
    TDD -- "spec ambiguous" --> P
```

## Transition States

- **TDD Escalation:** If TDD fails to pass after 3 attempts, it must return to `diagnose` or `planning`. This is now reflected directly in `SKILL.md`'s Gate 3 text.
- **Review Failure:** `receive-code-review` analyzes the failure level and routes back to the appropriate corrective skill, using `request-code-review`'s Tier classification (`references/patterns.md` in that skill): Tier 1 = Security, Tier 2 = Correctness, Tier 3 = Performance, Tier 4 = Reuse/hygiene. Tier 1/2 findings route to `diagnose`; Tier 4 findings are fixed inline by `receive-code-review` itself; Tier 3 findings are non-blocking and require no escalation. `SKILL.md`'s Gate 4 describes this same routing using "blocking issue"/"hygiene issue" wording rather than tier numbers — both describe the same logic.
- **Re-review Cap:** Once `diagnose` verifies its fix (or `receive-code-review` fixes a Tier 4 item inline), control returns to `receive-code-review`, which re-invokes `request-code-review` for a fresh-context re-review of the same range. This cycle is capped at 2 re-reviews before escalating to the user — `receive-code-review`'s own doc states this cap directly so the limit isn't only discoverable via the orchestrator.
