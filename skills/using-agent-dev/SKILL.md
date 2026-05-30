---
name: using-agent-dev
description: |
  Navigation guide for agent-dev plugin skills — establishes routing and priority order.
  Use when asking "which skill should I use for X?", when a task doesn't clearly map to
  an existing skill, or when working within the agent-dev plugin context. Essential for 
  choosing between process skills (diagnose vs TDD), overlapping domains (refactor vs architecture), 
  and understanding workflow sequences.
disable-model-invocation: false
---

> **Invocation:** When installed as the `agent-dev` plugin, prefix skill names with `agent-dev:` — e.g., `/agent-dev:brainstorming`. In a standalone `.claude/skills/` installation, use bare names — e.g., `/brainstorming`.

# Agent-Dev Skill System

## ⚠️ Rigid vs Flexible — Discipline Rules

Some skills are **non-negotiable**. Follow these exactly; do not adapt away from the discipline:

| Skill | Rule | Why |
|-------|------|-----|
| `diagnose` | Document root cause BEFORE fixing | Prevents symptom-chasing and recurrence |
| `test-driven-development` | One test, run it, one impl, run it; no batching | Batching defeats the red-green-refactor discipline |
| `spec-driven-development` | Spec → plan → code order is mandatory | Skipping spec leads to rework and misaligned delivery |

All other skills are **flexible** — adapt principles to your context unless their body says otherwise.

---

## 🗺️ Skill Routing Map

### Process Skills — Choose ONE first (they govern HOW to work)

These determine your workflow discipline. **Use BEFORE domain skills.**

| Skill | Trigger | Quick Reference |
|-------|---------|-----------------|
| `brainstorming` | Features, design questions, ambiguous terminology, requirements unclear | Clarifies intent, explores options, aligns terminology before committing |
| `diagnose` | Crashes, test failures, unexpected behavior, "why did this break?" | Documents root cause before fixes; required by rigid discipline |
| `test-driven-development` | Implementing features or bugfixes with focus on test-first cadence | One test → run → one impl → run; red-green-refactor cycle |
| `spec-driven-development` | Full feature lifecycle: spec → plan → code → validate; requirements-first approach | Complete workflow including create-specs and create-plan steps |
| `verification-before-completion` | Before marking any task or feature done; final checklist before declaring success | Confirms correctness, tests pass, edge cases handled |
| `code-review` | Before reporting implementation complete or creating a PR | Catches quality issues, security gaps, maintainability concerns (required gate for delivery) |
| `delivery-manager` | Transitioning code to PR, merge, or production; finalizing handoff | Workflow for merge strategy, CI status, release coordination |

**Note:** `create-specs` and `create-plan` are Steps 2–3 of `spec-driven-development`; you invoke them within that workflow, not as standalone entry points.

---

### Domain Skills — Choose AFTER your process (guide implementation details)

These provide domain expertise. **Use AFTER choosing your process skill.**

| Skill | Trigger | Quick Reference |
|-------|---------|-----------------|
| `research` | Unfamiliar APIs, libraries, frameworks, or documentation gaps | Fetches current docs, finds examples, clarifies best practices |
| `architecture` | Structure itself is unclear or wrong; designing new systems; rethinking the blueprint | System-level design, module dependencies, scalability decisions |
| `refactor` | Code quality is poor but structure is sound; duplication, readability, maintainability | Improves existing code without changing structure or behavior |
| `diagrams` | Creating architectural visualizations, system diagrams, flow charts | Renders visual representations of designs or systems |
| `github-automation` | GitHub Actions workflows, gh CLI scripts, automation/CI tasks | Workflow automation, CI/CD pipeline design, scripting |
| `hook-development` | Designing or implementing Claude Code hooks (session, pre-tool, format events) | Hook architecture, event handling, hook testing |
| `agent-development` | Building Claude agents, skills, or multi-skill pipelines; agent routing | Agent design patterns, skill composition, LLM agent logic |
| `skill-builder` | Creating new skills, updating existing skills, testing skills, benchmarking | Skill authoring, iteration, quality assurance |
| `agents-maintainer` | Updating AGENTS.md, CLAUDE.md, instruction files, plugin metadata | Documentation updates, instruction clarity, plugin configuration |

---

## 🎯 Decision Logic for Overlapping Skills

**When you see overlapping triggers, use this decision tree:**

### Refactor vs. Architecture
```
Is the fundamental structure/design wrong or problematic?
├─ YES → architecture (redesign the blueprint)
└─ NO → refactor (clean up the existing code)

Examples:
  "Microservices are too tightly coupled" → architecture
  "This function has 8 nested loops" → refactor
  "Database schema should be denormalized" → architecture
  "Code has 200% duplication" → refactor
```

### Diagnose vs. Test-Driven-Development
```
Did something unexpected happen (crash, failure, wrong output)?
├─ YES → diagnose (find root cause first)
└─ NO → test-driven-development (implement with test-first discipline)

Examples:
  "Tests are failing intermittently" → diagnose (why?)
  "I need to add a new feature" → test-driven-development
  "API returns 500 in production" → diagnose
  "I'm implementing authentication" → test-driven-development
```

### Spec-Driven-Development vs. Brainstorming
```
Are requirements already clear and agreed?
├─ YES → spec-driven-development (formalize and execute)
└─ NO → brainstorming (explore options, align terminology, clarify intent)

Examples:
  "We know what to build, let's do it" → spec-driven-development
  "We might need feature X, or maybe Y?" → brainstorming
  "Requirements are documented" → spec-driven-development
  "Terms like 'user', 'role', 'permission' mean different things to different people" → brainstorming
```

---

## 🔄 Common Workflow Sequences

Use these complete paths for common scenarios:

### **Feature Implementation**
```
1. brainstorming (clarify intent, explore design, align terminology)
2. spec-driven-development (formalize spec → plan → code)
   ├─ create-specs (Step 2 of spec-driven-development)
   ├─ create-plan (Step 3 of spec-driven-development)
   └─ code (Step 4, may use test-driven-development if desired)
3. verification-before-completion (confirm tests, edge cases, correctness)
4. code-review (catch quality/security/maintainability issues)
5. delivery-manager (merge, deploy, release coordination)
```

### **Bug Fix (Production Issue)**
```
1. diagnose (find root cause; required rigid discipline)
2. test-driven-development (implement fix with test-first cadence; optional but recommended)
   OR direct fix (if root cause is obvious and trivial)
3. verification-before-completion (confirm fix works, no regressions)
4. code-review (quality gate before merge)
5. delivery-manager (deploy hotfix or planned merge)
```

### **Code Quality Improvement**
```
1. brainstorming (clarify scope: refactor vs. architecture?)
2. architecture (if structure is wrong) OR refactor (if structure is sound)
3. test-driven-development (optional; recommended for complex refactors)
4. verification-before-completion (confirm behavior unchanged)
5. code-review (review for correctness, quality)
6. delivery-manager (merge)
```

### **Infrastructure/Hook/Skill Development**
```
1. brainstorming (clarify requirements, design options)
2. research (if unfamiliar with APIs/patterns)
3. agent-development (if building agents/skills) OR hook-development (if building hooks)
4. skill-builder (if creating a skill; includes testing and iteration)
5. code-review (quality gate)
6. delivery-manager (merge, release)
```

---

## 🤔 If You're Stuck

**"I don't know which skill to use"**

Ask yourself:

1. **Is something broken?** → Use `diagnose` (find root cause)
2. **Are requirements unclear?** → Use `brainstorming` (clarify intent)
3. **Do you know what to build AND how to build it?** → Use `spec-driven-development` (execute)
4. **Is the code messy but structure is fine?** → Use `refactor` (clean it up)
5. **Is the structure/design itself wrong?** → Use `architecture` (redesign)
6. **Do none of the above fit?** → Use `skill-builder` (create a new skill or improve an existing one)

---

## 📋 Domain Skill Selection Matrix

**When choosing between domain skills, use this framework:**

|  | New Code/System | Existing Code/System |
|---|---|---|
| **Unclear structure** | `agent-development` (if agents), `skill-builder` (if skills), `architecture` (if system redesign) | `architecture` (redesign needed) |
| **Structure clear, quality poor** | `test-driven-development` (TDD as you build) | `refactor` (improve without changing structure) |
| **Need automation/scripting** | `github-automation` (CI/CD) or `hook-development` (Claude hooks) | Same |
| **Uncertain how to implement** | `research` (learn APIs/patterns) | Same |
| **Need visual documentation** | `diagrams` (draw it out) | Same |

---

## 🔗 Skill Combinations & Dependencies

Some skills work together:

- **`agent-development` + `skill-builder`**: Build agents using skills; use skill-builder to create the skills themselves
- **`spec-driven-development` includes `create-specs` + `create-plan`**: Don't invoke specs/plan as standalone skills; they're internal steps
- **`code-review` → `delivery-manager`**: code-review must pass (zero blocking findings) before running delivery-manager
- **`diagnose` → `test-driven-development`**: After diagnosing root cause, TDD ensures the fix stays fixed
- **`research` + any domain skill**: Research first if you're unfamiliar with the domain

---

## 🚫 Unmapped Tasks

If a task doesn't fit any skill above, use `skill-builder` to:
- Create a new skill to capture that knowledge
- Improve an existing skill that's incomplete
- Extend the skill ecosystem

