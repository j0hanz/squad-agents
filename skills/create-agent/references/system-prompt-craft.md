# The Craft of Agent System Prompts

The system prompt is the agent. For a Claude Code subagent it *replaces* the default prompt entirely — there is no fallback personality, no inherited instructions, no conversation history. What you write is all the agent knows. This file is about writing it well.

## Table of contents

- [The five-part skeleton](#the-five-part-skeleton)
- [The handoff contract](#the-handoff-contract-the-part-everyone-forgets)
- [Self-containment](#self-containment)
- [Boundaries and fences](#boundaries-and-fences)
- [Worked example: a reviewer](#worked-example-a-reviewer)
- [Worked example: an implementer](#worked-example-an-implementer)
- [Anti-patterns](#anti-patterns)
- [The description field is a separate craft](#the-description-field-is-a-separate-craft)

---

## The five-part skeleton

Almost every good agent prompt has these five parts, in this order:

1. **Role & job.** One or two sentences. Who the agent is and the single job. `You are a security reviewer. You audit a diff for vulnerabilities and report them — you never modify code.`
2. **Operating procedure.** The ordered steps. This is where most of the quality lives — be concrete and imperative. `1. Read the diff. 2. For each changed file, check for: injection, auth bypass, secret exposure. 3. ...`
3. **Boundaries.** What it must not do. `Do not edit files. Do not run the app. Do not comment on style.`
4. **Output contract.** The exact shape of the final message. `Return a markdown list; each item: file:line, severity, one-line description, suggested fix. If no issues: "No security issues found."`
5. **Tone & length.** `Be terse and factual. No preamble.`

Not every agent needs all five sections as headers — but if you can't answer all five questions, the prompt isn't done.

---

## The handoff contract (the part everyone forgets)

**The parent only ever sees the agent's final message.** Every tool call, every intermediate reasoning step, every file the agent read — all discarded. The single text block the agent returns is the entire value of the delegation.

This has two consequences:

- **Design the output explicitly.** "Summarize what you found" produces mush. "Return: (1) a one-line verdict, (2) a bullet list of `file:line — issue`, (3) the single highest-priority fix" produces something the parent can act on.
- **Make it self-contained.** The parent can't re-run the agent's reasoning. If the agent found a bug at `auth.ts:42`, the final message must *say* `auth.ts:42` — the parent never saw the agent open that file.

A useful test: could a *different* person, given only the final message, act correctly without asking a follow-up? If not, tighten the contract.

---

## Self-containment

A subagent gets **no parent conversation history**. It does not know what the user asked, what was decided three turns ago, or which file is "the one we were just looking at."

- Put everything the agent needs in its **system prompt** (durable role) or the **invocation prompt** (this-task specifics).
- Never write "continue what we were doing" or "fix the bug we discussed."
- If the agent needs a file path, a branch name, or a constraint, the invocation prompt must name it.

When you invoke an agent, write the prompt as if briefing a contractor who just walked in: full context, no assumptions.

---

## Boundaries and fences

Agents over-reach. The single most common failure is an agent asked to *review* that starts *rewriting*, or one asked to *investigate* that "helpfully" commits a fix. Prevent it two ways:

1. **In the prompt:** an explicit "Do not…" list. `Do not modify files. Do not commit. Do not touch anything outside src/auth/.`
2. **In the config:** least-privilege tools. A reviewer with no `Edit`/`Write` tool *cannot* rewrite, no matter what the prompt says. Belt and suspenders — state the boundary *and* remove the capability.

Config-level fences are stronger than prompt-level ones. Prefer them; use the prompt to explain intent.

---

## Worked example: a reviewer

```markdown
---
name: security-reviewer
description: Audits a diff or file for security vulnerabilities. Use proactively after auth, input-handling, or crypto changes.
tools: Read, Grep, Glob
model: opus
---

You are a security reviewer. You audit code for vulnerabilities and report them. You never modify code, run commands, or comment on style.

## Procedure
1. Read the target diff or files named in the prompt.
2. For each changed region, check for: injection (SQL/command/path), authentication or authorization bypass, exposed secrets or keys, unsafe deserialization, and missing input validation.
3. Trace tainted input to where it is used. Note the path concretely.

## Boundaries
- Do not edit, write, or commit anything.
- Do not flag style, naming, or formatting.
- If asked to fix something, report the fix as text — do not apply it.

## Output
Return a markdown list. Each finding: `file:line` — **severity** (critical/high/medium) — one-line description — suggested fix.
If no issues: exactly `No security issues found.`
Be terse. No preamble.
```

Why these choices: read-only tools (a reviewer must not write); `opus` (adversarial reasoning); a tight output contract the parent can paste into a PR.

---

## Worked example: an implementer

```markdown
---
name: test-fixer
description: Runs the test suite and fixes failing tests autonomously. Use when tests are red and the cause is known to be in the implementation.
tools: Read, Edit, Write, Bash, Grep, Glob
model: sonnet
---

You fix failing tests until the suite is green. Work autonomously; do not ask questions mid-run.

## Procedure
1. Run the test command given in the prompt (or `npm test` if unspecified).
2. Read the first failure. Form one hypothesis about the cause.
3. Make the smallest change that could fix it. Re-run that test.
4. Repeat until the full suite passes. Re-run the whole suite at the end to confirm.

## Boundaries
- Change implementation or test code only as needed to make tests pass — do not refactor unrelated code.
- Do not commit. Do not push. Do not change CI config or dependencies.
- If a test is failing because it is wrong (not the code), say so in the output instead of forcing it green.

## Output
Return: (1) final suite status, (2) a bullet per file changed with a one-line reason, (3) any test you believe is itself incorrect.
```

Why these choices: write + `Bash` (it must run and fix); `sonnet` (capable, cost-appropriate for mechanical iteration); explicit "do not commit" because autonomous agents with write access drift.

---

## Anti-patterns

| Anti-pattern | Fix |
| :--- | :--- |
| "You are a helpful assistant that helps with code." | Name the *one* job and its boundaries. |
| "You should try to…", "You might want to…" | Imperative: "Do X." Aspirational language reads as optional. |
| No output contract | Define the final message shape — the parent sees nothing else. |
| Assumes conversation history ("fix the bug we found") | Restate every fact in the system or invocation prompt. |
| Reviewer/analyzer granted `Edit`/`Write`/`Bash` | Remove the capability; read-only enforces the role. |
| Kitchen-sink prompt covering three jobs | Split into three agents, each with one job. |
| Relies on the model to discover a skill | Preload it with `skills:` so the capability is guaranteed. |
| Autonomous agent with no termination condition | State when to stop; consider a `SubagentStop` gate. |

---

## The description field is a separate craft

The `description` is **not** the system prompt — it is the *triggering* mechanism. Claude reads it to decide whether to delegate. Make it pushy and concrete: name the situations, include "use proactively" if you want automatic delegation, and list the trigger phrases. A vague description means the agent never fires; an over-broad one means it fires when it shouldn't. Tune it *after* the system prompt's behavior is stable — see the `skill-builder` skill for description optimization.
