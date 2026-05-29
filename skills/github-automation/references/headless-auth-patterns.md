# Headless Authentication Patterns

When executing `gh` in headless environments (CI/CD, cron jobs, Kubernetes), interactive `gh auth login` is impossible.

## The GitHub App Token Pattern

For organization-level automation, PATs are a security risk (tied to a human, overly broad scopes). Use a GitHub App to generate a short-lived token.

**1. Generate a JWT and Exchange for Installation Token**
Instead of using raw `curl`, use a dedicated action (like `actions/create-github-app-token`) in Actions, or securely generate it in your script.

**2. Inject via `GH_TOKEN`**
`gh` automatically authenticates if `GH_TOKEN` is present in the environment.

```bash
export GH_TOKEN="ghs_your_short_lived_installation_token"
# Now gh operates as the App installation
gh api /installation/repositories
```

## Cross-Repo Access in GitHub Actions

By default, the `GITHUB_TOKEN` provided to a GitHub Action only has access to the _current_ repository.
If your `gh` script needs to modify another repo:

**NEVER try to use the default `GITHUB_TOKEN`.**
**INSTEAD:**

1. Create a fine-grained PAT or GitHub App token with access to the target repo.
2. Store it in GitHub Secrets.
3. Expose it to the step explicitly:

```yaml
- name: Cross-repo PR automation
  env:
    GH_TOKEN: ${{ secrets.CROSS_REPO_APP_TOKEN }}
  run: |
    gh pr create --repo target-org/target-repo --title "Automated update"
```
