---
name: github-automation
description: "This skill should be used when the user asks to 'add CI', 'setup a release pipeline', 'harden a workflow', 'pin actions to SHA', 'setup OIDC for AWS/GCP/Azure', 'gh api script', 'least-privilege permissions', or 'headless GitHub automation'. Covers GitHub Actions YAML authoring with SHA-pinning, OIDC trust, and injection prevention; and headless gh CLI scripting with auth, pagination, and idempotency. Not for reviewing code quality or correctness (see request-code-review)."
---

# github-automation

Secure, high-performance GitHub automation.

## Process Flow

```
Trigger: Workflow/CLI Request
  -- yml / CI --> Path A: ACTIONS
                    -> 1. Classify Intent
                    -> 2. Author & Harden (SHA-pinning/OIDC)
                    -> 3. Validate & Audit (lint/security review)
                         -- runtime fail ---> diagnose (handoff)
                         -- hygiene issue --> refactor (handoff)
  -- gh / API --> Path B: CLI
                    -> 1. Mode Selection (inline vs script)
                    -> 2. Headless Standards (auth/paginate)
                    -> 3. Safety & Idempotency (snapshot/check existence)
                         -- script fail --> diagnose (handoff)
```

## NEVER Do This

- **NEVER** interpolate `${{ github.event... }}` directly into `run:`. **WHY:** This allows attackers to inject malicious shell commands if they control event data (e.g., PR titles). **FIX:** Always pipe inputs through `env:`.
- **NEVER** use `pull_request_target` to check out a PR head without manual auditing. **WHY:** It runs with repository secrets and write permissions; checking out untrusted code allows that code to exfiltrate secrets or corrupt the repo.
- **NEVER** use long-lived cloud credentials (IAM User keys, GCP JSON keys) as GitHub Secrets if the provider supports OIDC. **WHY:** Secrets never expire; OIDC tokens are short-lived and cryptographically bound to the specific repo/job.
- **NEVER** interpolate `${{ github.event.inputs.* }}` (workflow_dispatch inputs) directly into `run:`. **WHY:** These are attacker-controlled at trigger time just like PR titles — a primary, often-overlooked injection vector. **FIX:** Pipe through `env:` like any other untrusted input.
- **NEVER** use `secrets: inherit` on a called reusable workflow without confirming it actually needs every inherited secret. **WHY:** It silently widens the blast radius of a compromised reusable workflow to all secrets the caller holds.

## Routing Logic

| Signal                                                    | Path                |
| :-------------------------------------------------------- | :------------------ |
| `.github/workflows/*.yml`, \"add CI\", \"set up release\" | **Path A: ACTIONS** |
| `gh` script, batch API, headless automation               | **Path B: CLI**     |

All script paths below are relative to **this skill's directory** (the folder containing this SKILL.md), not the user's repo root. Resolve the absolute path to `scripts/` before invoking — e.g. `python3 "<skill_dir>/scripts/pin_actions.py" path/to/workflow.yml`.

## PATH A — ACTIONS: YAML Workflows

**action: Classify Intent**
Identify the workflow type and confirm via `AskUserQuestion` — the tool supplies a free-text "Other" automatically, so don't add one manually. There are exactly 3 named intents; surface the 2 most plausible as real options rather than padding with a generic one:

1. ✅ **Recommended** — [CI / Release / Deploy] based on [trigger and context: push vs tag vs environment target].
2. **Alternative** — [the next-most-plausible of the remaining two intents] + reason it might apply instead.

3. **Author with Hardening (Non-Negotiable):**
   - **MANDATORY:** Read `references/workflow-recipes.md` in full before authoring any workflow.
   - **MANDATORY (cloud deploy only):** Read `references/oidc-cloud.md` for provider-specific OIDC setup.
   - Do NOT load `references/headless-auth-patterns.md` or `references/api-pagination-and-limits.md` — those are Path B only.
   - **SHA-Pinning:** Replace `@v4` with `@<full_sha>`.
     - **Command:** `python3 scripts/pin_actions.py path/to/workflow.yml` (see path note above)
   - **Permissions:** Default to `contents: read`. Widen only where needed.
   - **OIDC:** Use `id-token: write` and cloud OIDC actions (AWS, GCP, Azure, HashiCorp Vault).
4. **Validate:**
   - **MANDATORY:** Read `references/security-hardening.md` before the audit step.
   - **Command:** `python3 scripts/lint.py path/to/workflow.yml` (see path note above)
   - Report linter tier (actionlint | yamllint | built-in Python check).
5. **Audit:** Dispatch the `general-purpose` subagent for semantic security review. Pass it the contents of `references/schemas.md` and require its findings in that JSON shape.

## PATH B — CLI: GitHub CLI Automation

**action: Mode Selection**
Identify the execution mode and confirm via `AskUserQuestion` — the tool supplies a free-text "Other" automatically, so don't add one manually:

1. ✅ **Recommended** — [Inline Command / Headless Script] based on [one-shot vs repeatable/batch complexity].
2. **Alternative** — [the other mode] + the condition under which it would actually be preferable.

3. **Headless Standards:**
   - **MANDATORY:** Read `references/headless-auth-patterns.md` and `references/api-pagination-and-limits.md` before writing the script.
   - Do NOT load `references/workflow-recipes.md` or `references/oidc-cloud.md` — those are Path A only.
   - Set `GH_PROMPT_DISABLED=1`.
   - Verify auth via `gh auth status` before mutation.
   - Use `gh api --paginate` with `--jq` for structured output.
4. **Safety:** Snapshot IDs before batch mutations. Add jitter/sleep for write loops.
5. **Idempotency:** Check existence before `POST`; prefer `PATCH`.

Both paths: if a script or workflow fails at runtime, read `references/troubleshooting.md` before handing off to `diagnose`.

## Mandatory Security Checklist

- [ ] `permissions:` set explicitly (no reliance on defaults).
- [ ] All third-party actions pinned to 40-char SHA via `pin_actions.py`.
- [ ] Untrusted inputs piped through `env:`, never `run:` interpolation.
- [ ] No long-lived cloud credentials (OIDC only for AWS/GCP/Azure/npm/PyPI).
- [ ] `pull_request_target` audited for PR head checkout (Forbidden).

## Reference Index

Loading is path-conditional and embedded as MANDATORY steps above — this is just an index, not a separate loading trigger.

- `references/workflow-recipes.md`, `references/oidc-cloud.md`, `references/security-hardening.md`, `references/schemas.md` — Path A only.
- `references/headless-auth-patterns.md`, `references/api-pagination-and-limits.md` — Path B only.
- `references/troubleshooting.md` — either path, on runtime failure.
- `references/topic-map.md` — conceptual lookup only; load on an explicit user question about how Actions/OIDC concepts work, not during normal authoring.
- **Verifying PR Statuses:** Use `scripts/inspect_pr_checks.py` to fetch checks/statuses for a PR head commit.

**next skills:**

- `verification-before-completion`: After updating workflows or automation scripts, to verify they pass linting and initial validation before committing.
- `diagnose`: If any `gh` or automation script fails at runtime, to root-cause the error trace rather than patching it blind.
- `refactor`: If validation/audit flags a structural or hygiene issue (not a runtime failure) in the workflow/script.

## Transition

1. **Fail:** Invoke `diagnose` or `refactor` based on blocking issue type.
2. **Script Error:** If any `gh` or automation script fails, immediately handoff to `diagnose` with the error trace.
