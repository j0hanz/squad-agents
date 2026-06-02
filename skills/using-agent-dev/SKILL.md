---
name: using-agent-dev
description: Use when working on the agent-dev plugin itself — for authoring, testing, validating, or shipping agents, skills, hooks, or documentation. Trigger on 'agent-dev', 'using agent-dev', 'how to use agent-dev'. Always check for relevant skills before acting.
user-invocable: false
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill — your instructions already include full context from the parent session.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If a skill might apply, invoke it before acting. No exceptions.

Invoking a skill that turns out not to apply costs nothing.
Skipping a skill that should have applied causes rework — and that rework compounds.

When in doubt: invoke first, act second.
</EXTREMELY-IMPORTANT>

---

## What Agent-Dev Is

Agent-Dev is a Claude Code plugin for **authoring, testing, validating, and shipping agents, skills, and hooks**. It provides:

- **19 skills** — process and domain methodologies loaded on demand
- **4 managed agents** — scoped subagents for delegated autonomous work
- **8 slash commands** — entry points for common workflows
- **15 lifecycle hooks** — automatic context injection, formatting, and nudges
- **Validation infrastructure** — `npm validate` for plugin health; `npm test` for full test suite

Everything in this repo follows a **skill-first, design-before-code** discipline. The output style enforces four phases: **Design → Build → Validate → Ship**.

**Invocation patterns**: Skills are invoked via the Skill tool (or skill name in your message). Managed agents are invoked via `@agent-name` followed by a prompt. Slash commands are typed as `/command-name`. These are three distinct mechanisms — do not confuse them.

---

## Instruction Priority

1. **User's explicit instructions** (CLAUDE.md, AGENTS.md, direct requests) — highest priority
2. **Agent-dev skills** — override default behavior where they conflict
3. **Default system prompt** — lowest priority

---

See [references/terminology.md](references/terminology.md) for definitions of skill, agent, command, hook, component, and other key terms.

---

## Process-First Rule (Skill-First)

**Invoke process skills (brainstorming, diagnose, planning) before implementation skills (refactor, code-review) and before any direct action.** Process skills tell you HOW to approach a task; implementation skills tell you HOW to execute it.

```
User message → Might any skill apply? → YES → Invoke Skill tool → Follow skill
                                       → DEFINITELY NOT → Respond directly
```

See [references/red-flags.md](references/red-flags.md) for warning signs you're rationalizing away the skill-first rule, plus the cost of skipping process skills.

### Skill Priority Order

1. **Process skills first** (brainstorming, diagnose, planning) — determine HOW to approach
2. **Implementation skills second** (refactor, code-review, tdd) — guide execution

"Let's build X" → `brainstorming` first, then implementation skills.
"Fix this bug" → `diagnose` first, then domain skills.

**When to skip skill invocation**: If none of the skills in the Skill Routing Map applies, respond directly. If the task is a single-word search, a clarifying question, or retrieving a file path — no skill is needed. If in doubt, check the Quick Lookup table first.

---

## Building a New Skill: Complete Workflow Example

**Want to create a new skill?** Follow this 5-step workflow:

| Step      | Invoke                 | How           | Output                          | Move On When                              |
| --------- | ---------------------- | ------------- | ------------------------------- | ----------------------------------------- |
| 1. Design | `brainstorming` skill  | Skill tool    | Design approval from user       | User says "Approved" / "LGTM" / "Proceed" |
| 2. Plan   | `/plan` command        | Slash command | `plan-*.md` file in `/plan/`    | Plan file created and reviewed            |
| 3. Build  | `/skill-builder` skill | Skill tool    | `SKILL.md` + `evals/evals.json` | All evals scaffolded                      |
| 4. Test   | `/test` command        | Slash command | Test results                    | All pass: `npm test` exits 0              |
| 5. Ship   | `/pr` command          | Slash command | PR URL + commit hash            | PR open, CI green                         |

---

## Skill Routing Map

18 skills organized by category. See [references/skill-routing-map.md](references/skill-routing-map.md) for the complete index of all Process, Domain/Execution, and Lifecycle skills with detailed invocation guidance.

---

## Managed Agents

Delegate to agents for isolated, autonomous work. Each runs in its own context — give it everything it needs in the prompt, because it has no access to the parent session.

**How to invoke**: Mention the agent name with `@` prefix followed by your prompt.
Example: `@coder refactor hooks/handlers/format.mjs to reduce nesting`

**Where outputs appear**: Coder and documenter write to a git worktree branch (`.claude/worktrees/`). Detective and explorer return structured text output in the conversation.

**Lifecycle**: Agents run asynchronously. You will receive a notification when complete. If an agent times out, re-invoke with a more scoped prompt.

For detailed information on each agent (job, isolation, use cases, invocation), see [references/managed-agents.md](references/managed-agents.md).

---

## Slash Commands

| Command       | Invokes               | When to Use                                             | Output                                   |
| ------------- | --------------------- | ------------------------------------------------------- | ---------------------------------------- |
| `/brainstorm` | `brainstorming` skill | Start any new feature, component, agent, skill, or hook | Design table + approval                  |
| `/coder`      | `coder` agent         | Autonomous code execution for multi-file tasks          | Worktree branch with changes             |
| `/detective`  | `detective` agent     | Root-cause analysis of bugs or failures                 | Structured bug report with fix proposals |
| `/diagram`    | `diagrams` skill      | Visualize architecture, workflows, or data flows        | ASCII/Mermaid diagram                    |
| `/explore`    | `explorer` agent      | Read-only code search and symbol lookups                | Search results + usage patterns          |
| `/fix`        | `diagnose` skill      | Debug a runtime failure or logic bug                    | Root cause analysis with diffs           |
| `/hook`       | `create-hook` skill   | Design or implement a lifecycle hook                    | Hook handler code + test cases           |
| `/pr`         | `code-review` skill   | Review a diff or PR for quality issues                  | Review findings with suggestions         |

---

## Hook Behaviors (What Fires Automatically)

Hook behaviors are automatic — you do not invoke them. They fire on lifecycle events. See [references/hooks.md](references/hooks.md) for the complete hook trigger and behavior reference.

---

## Output Style: Phase Discipline

Every work session follows four phases. **Do not skip phases or merge them.**

### Design Phase

- State the component type, trigger condition, and approach in a table **before writing any code**
- Get explicit design approval from the user before proceeding
- `brainstorming` skill governs this phase

**Design Phase Complete When:**

- [ ] User explicitly says "Approved", "LGTM", "Good", or "Proceed"
- [ ] Design table is present with: component type, trigger condition, approach
- [ ] No open blocking questions remain

### Build Phase

- One-line intent, then act — no preamble
- Every claim about existing code includes a `file:line` citation
- Sequential file edits only — one edit per turn per file

**Build Phase Complete When:**

- [ ] All planned files have been created or edited
- [ ] Code follows the project style guide (check with linting)
- [ ] No debug code, console.log, or `.skip` in tests remains
- [ ] Ready for validation testing

### Validate Phase

- Report as `PASS` or `FAIL`
- Each failure is a triple: **component → rule violated → specific fix**
- Run `npm validate` and `npm test` before marking complete

**Validate Phase Complete When:**

- [ ] `npm validate` exits with code 0
- [ ] `npm test` exits with code 0, all tests passing
- [ ] No code review findings block the PR
- [ ] Ready to ship

### Ship Phase

- List artifacts produced and what the next session can build on
- Use `/pr` to create a pull request with proper attribution
- All AI commits MUST include the attribution trailer (see below)

**Ship Phase Complete When:**

- [ ] Invoked `/pr` successfully
- [ ] PR is open with title and description
- [ ] CI/checks are running or passing
- [ ] Work is available for code review

### Phase Iteration

Phases are not strictly linear. Validate failures loop back to Build. Design changes during Build loop back to Design (get re-approval). Expect 1–3 Build/Validate iterations per task. This is normal.

### Exceptions to Phase Discipline

Not all work requires four full phases. See [references/exceptions.md](references/exceptions.md) for guidance on which phases to use for different work types (features, bugs, hotfixes, docs, research).

### Phase Discipline: Worked Example

See [references/phase-example.md](references/phase-example.md) for a detailed worked example showing the `/lint` command flowing through all four phases (Design → Build → Validate → Ship).

---

## Commit Attribution — Required on Every AI Commit

Every commit made by or with AI assistance MUST include this trailer (replace model name with the active model):

```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Use `/pr` to create a PR with proper attribution, or add the trailer manually when committing directly.

---

See [references/reference.md](references/reference.md) for tech stack and key file paths.

---

## If You're Stuck

**Can't find a skill?** Use the Quick Lookup table in Skill Routing Map or browse by category.

**Skill output confusing?** Check the skill's SKILL.md file for examples and guidance.

**Phase discipline unclear?** See the worked example in Phase Discipline section — shows `/lint` command through all four phases.

**Workflow steps?** The "Building a New Skill" table shows all 5 invocation steps with outputs.

**Error occurred?** See [references/error-recovery.md](references/error-recovery.md) for recovery steps: skill load failures, subagent timeouts, test failures, design approval stalls.
