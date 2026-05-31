# Testing Agents — Eval-First

An agent's failures are **behavioral**, not syntactic. The config can be valid and the agent still over-reach, return mush, loop forever, or quietly do nothing. Test behavior on real inputs before you ship.

## Table of contents

- [Two layers of checks](#two-layers-of-checks)
- [Baseline comparison](#baseline-comparison-is-the-agent-pulling-its-weight)
- [The behavioral checklist](#the-behavioral-checklist)
- [Flakiness](#flakiness)
- [Sandbox side effects](#sandbox-side-effects)
- [When to reach for skill-builder](#when-to-reach-for-skill-builder)

---

## Two layers of checks

**Layer A — Deterministic.** Things with one right answer: did it call only the granted tools? did it write outside its boundary? did the final message match the contract shape? did it terminate? Check these with assertions or a `SubagentStop`/`PostToolUse` hook observing tool calls — *never* with an LLM judge.

**Layer B — Qualitative.** Things needing judgment: is the review insightful? is the summary clear? is the reasoning sound? Use an LLM-as-judge (or your own read) here — and *only* here. Never use a judge for deterministic checks; never use a deterministic assertion for quality.

Default: run both. Write the deterministic checks first, before the prompt is final — they pin the boundaries the prompt must respect.

---

## Baseline comparison: is the agent pulling its weight?

An agent earns its cost only if it beats the alternative. Run the same task two ways:

- **With the agent** — your definition.
- **Baseline** — the plain model with no special prompt (for a new agent), or the previous version (when iterating).

If the agent isn't clearly better — tighter output, fewer tokens in the parent, more reliable boundaries — the extra primitive isn't justified. Either fix the prompt or drop the agent and inline the work.

---

## The behavioral checklist

Run the agent on 2–3 representative inputs — include one edge case and one it should **refuse or scope out of** — and check:

- [ ] **Boundaries held** — no scope creep, no unrequested writes, no commits.
- [ ] **Output contract met** — the final message is the exact shape you designed: parseable, complete, self-contained (no "as discussed").
- [ ] **Tool surface respected** — used only granted tools; no thrashing or redundant calls.
- [ ] **Termination** — it stopped when done (critical for autonomous/background agents — does it loop?).
- [ ] **Refusal works** — given the out-of-scope input, it declined cleanly instead of improvising.

---

## Flakiness

Agents are stochastic. A single green run proves little. For anything you'll depend on, run each case **2–3 times** and watch for variance: does it sometimes write a file it shouldn't? sometimes return a different output shape? Flaky boundaries are a prompt or permission problem — tighten the fence (prefer config-level: remove the tool) until the behavior is stable across runs.

---

## Sandbox side effects

If the agent has write, `Bash`, deploy, or external-call capability, **test in a sandbox / disposable worktree first**. A real agent with `Bash` can modify the host, send real messages, or charge real money. Use `isolation: worktree` for file-writing agents, and never run a side-effecting agent's first test against production state.

---

## When to reach for skill-builder

For a rigorous, repeatable benchmark — formal eval sets, baseline-vs-candidate scoring, variance analysis, description-trigger optimization — hand off to the **`skill-builder`** skill. It provides the harness (workspace scaffolding, graders, aggregation, a review viewer) for measuring an agent or skill across many cases. Use it once an agent's behavior is roughly right and you want to *prove* it before shipping.
