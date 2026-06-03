# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-03

### Added

- **Skills (14):** `architecture`, `brainstorming`, `code-review`, `create-agent`, `create-hook`, `diagnose`, `github-automation`, `planning`, `refactor`, `skill-builder`, `test-driven-development`, `using-agent-dev-skills`, `verification-before-completion`, `agents-maintainer`
- **Agents (4):** `coder` (autonomous executor with worktree isolation), `detective` (read-only debugging specialist), `documenter` (documentation maintainer), `explorer` (research-focused, read-only)
- **Hooks (7 lifecycle events):** `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `SessionEnd`
- **MCP server:** context7 HTTP integration for live library documentation
- **Monitors (experimental):** live telemetry watcher, Node.js test watcher (on `create-hook`), Python test watcher (on `skill-builder`)
- Comprehensive unit and integration test suite (`node --test`, `pytest`)
- Plugin validation script (`npm run validate`)
- Marketplace manifest for one-command installation

[1.0.0]: https://github.com/j0hanz/claude-agent-dev-plugin/releases/tag/v1.0.0
