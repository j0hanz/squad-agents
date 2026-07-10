---
name: project-init
description: 'Use when a repository needs AGENTS.md, CLAUDE.md, or GEMINI.md — initializing a new repo, bootstrapping agent instructions, or auditing an existing instructions file. Prefer over hand-writing AGENTS.md/CLAUDE.md from scratch.'
disable-model-invocation: false
allowed-tools: Bash(python *), Bash(python3 *), AskUserQuestion, Skill(dispatch-agents), Skill(diagnose), Read, Grep, Glob
---

# project-init

## Overview

Bootstraps a repository's agent instructions via a blind parallel discovery fan-out converging into a deterministic generator.

- **Goal:** A lean, high-signal `AGENTS.md` (<100 lines, sectioned bullet lists — no `key:` labels, no filler prose) + one-line stub `CLAUDE.md`/`GEMINI.md` that redirect to it.
- **Method:** Blind parallel discovery (read-only Researcher fan-out, evidence-cited claims) → ONE deterministic generator (`scripts/init.py`) verifies, merges, writes.
- **Invariant:** Discovered commands are transcribed as TEXT, never executed. `init.py` is the SOLE writer.

- **Phase 0: PRESCAN + SURVEY**
  - _valid project-init marker found_: reuse encoded answers (offer --force re-survey) -> Phase 1
  - _no marker_: AskUserQuestion (4 Qs) -> Phase 1
  - _no manifest (trivial repo)_: single serial discovery lane (skip fan-out) -> Phase 2
- **Phase 1: DISCOVERY FAN-OUT (blind, read-only, claims as JSON)**
  - L1 build+PM | L2 stack+layout | L3 conventions+CI+docs (monorepo: + per-package lanes, batch <=3) -> Phase 2
- **Phase 2: MERGE (preview)** (init.py generate --claims claims.json, no --out)
  - _lint FAIL_: fix inputs / re-dispatch the failing lane
  - _preview OK_: show AGENTS.md + dropped report to user -> Phase 3
- **Phase 3: CONSENT + WRITE**
  - _existing authored file_: back up + explicit overwrite consent
  - _approved_: generate --out | wire stubs | lint | receipt -> DONE

**trigger:** bootstrap agent instructions, initialize repository, audit AGENTS.md, create CLAUDE.md, create GEMINI.md

## Phase 0: Check and Ask

**mandatory:** Read the option mappings and CI detection rules in `references/hard-rules.md`.

1. **action:** Run prescan using `python "${CLAUDE_SKILL_DIR}/scripts/init.py" prescan .` (hereafter `init.py`).
2. **action:** Read `AGENTS.md` if present. If it has the `<!-- project-init:hard-rules... -->` tag, reuse those answers (`commit=`, `maturity=`, `testing=`, `ci=`, and `sections=` if present — default missing `sections=` to "include everything"). Do not re-survey unless forced.
3. **action:** If no old rules exist, run `AskUserQuestion` exactly once with all 4 questions from `references/hard-rules.md`. Use the exact wording provided, and stop if the user cancels.
4. **action:** Choose path:
   - If `has_manifest == false` (trivial repo), skip Phase 1 and go to Phase 2, using `Glob`/`Grep`/`Read` to explore the project.
   - If `is_monorepo == true`, follow the **Monorepo Variation** for all subsequent phases.
   - Otherwise, go to Phase 1.

**gate:** `init.py prescan` completed, hard-rules answers resolved, and path (standard Phase 1, trivial Phase 2, or monorepos) chosen.

## Phase 1: Search (Read-Only)

**mandatory:** Ensure all discovery agents validate claims against `references/canonical-keys.md`.
**constraint:** Read-only. DO NOT execute commands or use Bash. Every claim must cite a file path and exact quote.

1. **action:** Dispatch 3 parallel read-only agents via `dispatch-agents`, sharing all Phase 0 facts.
2. **action:** Assign lanes:
   - **Lane 1 (Build):** package managers, build steps, run commands.
   - **Lane 2 (Structure):** coding languages, frameworks, folder setup.
   - **Lane 3 (Rules):** format rules, CI steps, old rule files.
3. **action:** Output a single JSON list of facts matching the vocabulary in `references/canonical-keys.md`.

**gate:** 3 lanes have returned valid JSON fact lists, each citing a file path and exact quote.

## Phase 2: Check and Preview

1. **action:** Merge all Phase 1 facts into `claims.json`.
2. **action:** Run `init.py generate --claims claims.json --commit <c> --maturity <m> --testing <t> --ci <ci> --skip-sections <s>` (no `--out`).
3. **action:** Display the draft `AGENTS.md` and dropped-facts list. If errors occur, fix inputs or re-run the failing agent.

**gate:** Preview prints the draft and dropped-facts list with no lint errors, and the user has seen the output.

## Phase 3: Ask and Save

**constraint:** Make a backup (`.bak`) and ask for explicit permission before replacing any existing `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`.
**constraint:** NEVER copy text into a stub file. Stub files must only use redirects.

1. **action:** Save the root instructions: `init.py generate --claims claims.json --commit <c> --maturity <m> --testing <t> --ci <ci> --skip-sections <s> --out AGENTS.md`.
2. **action:** Wire redirects: `init.py wire AGENTS.md CLAUDE.md GEMINI.md` to establish root-level redirects.
3. **action:** Validate output: Run `init.py lint AGENTS.md`. It must pass.
4. **action:** Report results, listing saved files, line counts, and dropped facts.

**gate:** `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` are written, `init.py lint` passes, and the receipt is shown.

## Monorepo Variation

**action:** If the repository is a monorepo:

1. **Phase 1 (Discovery):** Dispatch one agent per package folder (batch size <= 3). If >6 packages, request user permission before dispatching.
2. **Phase 2 (Preview):** Run `init.py generate` with the `--package <pkg>` option for each package folder in `packages` to preview the draft.
3. **Phase 3 (Save):**
   - Save package files using: `init.py generate ... --package <pkg> --out <pkg>/AGENTS.md`.
   - Lint each package file using: `init.py lint <pkg>/AGENTS.md`.
   - Ensure backups and consent constraints apply to all package-level `<pkg>/AGENTS.md` files.

## Error Recovery

**constraint:** If a script fails, fix the underlying inputs or script and restart the current phase. Do not restart Phase 0.
