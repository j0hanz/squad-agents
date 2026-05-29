# Documentation Lookup

Retrieves and queries up-to-date documentation and code examples from Context7 for any programming library or framework. Two-step workflow: resolve the library name to get its ID, then query docs using that ID.

If the user already provided a library ID in `/org/project` or `/org/project/version` format, use it directly.

**Important:** always use the user’s full intent as the query. Do not reduce the question to a single keyword.

## Step 1: Resolve a Library

Resolves a package/product name to a Context7-compatible library ID and returns matching libraries.

**Via CLI:**

```bash
ctx7 library react "How to clean up useEffect with async operations"
ctx7 library nextjs "How to set up app router with middleware"
```

**Via MCP:**
Call `mcp__context7__resolve-library-id` with `libraryName` and `query`.

Always pass a `query` argument — it is required and directly affects result ranking. Use the user's intent to form the query. Do not include any sensitive or confidential information in your query.

### Result fields

Each result includes:

- **Library ID** — Context7-compatible identifier (format: `/org/project`)
- **Name** — Library or package name
- **Description** — Short summary
- **Code Snippets** — Number of available code examples
- **Source Reputation** — Authority indicator (High, Medium, Low, or Unknown)
- **Benchmark Score** — Quality indicator (100 is the highest score)
- **Versions** — List of versions if available (e.g., `/org/project/version`)

### Selection process

1. Analyze the query to understand what library/package the user is looking for
2. Select the most relevant match based on:
   - Name similarity to the query
   - Documentation coverage (higher Code Snippets)
   - Source reputation (High or Medium)
   - Benchmark score (higher is better)
3. If multiple good matches exist, acknowledge this but proceed with the most relevant one
4. If no good matches exist, clearly state this and suggest query refinements

IMPORTANT: Do not attempt to resolve a library more than 3 times per question.

### Version-specific IDs

If the user mentions a specific version, use a version-specific library ID:
`/vercel/next.js/v14.3.0-canary.87`

## Step 2: Query Documentation

Retrieves up-to-date documentation and code examples for the resolved library.

**Via CLI:**

```bash
ctx7 docs /facebook/react "How to clean up useEffect with async operations"
```

**Via MCP:**
Call `mcp__context7__query-docs` with `libraryId` and `query`.

IMPORTANT: Do not query docs more than 3 times per question.

## Authentication & Errors (CLI)

For higher rate limits:

```bash
export CONTEXT7_API_KEY=your_key
# OR
ctx7 login
```

If a quota error occurs, inform the user and suggest they authenticate using `ctx7 login`. Do not silently fall back to training data without telling the user why Context7 was not used.

## See Also

- **[Setup Guide](setup.md)** — Configure authentication and MCP/CLI mode
- **[Main Skill](../SKILL.md)** — Full workflow overview and error recovery examples
