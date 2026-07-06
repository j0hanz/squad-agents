---
name: hard-rules
description: Verbatim option sets for the four Phase-0 AskUserQuestion survey prompts in project-init.
type: reference
canonical: true
---

# Hard Rule Survey: Option Sets

The exact option sets for the 4 `AskUserQuestion` prompts in Phase 0 (one tool call: the tool allows up to 4 questions per call). Use this wording verbatim or near-verbatim. Each option lists the marker value it maps to (encoded into the trailing `project-init:hard-rules v1` marker comment so a re-run can reuse the answers unambiguously).

CI/CD Automation is **not** surveyed: it is file-detected (see below). It is also the one field with no "Don't include" option, since every AGENTS.md needs to say how a change gets verified before it ships.

Every other question gets a **"Don't include"** option (4th option, `=skip`). A user who finds a line not worth the words it'd cost in a <100-line budget should be able to say so without lying about their actual policy by picking the closest wrong answer.

The option prose below must stay byte-identical with `HARD_RULES_TEXT` in `scripts/init.py` (the script renders from its own copy; this file is what the survey question shows the user).

## 1. Commit & attribution policy

Header: `Commit policy`

- Strict: Conventional Commits format (`type(scope): subject`) required (see `pr-workflow` skill) → `commit=strict`
- Relaxed: Free-form commit messages allowed (see `pr-workflow` skill) → `commit=relaxed`
- Minimal: No enforced message format → `commit=minimal`
- Don't include: omit the commit-policy line from AGENTS.md → `commit=skip`

Message construction, atomicity, and issue refs belong to the `pr-workflow` skill, which reads this `commit=` marker. They aren't duplicated here.

## 2. Project maturity state

Header: `Project maturity`

- Production: Stability first: avoid breaking changes, prefer additive ones, and flag any breaking change before you ship it → `maturity=production`
- Development: Breaking changes are fine. Never add fallback/legacy-compat shims; rewrite to the better approach directly → `maturity=development`
- Don't include: omit the maturity line from AGENTS.md → `maturity=skip`

## 3. Testing rigor

Header: `Testing rigor`

- Always required: Every change must have passing tests before being called done → `testing=always`
- Touched-files only: Test/typecheck only files you changed; do not require full-suite runs → `testing=touched-files`
- Not enforced: No automatic testing requirement; rely on existing CI → `testing=not-enforced`
- Don't include: omit the testing-rigor line from AGENTS.md → `testing=skip`

## 4. Optional sections to omit

Header: `Sections`

multiSelect: the user may pick 0 to 3. **Leaving none selected means include everything that gets discovered**, which is the lazy default and needs no explanation to the user.

- Key Conventions: never show a `## Key Conventions` section, even if conventions are discovered → exclude `conv.*` (`conventions`)
- Dependency Locations: never show a `## Dependency Locations` section, even if discovered → exclude `dep.*` (`dependencies`)
- File-Scoped Commands: never show the `## File-Scoped Commands` table, even if discovered → exclude `file.*` (`file-commands`)

This question exists because the <100-line budget already drops the lowest-priority facts under pressure, but a user might want a section gone on principle (e.g. "we don't want dependency paths hardcoded into agent docs at all"), not just trimmed when space runs short. Pass the comma-joined selected names to `init.py generate --skip-sections <names>` (e.g. `--skip-sections conventions,dependencies`). Purpose/stack/Hard-Rules/Package-Manager are never offered here: they're load-bearing, not optional.

## Recommendation Heuristics

Pick the `(Recommended)` option per prompt from these signals (fall back to the first option if no signal). **Never recommend "Don't include."** Skip is an opt-out the user reaches for deliberately, not something to default them into.

1. **Commit policy:** `commit=strict` if `git log -20 --format=%s` shows >50% matching `type(scope): subject`; `commit=relaxed` if a `CONTRIBUTING.md`/`.github/` template mentions commit conventions without strict enforcement; else `commit=minimal`.
2. **Maturity:** `maturity=production` if a version/tag shows `>=1.0.0`, or a `CHANGELOG.md`/release workflow exists; else `maturity=development`.
3. **Testing rigor:** `testing=always` if CI runs the suite on every PR; `testing=touched-files` if tests exist but CI doesn't gate on them; else `testing=not-enforced`.
4. **Sections:** no signal-based recommendation; default is "nothing selected" (include everything discovery finds).

## CI detection (never surveyed)

`.github/workflows/` with at least one workflow file → `ci=github-actions`; `.gitlab-ci.yml` → `ci=gitlab-ci`; otherwise → `ci=local-only`. Pass the result to `init.py generate --ci <value>`.

## Re-survey reuse

The marker now also carries `sections=<csv|none>` (e.g. `sections=conventions,dependencies` or `sections=none`). When Phase 0 finds an existing marker, reuse this field the same way as `commit=`/`maturity=`/`testing=`. A marker written before this field existed simply has no `sections=` token. Treat that as `sections=none` (include everything), since that was the only behavior possible before.
