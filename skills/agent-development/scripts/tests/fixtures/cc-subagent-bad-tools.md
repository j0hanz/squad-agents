---
name: bad-subagent
description: Example CC subagent with malformed tools. Use this agent when you need to explore code.
model: claude-sonnet-4-6
tools:
  - Read
  - name: Glob
    permission: always_ask
---

# Bad Tools

This is a CC subagent with tools defined as a mix of strings and objects, which is invalid.
