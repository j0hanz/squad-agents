---
name: refactor
description: >-
  Apply when the user asks to "clean up", "refactor", "simplify", "improve",
  "modernize", or "restructure" code — or says it is messy, hard to read, hard
  to extend, or hard to test. Also trigger proactively when you spot obvious
  structural problems while working on something else: long functions,
  copy-pasted logic, god classes, magic numbers, tangled conditionals, or
  misleading names. Use for targeted, behavior-preserving improvements to
  existing code. Not for full rewrites.
disable-model-invocation: false
---

# Refactor

Refactoring means improving structure without changing behavior. The skill is knowing _what_ to change, _how much_, and _in what order_ — not knowing the patterns. You already know the patterns.

---

## Step 1: Read Before You Touch

Read the full code before proposing any change. Build a mental model:

- What does this code actually do? (Not just what the names imply)
- Who calls it? What does it depend on?
- What's already clean vs. what's genuinely problematic?
- Are there tests? Can you run them?

Don't refactor on a quick scan. Code that looks messy sometimes has hidden invariants that matter. Use `Grep` to rigorously assess the cross-file blast radius before touching module boundaries or exported functions.

---

## Step 2: Name the Pain Point

If the request is vague ("clean this up", "make it better"), ask one question:

> **What's the hardest thing about working with this code right now?**

Map the answer to the right fix:

| Pain                               | Likely problem                     | Likely fix                               |
| ---------------------------------- | ---------------------------------- | ---------------------------------------- |
| "Hard to add a new case"           | Missing abstraction                | Extract class, Strategy, or enum         |
| "Hard to understand"               | Poor naming, too much in one place | Rename, extract, remove comments-as-code |
| "Copy-pasted everywhere"           | Duplication                        | Extract shared utility                   |
| "Tests keep breaking unexpectedly" | Hidden coupling                    | Separate concerns, inject dependencies   |
| "Scared to touch it"               | No tests + complex logic           | Write characterization tests first       |

If the user said "just clean it up", proceed — but check in after surfacing the biggest wins before touching higher-risk changes.

---

## Step 3: Prioritize — High Value, Low Risk First

Rank your planned changes before writing a line:

**Do first (low risk, high clarity gain):**

- Rename variables/functions that lie about what they are
- Replace magic numbers/strings with named constants
- Remove dead code (grep callers first to be sure)
- Flatten nested conditionals into guard clauses / early returns
- Extract a well-understood block into a named function

**Do carefully (medium risk):**

- Split a large function into multiple helpers
- Extract a new class from mixed responsibilities
- Introduce a type/interface to replace a raw primitive or `any`
- Deduplicate logic across 3+ callsites

**Confirm with user first (higher risk):**

- Change a public API signature
- Reorganize modules or files
- Apply a structural design pattern (Strategy, Observer, etc.)
- Touch anything without test coverage

---

## Step 4: Execute in Small, Verified Steps

One change at a time. After each change:

1. Verify the code still does what it did (read the diff, check callers)
2. Run tests if they exist (`npm test`, `pytest`, `go test ./...`, etc.)
3. Confirm it still compiles / type-checks

Announce non-trivial changes before making them. If tests fail after a step, stop and diagnose before continuing.

**Hidden Bug Protocol:** If you uncover a pre-existing bug during refactoring: STOP. NEVER silently fix it within the refactoring step. Mixing structural changes with behavioral changes makes regressions impossible to untangle. Document it or fix it in an isolated, separate step.

**Automated Tooling First:** Before making manual stylistic changes, check if an ecosystem tool (`eslint --fix`, `prettier --write`, `go fmt`, `cargo fmt`) can do the heavy lifting safely and automatically.

### The right tool for each operation

**Extract function** — when a block has one clear purpose, is >20-30 lines, or a comment is explaining what it does (name the function instead of the comment).

**Rename** — when the name misleads. Grep all usages first; rename all at once. Don't rename just to rename.

**Inline** — when a function is called once and its name adds no clarity over reading the body.

**Flatten conditionals** — replace nested if/else chains with guard clauses. Replace switch-on-type with a lookup map or polymorphism when new variants are expected.

**DRY** — wait until 3+ real occurrences before extracting. Two similar-looking blocks with different semantics are not duplicates.

**Introduce type** — replace a raw primitive or anonymous object shape with a named type/interface. Especially at module boundaries and public APIs.

---

## Step 5: Communicate the Changes

After refactoring, explain briefly:

- **What changed**: file/function names, or a short summary ("Extracted `parseDate` from `processOrder`")
- **Why it matters**: what problem it solves ("It was doing 3 things — validation, transformation, and I/O — so I split those apart")
- **What's left** (optional): follow-on work worth doing, but don't do it unless asked

Keep it short. Skip obvious things. Focus on the _why_, not the _what_.

---

## Language Quick-Reference

**TypeScript/JavaScript**

- Prefer `const` and narrow union types over `any`
- Use `satisfies` to validate object shape without widening the type
- Prefer optional chaining (`?.`) and nullish coalescing (`??`) over deep null checks
- Use `Map`/`Set` instead of plain objects for dynamic-key collections
- Extract complex conditions into well-named boolean variables

**Python**

- `@dataclass` and `@property` for encapsulation without boilerplate
- `match` (3.10+) to replace chained `if/elif` type checks
- Prefer comprehensions over `map`/`filter`; use generators for large sequences
- Add type hints to all public function signatures
- Name complex boolean expressions as variables before using them in `if`

**Go**

- Keep interfaces small; accept interfaces, return structs
- Functional options (`WithTimeout(d time.Duration) Option`) for optional config
- Wrap errors: `fmt.Errorf("context: %w", err)` for traceable chains
- Named return values clarify intent at declaration; don't use them for naked returns

**Java / Kotlin**

- Prefer composition over inheritance; seal or finalize by default
- Replace `null` returns with `Optional<T>` (Java) or nullable types (Kotlin)
- Sealed classes for sum types where behavior varies per variant
- Builder pattern when a type has more than 4 optional fields

---

## Critical Anti-Patterns (NEVER do these)

- **NEVER mix behavior changes with structural changes:** Do not add features or fix bugs in the same step as a refactor. If a test fails, you won't know if the refactor broke it or the "fix" broke it.
- **NEVER extract based solely on structural similarity (Incidental Duplication):** Two blocks of code that _look_ identical but represent different business concepts should NOT be merged. They will evolve differently and force you to add awkward boolean flags later.
- **NEVER apply high-risk patterns without test coverage:** If there are no tests for complex logic, NEVER apply structural patterns like Strategy or Observer. Limit yourself to safe, mechanical renames or variable extractions unless you write characterization tests first.

---

## When to Stop

You've gone far enough when:

- The code reads as clearly as the comment that used to explain it
- A new case can be added without touching existing code
- Function names tell the story without reading the body

Stop before getting clever. A slightly under-abstracted design is better than a slightly over-engineered one.

---

## Reference Files (Conditional Loading)

**Do NOT load these files by default.** Only load them under these specific conditions:

- **When you spot a code smell but need a precise name and canonical fix strategy:** MANDATORY — READ ENTIRE FILE: [`references/smell-catalog.md`](references/smell-catalog.md).
- **When replacing complex conditionals with a structural design pattern:** MANDATORY — READ ENTIRE FILE: [`references/patterns.md`](references/patterns.md) before implementing the pattern.
