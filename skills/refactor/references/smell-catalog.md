# Code Smell Catalog

Quick reference for diagnosis and treatment. Each smell has: what you see, why it hurts, what to do.

---

## 1. Long Method / Function

**Symptoms:** Function longer than ~50 lines; needs a comment to explain each section; scrolling to read it.

**Why it hurts:** Hard to test, hard to name, hard to reuse any part of it.

**Fix:** Extract Method. Look for natural seams — blocks with a clear single purpose, blocks preceded by explanatory comments, blocks that operate on a different subset of variables. Each extracted function should be nameable in 3–5 words.

---

## 2. God Class / Module

**Symptoms:** A class with 20+ methods across unrelated domains (UserManager that also sends email and generates PDFs); a module that's imported by everything.

**Why it hurts:** Every change risks breaking unrelated behavior. Tests are complex. The class can't be understood without understanding the whole system.

**Fix:** Extract Class. Group methods by what data they operate on. Each resulting class should have a single, stateable reason to change.

---

## 3. Duplicated Code

**Symptoms:** The same logic copy-pasted across 3+ places (with minor variations).

**Why it hurts:** A bug fixed in one place lives on in the others. Logic drift over time.

**Fix:** Extract the shared logic. Be careful: two blocks that look similar but express different concepts shouldn't be merged — wait until you're sure the abstraction is real. Three occurrences is a stronger signal than two.

---

## 4. Long Parameter List

**Symptoms:** A function takes 5+ parameters; callers pass `null` for args they don't care about; parameters are always passed together.

**Why it hurts:** Hard to call correctly. Hard to evolve without breaking callers.

**Fix:** Introduce a Parameter Object (group into a struct/interface). Or consider whether the function is doing too much — if parameters belong to different concerns, the function may need to be split.

---

## 5. Primitive Obsession

**Symptoms:** Domain concepts represented as raw strings, numbers, or booleans (`status: string`, `userId: number`, `isAdmin: boolean`). Validation logic scattered at every callsite.

**Why it hurts:** Nothing prevents invalid values. Meaning is only in the name, not the type. Logic that belongs together is spread everywhere.

**Fix:** Introduce a Value Object or branded type. Put validation in the constructor. Let the type system enforce the invariant.

---

## 6. Feature Envy

**Symptoms:** A method in class A that spends most of its time reading fields from class B.

**Why it hurts:** Logic that belongs to B lives in A. Changes to B's internals require changing A.

**Fix:** Move the method (or the relevant portion) to class B. The rule of thumb: put code where the data is.

---

## 7. Shotgun Surgery

**Symptoms:** Changing one behavior requires edits to many unrelated files.

**Why it hurts:** Easy to miss a callsite. Hard to understand the full blast radius of a change.

**Fix:** Move scattered logic into one place — introduce a single class, module, or function that owns the behavior. Consider dependency inversion so changes flow through a single seam.

---

## 8. Data Clumps

**Symptoms:** The same 3–4 fields always appear together across functions, classes, and databases (e.g., `street, city, state, zip`).

**Why it hurts:** The group has semantics the code doesn't express. Callers have to know which fields go together.

**Fix:** Group into a named object (`Address`). Pass the object, not the fields.

---

## 9. Switch / if-else Chains on Type

**Symptoms:** Multiple switch/match statements or long if/elif chains that all branch on the same type field; adding a new type requires editing every switch.

**Why it hurts:** Adding a variant means touching every switch. Easy to miss one.

**Fix:** Replace with polymorphism (a class per variant, or a strategy/visitor) — if you control the type. If you don't, use a dispatch table (map from type → handler function).

---

## 10. Magic Numbers / Strings

**Symptoms:** Literal values appear in code without explanation (`if status === 2`, `timeout = 86400000`).

**Why it hurts:** No one knows what `2` means without reading history. Changing the value requires grep.

**Fix:** Named constant at the top of the file or in a constants module. The name should express the concept, not just the value.

---

## 11. Dead Code

**Symptoms:** Unused imports, unreachable branches, commented-out code, functions never called.

**Why it hurts:** Mental overhead. Readers waste time trying to understand dead code. Refactorings touch it unnecessarily.

**Fix:** Delete it. Git history preserves it if you ever need it back. Grep callsites before deleting a function.

---

## 12. Nested Conditionals (Arrow Code)

**Symptoms:** Code that indents 4+ levels deep due to nested if/else; else branches that are as long as the then branches.

**Why it hurts:** Hard to track what conditions are in effect at a given line. The happy path is buried.

**Fix:** Guard clauses (early returns for error/edge cases). Pull the error exits to the top; the happy path runs straight down. For complex boolean logic, extract named predicates.
