# Hard Rule Survey — Option Sets

These are the exact option sets used by the 3 `AskUserQuestion` prompts in Phase 0. Use this wording verbatim or near-verbatim. Each option lists the marker value it maps to (encoded later into the trailing `codebase-init:hard-rules` marker comment) so answers can be mapped unambiguously.

CI/CD Automation is **not** surveyed — it's auto-detected (see SKILL.md Phase 0).

## 1. Commit & attribution policy

Header: `Commit policy`

- Strict: Conventional Commits format (`type(scope): subject`) required, AND a mandatory `Co-Authored-By:` trailer on AI commits → `commit=strict`
- Relaxed: free-form commit messages allowed, but a mandatory `Co-Authored-By:` trailer on AI commits → `commit=relaxed`
- Minimal: no enforced message format, no required attribution trailer → `commit=minimal`

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

Use these signals, in order, to pick the ✅ Recommended option for each prompt — fall back to the first option if no signal is found:

1. **Commit & attribution policy:** Recommend `commit=strict` if `git log -20 --format=%s` shows >50% of subjects matching `type(scope): subject`; recommend `commit=relaxed` if a `CONTRIBUTING.md`/`.github/` template mentions commit conventions without enforcing a strict format; otherwise recommend `commit=minimal`.
2. **Project maturity state:** Recommend `maturity=production` if a version file/tag shows `>=1.0.0`, or a `CHANGELOG.md`/release workflow exists; otherwise recommend `maturity=development`.
3. **Testing rigor:** Recommend `testing=always` if CI config (`.github/workflows/*.yml`) runs the test suite on every PR; recommend `testing=touched-files` if tests exist but CI doesn't gate on them; otherwise recommend `testing=not-enforced`.

`ci=` is filled by `analyze-env`'s file-based detection (`.github/workflows/` → `github-actions`, `.gitlab-ci.yml` → `gitlab-ci`, otherwise `local-only`), never by survey.
