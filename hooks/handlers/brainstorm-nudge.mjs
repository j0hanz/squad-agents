// Non-blocking UserPromptSubmit hook: detects implementation intent and
// reminds the user to run brainstorming before implementing.
// Never blocks — output is advisory context only.

const IMPL_PATTERNS = [
  /\b(implement|build|create|add|write|develop|make|scaffold)\b/i,
  /\bnew\s+(feature|component|module|function|class|service|endpoint|api|hook|skill|agent)\b/i,
];

export async function nudge(input) {
  const prompt = input?.prompt || '';
  if (!IMPL_PATTERNS.some((p) => p.test(prompt))) return null;

  return {
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext:
        '> **Reminder:** Have you run the **brainstorming** skill to clarify intent and design before implementing? If you already have — ignore this.',
    },
  };
}
