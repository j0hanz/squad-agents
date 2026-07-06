---
name: project-init
description: 'Use when a repository needs AGENTS.md, CLAUDE.md, or GEMINI.md — initializing a new repo, bootstrapping agent instructions, or auditing an existing instructions file. Prefer over hand-writing AGENTS.md/CLAUDE.md from scratch.'
disable-model-invocation: false
allowed-tools: Bash(python *), Bash(python3 *), AskUserQuestion, Skill(multi-agent-dispatch), Skill(diagnose), Read, Grep, Glob
---

# project-init

## Overview

Bootstraps a repository's agent instructions via a blind parallel discovery fan-out converging into a deterministic generator.

- **Goal:** A lean, high-signal `AGENTS.md` (<100 lines, sectioned bullet lists — no `key:` labels, no filler prose) + one-line stub `CLAUDE.md`/`GEMINI.md` that redirect to it.
- **Method:** Blind parallel discovery (read-only Researcher fan-out, evidence-cited claims) → ONE deterministic generator (`scripts/init.py`) verifies, merges, writes.
- **Invariant:** Discovered commands are transcribed as TEXT, never executed. `init.py` is the SOLE writer.

```
Phase 0  PRESCAN + SURVEY
  -- valid project-init marker found --> reuse encoded answers (offer --force re-survey) --> Phase 1
  -- no marker -----------------------> AskUserQuestion (4 Qs) ------------------------------> Phase 1
  -- no manifest (trivial repo) ------> single serial discovery lane (skip fan-out) ---------> Phase 2

Phase 1  DISCOVERY FAN-OUT  (blind, read-only, claims as JSON)
  L1 build+PM | L2 stack+layout | L3 conventions+CI+docs    (monorepo: + per-package lanes, batch <=3)
  ------------------------------------------------------------------------------------> Phase 2

Phase 2  MERGE (preview)   init.py generate --claims claims.json (no --out)
  -- lint FAIL -------> fix inputs / re-dispatch the failing lane
  -- preview OK ------> show AGENTS.md + dropped report to user --------------------------> Phase 3

Phase 3  CONSENT + WRITE
  -- existing authored file --> back up + explicit overwrite consent
  -- approved ---------------> generate --out | wire stubs | lint | receipt --> DONE
```

## Phase 0: Check and Ask

**MANDATORY**: Before the survey, you MUST read the option mappings in `references/hard-rules.md`. Do NOT load `references/canonical-keys.md` during this phase.

1. **Scan:** Run `python "${CLAUDE_SKILL_DIR}/scripts/init.py" prescan .` (below, `init.py` is shorthand for this same invocation).
2. **Check for Old Rules:** Read `AGENTS.md` if present. If it has the `<!-- project-init:hard-rules... -->` tag, reuse those answers (`commit=`, `maturity=`, `testing=`, `ci=`, and `sections=` if present — a marker written before `sections=` existed has none, treat as "include everything"). Do not ask again unless the user forces it.
3. **Ask the User (if no old rules):** Run `AskUserQuestion` exactly once with all 4 questions from `references/hard-rules.md` (commit policy, project maturity, testing rigor, optional sections to omit — last is multiSelect, 0–3 picks). Use the exact words provided, including the "Don't include" option on the first three. Do not add an "Other" choice (the tool already provides one). Stop if the user cancels.
4. **Find CI Automatically:** Do not ask about CI. `.github/workflows/` → `github-actions`; `.gitlab-ci.yml` → `gitlab-ci`; otherwise `local-only`. CI is never skippable.
5. **Choose Path:** If the scan says `has_manifest == false`, explore the project yourself (`Glob` for structure, `Grep` for content, `Read` for specific files), skip Phase 1, go straight to Phase 2. Otherwise, go to Phase 1.

**Done when:** `init.py prescan .` has run, the hard-rules answers are resolved (from old marker or `AskUserQuestion`), and the next phase is chosen (Phase 1 fan-out, or straight to Phase 2 if `has_manifest == false`).

## Phase 1: Search (Read-Only)

**MANDATORY**: Ensure all discovery agents validate claims against the closed vocabulary in `references/canonical-keys.md`. Do NOT load `references/hard-rules.md` during this phase.

1. **Send Searchers:** Use `multi-agent-dispatch` to send 3 read-only agents in parallel. Give them all facts found in Phase 0.
2. **Assign Lanes:**

- **Lane 1 (Build):** package managers, build steps, run commands.
- **Lane 2 (Structure):** coding languages, frameworks, folder setup.
- **Lane 3 (Rules):** format rules, CI steps, old rule files.

3. **Big Projects (Monorepo):** Add one agent per package folder (run 3 at a time). If more than 6 packages, ask the user for permission first.
4. **Strict Rules for Searchers:**

- Read-only. NO Bash. NO running commands.
- Prove every fact by quoting the exact text and naming the file.

5. **Output:** A JSON list of facts matching `references/canonical-keys.md`. No extra text.

**Done when:** 3 read-only Researcher lanes (plus per-package lanes for monorepos) have returned JSON fact lists matching `references/canonical-keys.md`, with every claim citing a file path and exact quote.

## Phase 2: Check and Preview

1. **Combine:** Put all Phase 1 facts into one file `claims.json`.
2. **Test Root:** Run `init.py generate --claims claims.json --commit <c> --maturity <m> --testing <t> --ci <ci> --skip-sections <s>` (no `--out`; print to screen). Omit `--skip-sections` entirely if the user selected nothing.
3. **Test Packages (Monorepos):** If prescan shows `is_monorepo == true`, run the generate preview for each package folder `<pkg>` in `packages`:
   `init.py generate --claims claims.json --package <pkg> --commit <c> --maturity <m> --testing <t> --ci <ci> --skip-sections <s>`
4. **Filter:** The script keeps only proven facts and drops bad ones.
5. **Show the User:** Show the draft `AGENTS.md` (root and packages) and the dropped-facts list. If there is an error, fix the inputs or rerun the failing agent. Do not save yet.

**Done when:** `init.py generate --claims claims.json` (no `--out`) prints an `AGENTS.md` draft and the dropped-facts list with no lint errors, and the user has seen both.

## Phase 3: Ask and Save

1. **Protect Old Files:** If root `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` already exist, or any package-level `<pkg>/AGENTS.md` exists, show them to the user, make a backup (`.bak`), and **ask for explicit permission** before replacing them.
2. **Save Root:** Run `init.py generate --claims claims.json --commit <c> --maturity <m> --testing <t> --ci <ci> --skip-sections <s> --out AGENTS.md`.
3. **Save Packages (Monorepos):** For each package folder `<pkg>`, run:
   `init.py generate --claims claims.json --package <pkg> --commit <c> --maturity <m> --testing <t> --ci <ci> --skip-sections <s> --out <pkg>/AGENTS.md`.
4. **Link Files:** Run `init.py wire AGENTS.md CLAUDE.md GEMINI.md` (root-level redirect stubs only).
5. **Test Root File:** Run `init.py lint AGENTS.md`. It must pass.
6. **Test Package Files (Monorepos):** For each package folder `<pkg>`, run `init.py lint <pkg>/AGENTS.md`. They must pass.
7. **Report to User:** Tell the user what files were saved, how many lines they have, and remind them of the dropped facts.

**Done when:** `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` (plus any package-level `<pkg>/AGENTS.md`) are written, `init.py lint AGENTS.md` passes, and the receipt lists saved files and dropped facts.

## Fixing Errors

- If any script fails, use the `diagnose` skill on the error message. Fix the problem and restart the current phase. Never restart Phase 0.

## Rules

### STRICT PROHIBITIONS (NEVER DO THESE)

- **NEVER** copy text into a stub file.
- **NEVER** replace existing rule files without backing them up and asking the user.
- **NEVER** keep a fact lacking a real file path and an exact quote as proof.
