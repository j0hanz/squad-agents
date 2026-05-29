import { createPostToolUseFailure } from '../utils.mjs';

const NUDGE =
  '\n> **Diagnose Hook:** A Bash command failed. Before retrying, invoke the `diagnose` skill to map the root cause — do not blindly retry.\n';

export async function nudge(_input) {
  return createPostToolUseFailure(NUDGE);
}
