# Error Recovery Playbook

## Skill fails to load

**Symptoms**: Plugin validation fails or skill doesn't activate.

**Recovery**:

1. Run `npm validate` and check output for SKILL.md issues
2. Verify frontmatter: name must be kebab-case, description has no angle brackets
3. Check for table formatting errors (missing pipes, misaligned columns)

---

## /pr fails

**Symptoms**: PR creation fails when running `/pr`.

**Recovery**:

1. Check `npm validate` output first — fix all plugin health issues
2. Run `npm test` — fix any test failures
3. Ensure all changes are committed locally
4. Re-invoke `/pr` — it is safe to run multiple times
5. If git errors occur: resolve manually (merge conflicts, branch issues), then re-run

---

## Subagent times out

**Symptoms**: Coder, detective, or documenter agent stops responding.

**Recovery**:

1. Re-invoke with a narrower scope (single file, specific function)
2. Provide concrete file paths and function names in the prompt
3. Break large tasks into smaller focused subtasks
4. Check system resources (disk space, memory) if timeouts persist

---

## Tests fail in Validate phase

**Symptoms**: `npm test` exits with non-zero code.

**Recovery**:

1. Do NOT skip to Ship phase
2. Loop back to Build phase
3. Fix the failing test (implementation or test code)
4. Re-run tests until all pass
5. Proceed to Ship only after `npm test` exits 0

---

## Design approval stalls

**Symptoms**: User doesn't confirm design is acceptable.

**Recovery**:

1. Ask explicitly: "Is the Design Table above correct?"
2. Wait for explicit confirmation: "Approved", "LGTM", "Good", "Proceed"
3. If objections: address concerns and show revised Design Table
4. Do NOT proceed to Plan/Build without approval

---

## Skill output is confusing

**Symptoms**: Skill's guidance is unclear or doesn't match the task.

**Recovery**:

1. Ask: "What does [specific output line] mean?"
2. Check the skill's documentation file: `skills/<name>/SKILL.md`
3. Review worked examples in the skill's references/ folder
4. If the skill truly doesn't apply: use a different skill or proceed directly
