# API Pagination and Rate Limits

GitHub imposes strict limits: 5,000 requests per hour for authenticated users, but more critically, **Secondary Rate Limits** (abuse mechanisms) trigger if you make concurrent mutations too quickly.

## The `--paginate` Primitive

Do not write `while` loops checking for the `Link: <next>` header. `gh api` does this internally.

```bash
# Fetches ALL open PRs across all pages, combining them into a single JSON array
gh api graphql --paginate -f query='
  query($endCursor: String) {
    repository(owner: "owner", name: "repo") {
      pullRequests(states: OPEN, first: 100, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { number title }
      }
    }
  }
'
```

## Beating Secondary Rate Limits

When executing batch mutations (e.g., closing 500 stale issues), a tight `xargs -P 10` loop will trigger a 403 Secondary Rate Limit.

**The Batching Pattern:**
Always introduce intentional jitter or batching when mutating via the API.

```bash
# Get 500 issue IDs
gh api repos/:owner/:repo/issues --paginate --jq '.[].number' > issues.txt

# Process safely with a 1-second delay between mutations
cat issues.txt | while read issue; do
  gh api -X PATCH repos/:owner/:repo/issues/$issue -f state="closed"
  sleep 1
done
```

**GraphQL Mutations for Batching:**
If possible, use GraphQL aliases to batch up to 100 mutations in a single API call, bypassing the 1-second per-mutation delay entirely.
