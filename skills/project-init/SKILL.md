---
name: project-init
description: "Bootstrap a repo's agent instructions via a blind parallel discovery fan-out converging into a deterministic generator. Produces a lean (<100-line) markdown-kv AGENTS.md plus one-line CLAUDE.md/GEMINI.md redirect stubs. Discovery agents are read-only and emit evidence-cited claims; a single script is the sole writer and never executes a discovered command. Trigger on: 'init project', 'project-init', 'onboard repo', 'generate AGENTS.md', 'setup agent instructions', 'initialize project memory', 'audit AGENTS.md'."
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash(python *) Bash(python3 *) AskUserQuestion Skill Read Grep Glob Agent
---

# project-init

**goal:** A lean, high-signal `AGENTS.md` (`<100` lines, markdown-kv `key: value`, never prose) + one-line stub `CLAUDE.md`/`GEMINI.md` that redirect to it.
**method:** Blind parallel discovery (read-only Researcher fan-out, evidence-cited claims) → ONE deterministic generator (`scripts/init.py`) that verifies, merges, and writes.
**invariant:** Discovered commands are transcribed as TEXT, never executed. `init.py` is the SOLE writer.

```
Phase 0  PRESCAN + SURVEY
  -- valid project-init marker found --> reuse encoded answers (offer --force re-survey) --> Phase 1
  -- no marker -----------------------> AskUserQuestion (3 Qs) ------------------------------> Phase 1
  -- no manifest (trivial repo) ------> single serial discovery lane (skip fan-out) ---------> Phase 2

Phase 1  DISCOVERY FAN-OUT  (blind, read-only, claims as JSON)
  L1 build+PM | L2 stack+layout | L3 conventions+CI+docs    (monorepo: + per-package lanes, batch <=3)
  ------------------------------------------------------------------------------------> Phase 2

Phase 2  MERGE (preview)   init.py generate --claims claims.json (no --out)
  -- lint FAIL -------> fix inputs / re-dispatch the failing lane
  -- preview OK ------> show AGENTS.md + dropped report to user --------------------------> Phase 3

Phase 3  CONSENT + WRITE
  -- existing authored file --> back up + explicit overwrite consent
  -- approved ---------------> generate --out --model | wire stubs | lint | receipt --> DONE
```

---

## Phase 0: Check and Ask

1. **Scan:** Run `python "$CLAUDE_PLUGIN_ROOT/skills/project-init/scripts/init.py" prescan .` to get project details.
2. **Check for Old Rules:** Look for `AGENTS.md`. If it has the `<!-- project-init:hard-rules... -->` tag, use those answers. Do not ask the user again unless they force it.
3. **Ask the User (if no old rules):** Run `AskUserQuestion` exactly once. Ask the 3 questions from `references/hard-rules.md` (commit policy, project maturity, testing rigor). Use the exact words provided. Do not add an "Other" choice. Stop if the user cancels.
4. **Find CI Automatically:** Do not ask the user about CI. Look for folders: `.github/workflows/` means `github-actions`, `.gitlab-ci.yml` means `gitlab-ci`. Otherwise, use `local-only`.
5. **Choose Path:** If the scan says `has_manifest == false`, read the project files yourself, skip Phase 1, and go straight to Phase 2. Otherwise, go to Phase 1.

---

## Phase 1: Search (Read-Only)

1. **Send Searchers:** Use `multi-agent-dispatch` to send 3 read-only agents at the same time. Give them all facts found in Phase 0.
2. **Assign Lanes:**

- **Lane 1 (Build):** Find package managers, build steps, and run commands.
- **Lane 2 (Structure):** Find coding languages, frameworks, and folder setup.
- **Lane 3 (Rules):** Find format rules, CI steps, and old rule files.

3. **Big Projects (Monorepo):** Add one agent per package folder (run 3 at a time). If there are more than 6 packages, ask the user for permission first.
4. **Strict Rules for Searchers:**

- They can ONLY read files.
- **NO Bash. NO running commands.**
- They must prove every fact by quoting the exact text and naming the file.

5. **Output:** The agents must only output a JSON list of facts matching `references/canonical-keys.md`. No extra text.

---

## Phase 2: Check and Preview

1. **Combine:** Put all facts from Phase 1 into one file called `claims.json`.
2. **Test:** Run `init.py generate --claims claims.json --commit <c> --maturity <m> --testing <t> --ci <ci>` (Do not use `--out`. Just print it to the screen).
3. **Filter:** The script will keep only proven facts and drop bad ones.
4. **Show the User:** Show the user the draft of `AGENTS.md` and the list of dropped facts. If there is an error, fix the inputs or rerun the bad agent. Do not save yet.

---

## Phase 3: Ask and Save

1. **Protect Old Files:** If `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` already exist, show them to the user, make a backup (`.bak`), and **ask for explicit permission** before replacing them.
2. **Save:** Run `init.py generate --claims claims.json ... --model "<active model name>" --out AGENTS.md`.
3. **Link Files:** Run `init.py wire AGENTS.md CLAUDE.md GEMINI.md`.
4. **Test the File:** Run `init.py lint AGENTS.md`. It must pass.
5. **Report to User:** Tell the user what files were saved, how many lines they have, and remind them of the facts that were dropped.

---

## Fixing Errors

- If any script fails, use the `diagnose` skill on the error message. Fix the problem and restart the current phase. Never restart Phase 0.
- When done, run `verification-before-completion`.

---

## STRICT PROHIBITIONS (NEVER DO THESE)

- **NEVER** run any command found in the project.
- **NEVER** give search agents access to Bash.
- **NEVER** write or edit `AGENTS.md` by hand. Only the `init.py` script is allowed to write it.
- **NEVER** copy text into a stub file.
- **NEVER** replace existing rule files without backing them up and asking the user.
- **NEVER** keep a fact if you cannot prove it with a real file path and an exact quote.
