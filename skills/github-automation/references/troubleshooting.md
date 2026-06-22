# Troubleshooting workflows

The 12 things that go wrong most often, ordered roughly by frequency. Each entry: symptom → cause → fix.

## 1. "My workflow isn't triggering"

**Symptom:** Pushed/PRed and nothing happens. No run shows up in the Actions tab.

**Common causes:**

- **Workflow file is on a branch that isn't the default branch** (for `schedule`, `workflow_dispatch`, and `repository_dispatch` triggers). These triggers only fire from the default branch's copy of the workflow. Fix: merge to default.
- **YAML invalid.** GitHub silently disables workflows with parse errors. Check the Actions tab → "Disabled" filter, or run the linter (`scripts/lint.py`).
- **Branch filter excludes the branch.** `on.push.branches: [main]` won't fire from `feature/foo`. Either remove the filter or push to `main`.
- **`paths:` or `paths-ignore:` filter excludes the changed files.** Check what files the push actually changed.
- **`if:` on the job evaluated false.** Look at the workflow run (it does show up) — the job will be skipped with a yellow icon and you can see why.
- **Forked PRs from first-time contributors** require maintainer approval (org/repo setting).
- **Scheduled workflow on a repo with 60+ days of inactivity** is automatically disabled.

## 2. "Permission denied" on `GITHUB_TOKEN`

**Symptom:** Step that tries to push, comment, or upload fails with HTTP 403 or "Resource not accessible by integration."

**Cause:** Default `GITHUB_TOKEN` permissions don't include what the step needs (most likely `contents: write` or `pull-requests: write`).

**Fix:** Add the scope explicitly at the job level. See `security-hardening.md` § 1 for which scope each operation needs.

**Footgun:** Job-level `permissions:` _replaces_ workflow-level, doesn't merge. If you add `id-token: write` at job level you may lose your `contents: read`.

## 3. Expression evaluates to empty / `null` / unexpected value

**Symptom:** `${{ steps.foo.outputs.bar }}` is empty in a later step.

**Common causes:**

- **Output not set correctly.** Must use `echo "name=value" >> "$GITHUB_OUTPUT"` (or `>> $env:GITHUB_OUTPUT` on PowerShell). Setting `::set-output::` is deprecated and silently no-ops on some runners.
- **Step `id:` missing.** `steps.foo.outputs.bar` requires `id: foo` on that step.
- **Output is from a different job.** Cross-job outputs require declaring them in `jobs.<id>.outputs:` and consuming via `needs.<id>.outputs.<name>`.
- **Reading `env:` in `if:` at job level.** `env:` defined at job level isn't visible in the job's `if:` (chicken-and-egg). Use `vars.` or move the value to workflow-level `env:`.
- **`${{ env.FOO }}` inside `env:` itself.** Doesn't work — `env` doesn't see itself during its own evaluation.

## 4. Cache hits but the dependency is stale

**Symptom:** `actions/cache` reports hit but tests fail because a transitive dep changed.

**Cause:** Cache key is too coarse (e.g., `key: deps-${{ runner.os }}` with no lockfile hash).

**Fix:**

```yaml
key: deps-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
restore-keys: |
  deps-${{ runner.os }}-
```

`restore-keys` lets you fall back to a partial match (still useful), while `key` only writes on a clean miss.

For `setup-node`/`setup-python`/`setup-go`, prefer the built-in `cache:` option — it handles the key correctly.

## 5. Self-hosted runner runs as root / leaks between jobs

**Symptom:** Subsequent jobs see files / env vars from a previous run.

**Cause:** Self-hosted runners are persistent VMs by default. State carries over.

**Fix:**

- For untrusted workloads, **never** use a persistent self-hosted runner. Use ephemeral runners (ARC, or `--ephemeral` flag).
- Clean up explicitly: `runs-on:` step that `git clean -ffdx` before checkout.
- Don't run self-hosted runners on public repos. Use GitHub-hosted or ARC with ephemeral pods.

## 6. Composite action: "must specify shell"

**Symptom:** Composite action fails to run with `Error: Required property is missing: shell`.

**Cause:** Every `run:` step inside a composite action must declare `shell:`. There's no default.

**Fix:**

```yaml
- shell: bash
  run: echo hello
```

(On Windows runners, use `shell: pwsh` or `shell: powershell`.)

## 7. Matrix expansion produces no jobs

**Symptom:** Job declared with `strategy.matrix` shows "skipped" with no children.

**Cause:** Dynamic matrix from `fromJSON(...)` evaluated to `[]` or invalid JSON.

**Fix:**

- Gate the job with `if: needs.detect.outputs.packages != '[]'`.
- Echo the matrix value in the producing step to inspect it: `echo "matrix is: $MATRIX"`.

## 8. Secret is empty inside `run:`

**Symptom:** `echo "$MY_SECRET"` prints `***` (masked) or empty.

**Likely causes:**

- **`\***`printed:** the secret IS set, it's masked in logs. The step actually receives the value. Test with`[[-n "$MY_SECRET"]] && echo "set"`.
- **Empty:** secret not exposed to this job. Reusable workflows must declare `secrets:` on `workflow_call`. PRs from forks don't get repo secrets. Environment-scoped secrets aren't visible to jobs that don't use `environment:`.

## 9. `pull_request` from a fork can't read secrets — but it should be able to comment

**Symptom:** Linter or commenter runs in PR from a fork, fails to post.

**Cause:** Fork PRs deliberately get a read-only `GITHUB_TOKEN` and no secrets. This is by design.

**Fix:** Split into two workflows. The PR workflow builds and uploads an artifact; a separate `workflow_run`-triggered workflow runs in the base repo's context and posts the comment using the artifact. See `security-hardening.md` § 4.

## 10. Action uses old Node and prints deprecation warnings

**Symptom:** Workflow runs successfully but logs warn `Node 16 actions are deprecated`.

**Cause:** A third-party action's `action.yml` declares `using: 'node16'`.

**Fix:** Update to a newer version of the action. If none exists, file an issue upstream or fork. Eventually GitHub disables old Node versions and the action will hard-fail.

## 11. `actions/checkout` doesn't fetch tags or full history

**Symptom:** Steps that use `git describe`, `git log`, or compute version from tags fail or return wrong values.

**Cause:** `actions/checkout` defaults to shallow clone (depth 1) and doesn't fetch tags.

**Fix:**

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0 # full history
    fetch-tags: true # also tags (combine with fetch-depth: 0 for safety)
```

## 12. Workflow file changes don't take effect on a PR

**Symptom:** Edited the workflow on a branch, but the PR's checks still use the old version.

**Cause:** For most events (`push`, `pull_request`), the workflow file is taken from the branch/SHA that triggered the event. _Should_ update on next push. But for `workflow_run`, `schedule`, `repository_dispatch`, only the default branch's copy is used.

**Fix:** For testing those triggers, merge to default branch (or a special test branch you treat as default temporarily).

---

## Debug logging

When the symptom is "I have no idea what's happening", turn on debug logs:

1. Set repo secret `ACTIONS_RUNNER_DEBUG=true` for runner-level debug.
2. Set repo secret `ACTIONS_STEP_DEBUG=true` for step-level debug (expression evaluation, etc.).
3. Re-run the workflow with "Enable debug logging" checked from the UI.

Step-level debug is the more useful of the two — it shows what `${{ }}` expressions actually resolved to.

## When to escalate to `gh-fix-ci`

This skill is for designing and authoring workflows. If the user has a _specific failing run_ they want triaged from its logs, hand off — `gh-fix-ci` is built for that interaction loop (`gh run view`, log fetching, narrowing to a failing step). This skill's troubleshooting section is for design-time fixes you can spot from the workflow file alone.
