# make-a-skill — validation checklist

Human-readable mirror of what `scripts/validate_skill.py` enforces. Read this when a check fails and the
one-line message isn't enough context, or when drafting a skill by hand and you want to self-check before
running the validator.

## Frontmatter

- `name` must equal the skill's directory name exactly, and must be kebab-case (lowercase, hyphen-separated).
- `description` must be present and non-empty.
- `description` must not contain a leftover `{{FILL` marker — see §Description below for when to write the real one.
- `description` should be at least ~40 characters (long enough for Claude to judge when to invoke the skill) and under ~1024. Outside that range is a warning, not an error.
- `description` should end with an explicit `Trigger on: 'phrase one', 'phrase two', ...` clause — literal phrases a user might type. It's what lets Claude decide whether to auto-invoke.

## Body

- No `{{FILL: ...}}` placeholder should remain outside of inline code spans (a placeholder wrapped in single backticks is assumed to be prose _describing_ the convention, like this file and `SKILL.md` itself — not an unfilled section).
- Avoid vague adjectives the validator flags (`lightweight`, `clean`, `robust`, `fast`, `performant`, `easy`, `simple`) without a concrete, checkable claim backing them up.
- Avoid passive voice where an active, concrete instruction would be clearer.
- Keep the body under roughly 5000 estimated tokens (chars / 4) if there's no `references/` directory to push detail into — the Anthropic skill spec's progressive-disclosure guidance.

## References, scripts, evals

- Every `references/...`, `scripts/...`, or `evals/...` path linked from the body (in a markdown link or backtick-wrapped path) must point at a file that actually exists. A typo or rename here is always an error.
- A top-level file directly inside `scripts/` or `references/` whose filename never appears anywhere in the body is a warning — it may be invoked indirectly (e.g. via a `$CLAUDE_PLUGIN_ROOT`-prefixed path in a code fence) or genuinely orphaned. Use judgment; this check is intentionally scoped to top-level files only, not nested test/helper/fixture files, since those are usually implementation details.
- `evals/evals.json`, if present, must be valid JSON. Two top-level shapes are both accepted: a bare array of cases, or `{"skill_name": ..., "evals": [...]}`. Each case needs a `prompt` field at minimum; `assertions` or `expectations` should be present too, but the field name isn't enforced strictly, so a missing one is a warning, not an error.

## Description (write it last)

Don't write the real `description` until the body is finished — see `SKILL.md`'s Step 4. A description written before the body exists is a guess; one written after describes what the skill actually does. When you do write it:

- Third person, not imperative ("Scaffolds and validates...", not "Scaffold and validate...").
- Say what it's for, and name the sibling skill to use instead when this one doesn't apply, if there is one.
- End with `Trigger on: '...', '...'` — literal phrases a user might type, not abstract categories.

## Calibration

Per `agentskills.io`'s best-practices guidance: add what the agent wouldn't already know (project-specific conventions, non-obvious edge cases) and omit what it already knows (general programming concepts). If a section could be deleted without confusing a future reader, delete it rather than leaving boilerplate.
