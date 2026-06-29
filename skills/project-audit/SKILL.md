---
name: project-audit
description: 'Use when the codebase has structural problems — circular dependencies, infra code bleeding into domain logic, hidden coupling, God files, unclear module responsibilities, or modules whose stated purpose contradicts how other modules actually use them. Parallel per-directory agent judgment, not static-analysis scripts.'
disable-model-invocation: false
allowed-tools: Bash(python *), Bash(python3 *), Agent(researcher)
---

# project-audit

```
Trigger: structural/architecture audit request
  -> 1. GROUP   (band repo into ≤8 lanes, drop non-code dirs)
  -> 2. LAUNCH  (parallel researcher per lane, 5 fixed questions)
  -> 3. AGGREGATE (check_cycles.py join + synthesis prompt)
  -> 4. OUTPUT  (flat, corroborated-first report)
```

- **Trigger:** circular dependencies, infra-bleed, hidden coupling, God files, unclear/contradictory module responsibilities. Not for bugs (`diagnose`), security/diffs (`find-bugs`, `security-review`), or over-engineering/YAGNI (`ponytail-audit`) — this skill is structural/architecture only.

## Step 1: GROUP

- List the target repo's top-level directories one level deep (`Glob` for entries, no file content read).
- Drop directories that are obviously non-code by name/pattern: `docs`, `.github`, `.git`, `node_modules`, `dist`, `build`, lockfile-only directories. No agent dispatch wasted on them.
- Band the remaining directories into **at most 8 lanes** by file count: merge directories with very few files into the nearest lane, split a directory with disproportionately many files into multiple lanes within the same directory. Never dispatch more than 8 lanes, regardless of repo size — this is the hard cap that keeps cost and latency bounded.
- **Flat-repo fallback:** if there are no meaningful subdirectories (everything under one `src/`), chunk files by detected primary file extension (group `.ts`/`.tsx` together, `.py` together, etc.) instead of alphabetically — still cheap and mechanical, no parsing. **Mandatory:** when this fallback fires, the final report header MUST say so and add: "findings below use arbitrary file-extension chunks, not real module boundaries — treat purpose and contradiction findings with reduced confidence." Never omit this line when the fallback is used.

## Step 2: LAUNCH

Dispatch one `researcher` subagent per lane, **in parallel, in one message**. Tool grant: `Read, Grep, Glob, Bash` only — **never WebFetch**, no question below needs an external URL, and granting it only widens the blast radius if a lane reads adversarial/prompt-injected content.

Each lane agent is scoped to read ONLY its own lane's files and answer exactly these five questions, in free text:

1. **Purpose:** "State this lane's job in one sentence. If you cannot state a single coherent purpose, say so explicitly — that itself is a finding."
2. **Imports out:** "List every import this lane has from outside itself, as literal import paths copied character-for-character from the source line, with the file it came from. Do not paraphrase — this list gets mechanically cross-referenced against other lanes."
3. **Bleed smell:** "Does this lane mix infrastructure concerns (I/O, DB/HTTP clients, filesystem, framework glue) directly into what looks like core/domain logic in the same file? Name the specific file and quote the pattern if so."
4. **Size/cohesion outliers:** "Is there a file here that's unusually large or doing several unrelated things? Name the file; say whether its size is one cohesive concept or several jammed together."
5. **Hidden coupling:** "Is this lane coupled to something elsewhere in the repo in a way that isn't a normal import (shared global state, monkeypatching, naming-convention contracts)? Name the specific file or lane if so."

**Redaction (load-bearing, not optional):** before any quoted text from Q2/Q3 leaves the lane agent's answer, redact any line that looks like a credential — API keys, tokens, passwords, AWS-key-shaped strings, high-entropy strings — replacing it with `[redacted: possible credential]`. This is a heuristic, not a guarantee; state that plainly in the final report, never imply secrets are guaranteed-safe to quote.

If a lane has nothing to report across all five questions, its entry in the final report compresses to one line: `Lane <name>: nothing flagged.`

## Step 3: AGGREGATE

- Run `python ${CLAUDE_SKILL_DIR}/scripts/check_cycles.py` against all lanes' Q2 answers (pass lane→directory-prefix mapping and each lane's raw import list). It normalizes superficial formatting, resolves each import to its owning lane, drops intra-lane edges, and returns confirmed inter-lane cycles. **This is a best-effort secondary signal** — a lane agent that phrases an import inconsistently or misses one produces a silent false negative; state this in the report, never present cycle detection as exhaustive.
- Run one synthesis pass (a prompt, not a script) over all lane answers that does four things:
  1. **Corroboration ranking:** any finding independently mentioned by 2+ lanes is surfaced first, labeled "corroborated by N lanes." Single-lane findings come after, labeled as such.
  2. **Adjudication:** for every purpose-vs-coupling contradiction (lane X's Q1 conflicts with what another lane's Q3/Q5 says about it), state which side the evidence favors — a concrete quoted file/pattern outranks an unverified self-description. Only present it as a genuinely open question when both sides have comparably concrete evidence.
  3. **Pattern merging:** if 3+ lanes independently report the same finding shape (e.g., "mixes infra into domain"), merge into one repo-wide pattern finding instead of listing it once per lane.
  4. **Overlap detection:** compare every pair of lanes' Q1 answers for plausible responsibility overlap (two lanes both claiming the same job) — no other step catches this.

## Step 4: OUTPUT

One flat report. Each finding: `{finding, kind (cycle / bleed / cohesion / coupling / intent-mismatch / overlap), corroboration (N lanes, or "single-lane"), evidence}`. Corroborated findings first. **No numeric score, no HIGH/MEDIUM/LOW tier, no borrowed severity vocabulary** — corroboration count is the only ranking signal, and it means something different (independent agreement, not absolute severity). No ADR, no scaffold, no handoff artifact file. Close with: "Start with corroborated findings above; `request-plan` can formalize any single-lane finding you want to act on."

## Heuristics

- **No detection scripts beyond `check_cycles.py`.** The five questions are answered by judgment, not regex/AST. If you find yourself writing a second analysis script, stop — that's drifting back toward the retired `architecting` skill's mechanism, which this skill was explicitly built to not be.
- **Scale:** the 8-lane cap is the load-bearing scale control. Lane size still varies within a band — wall-clock is bounded by whatever lane lands largest, not perfectly equal. This is accepted, not solved further.

## Worked Example

11 directories → 7 lanes (merged 2 single-file dirs, split 1 400-file dir). Lane `billing` claims "pure billing calculations"; lane `infra/db` reports reaching directly into `billing/Invoice`'s private ledger field — concrete evidence outranks the unverified self-description, so this surfaces as a confirmed intent-mismatch. Two other lanes report the same shape from `infra/db`, pattern-merged into one 3-lane finding. Report leads with that pattern, then the single-lane contradiction, then the rest.

## Next Skills

- **request-plan:** formalize a fix for any specific finding.
- **diagnose:** if a finding turns out to be a live, currently-failing bug rather than structural debt.
- **multi-agent-development:** execute a multi-file structural fix once planned.

Hard limits (read-only diagnosis, no scope creep): no new-module design, no ADR, no scaffolding; never grant the lane `researcher` dispatch `WebFetch`; never skip redaction before quoting source text. No overlap with `find-bugs`, `security-review`, or `ponytail-audit` — stay structural.
