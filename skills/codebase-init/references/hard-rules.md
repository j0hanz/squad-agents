# Hard Rule Survey — Option Sets

These are the exact option sets used by the 3 `AskUserQuestion` prompts in Phase 0. Use this wording verbatim or near-verbatim. Each option lists the marker value it maps to (encoded later into the trailing `codebase-init:hard-rules` marker comment) so answers can be mapped unambiguously.

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
