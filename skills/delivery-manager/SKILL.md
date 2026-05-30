---
name: delivery-manager
description: |
  Transitions a feature from "code complete" to "delivered". Use when the user says "deliver this", "create a PR", "finish the feature", "wrap up", or asks to generate a PR description. Orchestrates final validation, PR metadata generation, attribution, and changelog updates.
disable-model-invocation: true
---

# Delivery Manager

> **Prerequisite**: `code-review` must pass (zero blocking findings) before running this skill. If the user hasn't run a code review yet, invoke `code-review` first and resolve all critical findings before proceeding.

The Delivery Manager orchestrates the final transition from "working code" to "merged history." Delivery is an act of communication, not just a technical operation.

## Mindset: The Artifacts of Delivery

Before touching Git, align with the expert perspective on delivery artifacts:

- **The Diff** is what changed.
- **The PR Description** is _why_ it changed and _how_ to verify it.
- **The Changelog** is the public contract of the impact.

A great delivery makes the reviewer's job trivial and the future maintainer's archeology possible.

## Phase 1: Strategic Diff Analysis

Do not just read the raw diff. Analyze it to build the narrative.

1.  **Run Validation:** Ensure all tests, linters, and type-checks pass. **Stop** if they fail.
2.  **Structural Review:** Run `git diff --stat origin/main`. Look for:
    - **Scope Creep:** Did files outside the core feature domain change? (e.g., a UI feature modifying a core database utility). Call this out in the PR.
    - **The Weight:** Where are the most lines changed? That is the heart of the PR.
3.  **Semantic Review:** When reading the full diff:
    - Look at `import` changes first to understand architectural shifts.
    - Identify the entry point (the new route, the exported function) and map the dependency graph outward.

**After steps 2–3 — spawn the `diff-analyst` subagent** (`agents/diff-analyst.md`) to handle deep file reading and scope analysis in isolation:

```
Agent(
  description: "Diff analysis for PR narrative",
  prompt: |
    git_diff: [full stdout of: git diff origin/main...HEAD]
    git_stat: [full stdout of: git diff --stat origin/main...HEAD]
    git_log:  [full stdout of: git log --oneline origin/main...HEAD]
    base: origin/main
)
```

The agent returns a structured JSON. Wire it into Phase 2 as follows:
- `narrative.why` → "The Why" section body
- `narrative.architectural_decisions` → "The How" bullet items
- `narrative.verification_steps` → Verification checklist items
- `scope_creep` → call each entry out explicitly in the PR description
- `delivery_blockers` → **must be empty before proceeding**; if non-empty, resolve each item first

## Phase 2: Narrative Generation (PR & Changelog)

> **To create the PR**: After drafting the description below, invoke `github-automation` to open the pull request using the `gh pr create` workflow. Do not create PRs manually via the GitHub UI when `github-automation` is available.

Translate the code diff into human intent.

### PR Description Template

```markdown
# [Context]: [Actionable, specific title]

## The "Why"

[Explain the business or technical motivation. Do not explain the code; explain the problem the code solves. Link to related issues or plans.]

## The "How" (Architecture & Key Decisions)

- [Component A]: [Explain the architectural choice or pattern used, not the line-by-line implementation.]
- [Component B]: [Why was this approach chosen over alternatives?]

## Verification

- [ ] [Name specific automated test suites run]
- [ ] [Detail manual steps to verify the core user journey]
```

### Changelog Updates

Always update `CHANGELOG.md` under the `[Unreleased]` heading. If no `CHANGELOG.md` exists yet, create it with `# Changelog` as the header and an `## [Unreleased]` section following the [keepachangelog.com](https://keepachangelog.com) format.
Categorize strictly: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

**Format:** `- **[Component]**: Concise explanation of the user-facing impact. (#PR-or-Issue-Link)`

## Expert Anti-Patterns (NEVER List)

NEVER do the following during delivery:

- **NEVER use mechanical PR titles.** "Updated auth.ts" is useless. "feat(auth): implement PKCE flow for OAuth2" is searchable and semantic.
- **NEVER summarize the diff in the PR description.** The reviewer can read the code. Explain the _intent_ and the _trade-offs_ that the code cannot express.
- **NEVER mix unrelated changes.** If you find unrelated refactoring or formatting fixes in the diff, isolate them or flag them explicitly for the reviewer.
- **NEVER commit unresolved artifacts.** Scan the diff for `console.log`, `.skip` in tests, or `TODO: fix before merge`. If found, halt delivery and fix them.
- **NEVER invent version numbers.** Always target the `[Unreleased]` block in the changelog unless explicitly instructed to perform a release cut.
