# Terminology Glossary

| Term                 | Definition                                                                                                           |
| -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Skill**            | A methodology file (`SKILL.md`) loaded on demand that guides HOW to approach a specific task.                        |
| **Managed agent**    | A scoped subagent with defined tools, a system prompt, and isolated context. Used for delegated autonomous work.     |
| **Subagent**         | Another name for managed agent when dispatched for a specific task.                                                  |
| **Command**          | A slash command (`/plan`, `/deliver`, etc.) that triggers a skill or workflow.                                       |
| **Hook**             | An automatic event listener that fires on lifecycle events (e.g., PostToolUse Write). You do not invoke hooks.       |
| **Component**        | The specific artifact being built: a skill, agent, command, hook, or documentation file.                             |
| **Design phase**     | The phase where you produce a Design Table (component, trigger, approach) and get user approval before writing code. |
| **Isolated context** | Managed agents receive a fresh context window — they have no access to the parent session history.                   |
