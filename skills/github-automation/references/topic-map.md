# GitHub Actions docs topic map

For _conceptual_ questions where the live docs are the source of truth. For _authoring_, use `workflow-recipes.md`. For _hardening_, use `security-hardening.md`.

Verify against `docs.github.com` — URLs and section names move occasionally.

## Reference (the syntax-of-record pages)

- [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Contexts](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts) — `github.*`, `env.*`, `vars.*`, `secrets.*`, `inputs.*`, `needs.*`, etc.
- [Expressions](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions) — operators, functions like `fromJSON`, `hashFiles`, `toJSON`
- [Variables](https://docs.github.com/en/actions/reference/workflows-and-actions/variables) — default env vars, configuration vars
- [Metadata syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax) — `action.yml`
- [Reusing workflow configurations](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)
- [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [OpenID Connect reference](https://docs.github.com/en/actions/reference/security/oidc)

## Concepts (overview pages — start here for "what is X")

- [Understanding GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions)
- [Workflows](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows)
- [Custom actions](https://docs.github.com/en/actions/concepts/workflows-and-actions/custom-actions)
- [Deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments)
- [GitHub-hosted runners](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners)
- [Self-hosted runners](https://docs.github.com/en/actions/concepts/runners/self-hosted-runners)
- [Larger runners](https://docs.github.com/en/actions/concepts/runners/larger-runners)
- [Actions Runner Controller (ARC)](https://docs.github.com/en/actions/concepts/runners/actions-runner-controller)
- [Secrets](https://docs.github.com/en/actions/concepts/security/secrets)
- [`GITHUB_TOKEN`](https://docs.github.com/en/actions/concepts/security/github_token)
- [OpenID Connect](https://docs.github.com/en/actions/concepts/security/openid-connect)
- [Artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations)

## How-tos (the procedural pages)

- [Choosing the runner for a job](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job)
- [Running jobs in a container](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/run-jobs-in-a-container)
- [Using jobs in a workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs)
- [Job variations (matrix, conditional)](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations)
- [Passing information between jobs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/pass-job-outputs)
- [Reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [Configuring OIDC in AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
- [Using OIDC with reusable workflows](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows)
- [Using artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [Managing environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [Reviewing deployments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/review-deployments)
- [Enabling debug logging](https://docs.github.com/en/actions/how-tos/monitor-workflows/enable-debug-logging)
- [Troubleshooting workflows](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows)

## Tutorials and migration

- [Quickstart](https://docs.github.com/en/actions/get-started/quickstart)
- [Continuous integration](https://docs.github.com/en/actions/get-started/continuous-integration)
- [Continuous deployment](https://docs.github.com/en/actions/get-started/continuous-deployment)
- [Building and testing Node.js](https://docs.github.com/en/actions/tutorials/build-and-test-code/nodejs)
- [Migrating to GitHub Actions](https://docs.github.com/en/actions/tutorials/migrate-to-github-actions)
- [From Jenkins](https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/manual-migrations/migrate-from-jenkins)
- [From CircleCI](https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/manual-migrations/migrate-from-circleci)
- [From GitLab CI/CD](https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/manual-migrations/migrate-from-gitlab-cicd)
- [GitHub Actions Importer](https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/automated-migrations/use-github-actions-importer)

## When to leave this map and search live

Anything more specific than the above (a particular cloud's deploy steps, a particular language's setup action's options, a specific marketplace action) — search `docs.github.com` directly. This map is a routing aid, not a catalog.
