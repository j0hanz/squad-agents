---
name: gh-actions
description: 'Generates, audits, and hardens GitHub Actions workflows and headless gh CLI scripts from user requirements. Use when the user requests "setup CI/CD", "add GitHub Actions", "pin workflows to SHA", "configure OIDC authentication", "harden a workflow", or "write a gh batch/API script". Action: reads current YAML configs and outputs secure, SHA-pinned, least-privilege workflows. Not for committing/branching/opening a PR for an ordinary code change — that is `pr-workflow`.'
---

# gh-actions

Secure, high-performance CI/CD authoring and `gh` CLI automation. This skill is about the _content_ of workflows and batch scripts (hardening, OIDC, pagination), not shipping your day-to-day diff — to branch, commit, and open a PR for a reviewed change, use `pr-workflow`.

## Process Flow

```
Trigger: Workflow/CLI Request
  -- yml / CI --> Path A: ACTIONS
                    -> 1. Classify Intent
                    -> 2. Author & Harden (SHA-pinning/OIDC)
                    -> 3. Validate & Audit (lint/security review)
                         -- runtime fail ---> diagnose (handoff)
  -- gh / API --> Path B: CLI
                    -> 1. Mode Selection (inline vs script)
                    -> 2. Headless Standards (auth/paginate)
                    -> 3. Safety & Idempotency (snapshot/check existence)
                         -- script fail --> diagnose (handoff)
```

## STRICT SECURITY RULES

1. **Block Injections:** NEVER put `${{ github.event... }}` or inputs directly in `run:`. Always pass them through `env:`.
2. **Block Untrusted Code:** NEVER use `pull_request_target` to check out PR code.
3. **Block Permanent Keys:** NEVER save long-lived cloud keys as secrets. Use short-lived OIDC tokens.
4. **Block Secret Leaks:** NEVER use `secrets: inherit` unless you manually check every secret is needed.

## ROUTING

- **Path A (Actions):** For `.yml` workflows, CI, or releases.
- **Path B (CLI):** For `gh` scripts and API tasks.
- **Conceptual question** (not authoring/hardening): Read `references/topic-map.md` and follow its links to docs.github.com.
- _Rule:_ Run scripts from this skill folder. Example: `python3 "<skill_dir>/scripts/script.py path/to/file"`.

## PATH A: ACTIONS (YAML)

1. **Confirm Plan:** For multi-file or architecture-level requests (new pipeline, multi-cloud OIDC), ask the user to pick (1) recommended plan or (2) alternative plan. For a single-file or single-action fix, skip this and proceed directly.
2. **Read Required Files:** Read `references/workflow-recipes.md`. If deploying to cloud, also read `references/oidc-cloud.md`.
3. **Write Code:**
   - Pin all actions to exact SHA using `python3 scripts/pin_actions.py <path>`.
   - Set default permissions to `contents: read`.
   - Use OIDC (`id-token: write`).
4. **Validate:** Read `references/security-hardening.md`. Run `python3 scripts/lint.py <path>`.
5. **Audit:** Dispatch a `general-purpose` subagent with the full workflow YAML plus `references/security-hardening.md`, instructing it to return findings in the JSON shape defined in `references/schemas.md`. If `clean` is false, fix each finding and re-run step 4.

## PATH B: CLI (gh)

1. **Confirm Plan:** For multi-script or multi-repo requests, ask the user to pick (1) recommended plan or (2) alternative plan. For a single small script, skip this and proceed directly.
2. **Read Required Files:** Read `references/headless-auth-patterns.md` and `references/api-pagination-and-limits.md`.
3. **Write Script:**
   - Set `GH_PROMPT_DISABLED=1`.
   - Check login first: `gh auth status`.
   - Get clean data: Use `gh api --paginate --jq`.
   - Be safe: Save IDs before editing many things. Add pause times in loops.
   - Do not duplicate: Check if an item exists before creating it.

## SECURITY CHECKLIST (MANDATORY)

- [ ] `permissions` are explicitly set.
- [ ] Third-party actions are SHA-pinned.
- [ ] User inputs use `env:`, never `run:`.
- [ ] Uses OIDC instead of permanent cloud keys.
- [ ] `pull_request_target` is safe.

## NEXT STEPS & ERRORS

- **If anything fails:** Read `references/troubleshooting.md`.
- **Inspecting a failing PR check:** Run `python3 scripts/inspect_pr_checks.py --pr <n>` to fetch failing check logs and a failure snippet before deciding how to fix the workflow.
- **`diagnose`:** Call this if a script fails while running.
- **`verification-before-completion`:** Call this to double-check work before saving.
- **`pr-workflow`:** Call this to create a branch, commit, and open a PR.
- **`context-optimizer`:** Call this if the chat memory gets too full.
