# Hard Rule Survey — Option Sets

The exact option sets for the 3 `AskUserQuestion` prompts in Phase 0. Use this wording verbatim or near-verbatim. Each option lists the marker value it maps to (encoded into the trailing `project-init:hard-rules v1` marker comment so a re-run can reuse the answers unambiguously).

CI/CD Automation is **not** surveyed — it is file-detected (see below).

## 1. Commit & attribution policy

Header: `Commit policy`

- Strict: Conventional Commits format (`type(scope): subject`) required → `commit=strict`
- Relaxed: free-form commit messages allowed → `commit=relaxed`
- Minimal: no enforced message format → `commit=minimal`

Message construction, atomicity, and issue refs are owned by the `pr-workflow` skill, which reads this `commit=` marker — not duplicated here.

## 2. Project maturity state

Header: `Project maturity`

- Production: stability first — avoid breaking changes, prefer additive changes, flag breaking changes explicitly before making them → `maturity=production`
- Development: breaking changes are fine — never add fallback/legacy-compat shims, rewrite to the better approach directly → `maturity=development`

## 3. Testing rigor

Header: `Testing rigor`

- Always required: every change must have passing tests before being called done → `testing=always`
- Touched-files only: test/typecheck files you changed; don't require full-suite runs → `testing=touched-files`
- Not enforced: no automatic testing requirement, rely on existing CI → `testing=not-enforced`

## Recommendation Heuristics

Pick the ✅ Recommended option per prompt from these signals (fall back to the first option if no signal):

1. **Commit policy:** `commit=strict` if `git log -20 --format=%s` shows >50% matching `type(scope): subject`; `commit=relaxed` if a `CONTRIBUTING.md`/`.github/` template mentions commit conventions without strict enforcement; else `commit=minimal`.
2. **Maturity:** `maturity=production` if a version/tag shows `>=1.0.0`, or a `CHANGELOG.md`/release workflow exists; else `maturity=development`.
3. **Testing rigor:** `testing=always` if CI runs the suite on every PR; `testing=touched-files` if tests exist but CI doesn't gate on them; else `testing=not-enforced`.

## CI detection (never surveyed)

`.github/workflows/` with at least one workflow file → `ci=github-actions`; `.gitlab-ci.yml` → `ci=gitlab-ci`; otherwise → `ci=local-only`. Pass the result to `init.py generate --ci <value>`.
