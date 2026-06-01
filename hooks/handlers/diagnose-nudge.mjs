// PostToolUseFailure(Bash) handler — when a shell command fails, inject the
// structured-debugging skill as context alongside a trimmed error excerpt, so
// the agent reaches for a methodology instead of blind retries. Additive only:
// uses additionalContext, never blocks, fires only on repeated failures to avoid
// noise on one-off typos.

import { appendJsonl, readJsonlTail } from '../utils.mjs';

const STATE = '.claude/state/diagnose-nudge.jsonl';
const THRESHOLD = 2; // nudge once this many Bash failures pile up in a session

function errorExcerpt(input) {
  const r = input.tool_response;
  const text = typeof r === 'string' ? r : r?.stderr || r?.error || r?.output || '';
  return String(text).split('\n').filter(Boolean).slice(0, 3).join(' ⏎ ').slice(0, 240);
}

/** PostToolUseFailure: nudge toward the diagnose skill after repeated failures. */
export function onFailure(input = {}) {
  if (input.tool_name !== 'Bash') return null;

  const session = input.session_id || 'unknown';
  appendJsonl(STATE, { ts: new Date().toISOString(), session });

  const sessionFailures = readJsonlTail(STATE, 200).filter((r) => r.session === session);
  const failureCount = sessionFailures.length;
  if (failureCount !== THRESHOLD) return null; // exactly at threshold → nudge once

  const excerpt = errorExcerpt(input);
  const msg =
    'Multiple Bash failures this session. Consider the `diagnose` skill — ' +
    'reproduce → isolate → hypothesize → fix, rather than retrying variants.';
  return excerpt ? `${msg}\nLast error: ${excerpt}` : msg;
}
