# OIDC for cloud deploys

OpenID Connect lets your workflow request a short-lived token from a cloud provider, signed by GitHub, scoped to a specific repo/branch/environment. **No long-lived cloud credentials in GitHub secrets.**

The setup is two-sided: a workflow side (small) and a cloud side (trust policy). The workflow side is similar across clouds; the cloud side differs.

## Subject claim format

GitHub signs the OIDC token with a `sub` claim that the cloud's trust policy matches against. The format depends on the workflow trigger:

| Trigger context           | `sub` value                                                                           |
| ------------------------- | ------------------------------------------------------------------------------------- |
| Workflow on a branch      | `repo:OWNER/REPO:ref:refs/heads/BRANCH`                                               |
| Workflow on a tag         | `repo:OWNER/REPO:ref:refs/tags/TAG`                                                   |
| Workflow on a PR          | `repo:OWNER/REPO:pull_request`                                                        |
| Workflow with environment | `repo:OWNER/REPO:environment:ENV_NAME`                                                |
| Reusable workflow         | `repo:OWNER/REPO:job_workflow_ref:OTHER_OWNER/OTHER_REPO/.github/workflows/X.yml@REF` |

**Use the most restrictive claim that works.** Scoping to `environment:production` is dramatically safer than scoping to the whole repo, because the GitHub environment can require human approval before the OIDC token is even minted.

You can customize the `sub` format per repo via the org/repo OIDC settings if you need to include `job_workflow_ref`, `runner_environment`, etc.

## Workflow side (universal)

```yaml
permissions:
  contents: read
  id-token: write # ALWAYS required for OIDC
```

`id-token: write` should be on the **job** that authenticates, not the whole workflow.

---

## AWS

### Workflow AWS

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4 # pin SHA in real use
        with:
          role-to-assume: arn:aws:iam::123456789012:role/gha-deployer-prod
          aws-region: us-east-1
      - run: aws sts get-caller-identity # sanity check
      - run: aws s3 sync ./dist s3://prod-bucket --delete
```

### IAM side

**1. Create the OIDC provider** (once per AWS account):

- URL: `https://token.actions.githubusercontent.com`
- Audience: `sts.amazonaws.com`
- Thumbprint: AWS now fetches this automatically — leave the field as documented.

**2. Create an IAM role** with a trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:my-org/my-repo:environment:production"
        }
      }
    }
  ]
}
```

The role's permission policy is whatever the deploy needs (S3 access, ECS update, etc.) — keep it tight.

**Common mistake:** using `StringEquals` on `:sub` with a wildcard — `StringEquals` is literal, wildcards need `StringLike`.

---

## GCP

### Workflow GCP

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - id: auth
        uses: google-github-actions/auth@v2 # pin SHA
        with:
          workload_identity_provider: projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
          service_account: gha-deployer@my-project.iam.gserviceaccount.com
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud run deploy my-svc --image gcr.io/my-project/my-svc:${{ github.sha }}
```

### GCP side

**1. Create a Workload Identity Pool and Provider:**

```bash
gcloud iam workload-identity-pools create github-pool \
  --location=global --display-name="GitHub Actions pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global --workload-identity-pool=github-pool \
  --display-name="GitHub Actions provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.environment=assertion.environment" \
  --attribute-condition="assertion.repository=='my-org/my-repo'"
```

`attribute-condition` is the critical lockdown — without it, _any_ GitHub repo's OIDC token would be accepted by the pool.

**2. Bind a service account:**

```bash
gcloud iam service-accounts add-iam-policy-binding gha-deployer@my-project.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/123456789/locations/global/workloadIdentityPools/github-pool/attribute.repository/my-org/my-repo"
```

For per-environment scoping, use `attribute.environment/production` instead of (or in addition to) `attribute.repository`.

---

## Azure

### Workflow

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2 # pin SHA
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - run: az webapp deploy --resource-group prod-rg --name my-app --src-path dist.zip
```

Note: `client-id`, `tenant-id`, `subscription-id` go in **vars**, not secrets. They're identifiers, not credentials.

### Azure side

**1. Register an app** (Azure AD) and grant it the RBAC roles your deploy needs.

**2. Add a federated credential** to the app:

- Issuer: `https://token.actions.githubusercontent.com`
- Subject (entity type "Environment"): `repo:my-org/my-repo:environment:production`
- Audience: `api://AzureADTokenExchange`

Different entity types correspond to different `sub` formats — branch, tag, PR, environment. You can add multiple federated credentials per app (one per environment, for example).

---

## Other targets that support OIDC

- **HashiCorp Vault** — exchange the GitHub OIDC token via the JWT auth method.
- **npm** — "trusted publisher" supports OIDC since 2024; configure on npmjs.com and use `npm publish --provenance`.
- **PyPI** — trusted publisher via `pypa/gh-action-pypi-publish` with `id-token: write`.
- **Crates.io** — trusted publishing via `rust-lang/crates-io-auth-action`.

For any of these, the workflow side is the same `id-token: write` + a vendor action; the registry side is configured on the registry's UI by adding the repo + workflow path as a trusted publisher.

## Verifying OIDC works

After setting it up, run the workflow once and check:

1. `configure-aws-credentials` (or equivalent) step succeeds.
2. The next step (`aws sts get-caller-identity`, `gcloud auth list`, `az account show`) shows the federated identity.
3. Try a job from a non-matching branch/environment — it should fail to assume the role. If it succeeds, your trust policy is too permissive.
