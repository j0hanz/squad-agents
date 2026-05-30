---
description: Validate, commit with attribution, and prepare a PR for the current plugin work.
---

# Deliver — Delivery Pipeline

Deliver the current plugin work: validate output, commit with attribution, and open a PR.

## Prerequisite Gate

`/artifact-review` must pass (zero blocking findings) before delivery. If it has not been run, invoke it now and resolve all critical findings first.

## Pipeline

The `delivery-manager` skill drives this flow:

1. **Validate** — run `/check all` to confirm plugin health; surface any structural or manifest errors
2. **Lint & format** — confirm no linting or formatting violations (`npm run lint && npm run format:check`)
3. **Test** — run the full test suite (`npm test`); all tests must pass
4. **Stage & commit** — commit staged changes with the required `Co-Authored-By` trailer:

   ```text
   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
   ```

5. **PR** — generate a PR description summarizing changes, then open the pull request

Invoke the `delivery-manager` skill to execute this pipeline.
