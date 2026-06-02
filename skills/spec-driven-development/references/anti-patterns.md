# Anti-Patterns in Spec-Driven Development

## Code-First Development

**NEVER** write code before the spec is validated. This produces drift that compounds — interfaces end up designed around what was easy to implement, not what the system should do.

## Retrofitted Specs

**NEVER** retrofit a spec to match existing code. Retrofitted specs fail as contracts because requirements are written to match already-present behavior, making the spec redundant rather than authoritative.

## Ignoring Spec Drift

**NEVER** ignore drift detected during implementation. See [implementation-governance.md](implementation-governance.md) for the full stop-work trigger list and resolution procedure.

## Skipping Gates

**NEVER** skip the Specification Gate or Planning Gate, even under time pressure. Gates exist because downstream errors are exponentially more expensive to fix. A skipped gate is technical debt borrowed at high interest.

## Manual Spec or Plan Writing

**NEVER** write the spec or plan manually when the `planning` skill is available. Manual work is not validated against structural rules and will produce plans with missing traceability and an empty coverage matrix.

## Partially Validated Plans

**NEVER** begin implementation on a plan that failed `validate.py --plan` or `validate.py --cross`. A plan with structural errors or uncovered requirements will produce unpredictable implementation order and untraceable failures.
