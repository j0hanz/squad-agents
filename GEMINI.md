# See [AGENTS.md](AGENTS.md)

---

## Semantic Skill Routing Protocol

Whenever a user requests a new task, or you transition between phases of work, you MUST evaluate available skills using a `<skill_evaluation>` block before calling `activate_skill`.

<skill_routing_protocol>
Inside `<skill_evaluation>`, you must answer:
1. [Intent Analysis]: What is the exact state of the project, and what is the core semantic intent of the user's request?
2. [Skill Matching]: Which skill from `<available_skills>` best aligns with this intent? (Evaluate the problem space, not just keywords).
3. [Overlap Resolution]: Are there competing skills? (e.g., `refactor` vs `architecture`). If so, state why the chosen skill is the most precise fit.
4. [Action]: State the name of the skill to be activated.
</skill_evaluation>
</skill_routing_protocol>

### Example

<example>
<skill_evaluation>
1. The user wants to "clean up" the database connection logic because it's messy. We already have tests.
2. The `refactor` skill handles cleaning up messy, hard-to-read code. `architecture` is for system-level boundary issues.
3. Since this is single-file complexity rather than a cross-service boundary issue, `refactor` is the precise fit.
4. Activating `refactor`.
</skill_evaluation>
</example>
