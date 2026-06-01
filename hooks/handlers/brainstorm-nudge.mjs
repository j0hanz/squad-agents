// UserPromptSubmit handler — when a prompt looks like the start of a build with
// no design done yet, inject a single gentle pointer to the brainstorming skill.
// Additive only: it adds one line of context, never erases the prompt, fires at
// most once per session, and honors the `brainstorm_nudge` plugin config.

import { appendJsonl, readJsonlTail } from '../utils.mjs';

const STATE = '.claude/state/brainstorm-nudge.jsonl';

// "Start a build" intent: an imperative verb aimed at a unit of work.
const INTENT =
  /\b(build|implement|create|add|develop|design|scaffold|write)\b[\s\S]{0,60}\b(feature|component|module|endpoint|api|app|system|service|class|tool|command|hook|skill|agent|page|screen|integration|workflow|pipeline)\b/i;

// Signals the user is already past discovery — don't nudge.
const ALREADY =
  /\b(brainstorm|spec|specs|plan|requirements?|design doc|already (designed|planned|scoped))\b/i;

function enabled() {
  return process.env.AGENT_DEV_BRAINSTORM_NUDGE !== '0';
}

/** UserPromptSubmit: optionally inject a one-line brainstorm nudge. */
export function nudge(input = {}) {
  if (!enabled()) return null;

  const prompt = (input.prompt || '').trim();
  if (!prompt || prompt.startsWith('/')) return null; // skip slash commands
  if (!INTENT.test(prompt) || ALREADY.test(prompt)) return null;

  const session = input.session_id || 'unknown';
  const already = readJsonlTail(STATE, 50).some((r) => r.session && r.session === session);
  if (already) return null; // once per session

  appendJsonl(STATE, { ts: new Date().toISOString(), session });

  return (
    'Note: this looks like a new build. Consider a quick `brainstorming` pass ' +
    '(requirements + design) before implementing — it catches ambiguity early. ' +
    'Skip if the design is already clear.'
  );
}
