import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { onFailure } from './diagnose-nudge.mjs';

const ORIGINAL = process.env.CLAUDE_PROJECT_DIR;

function freshProject() {
  const dir = mkdtempSync(join(tmpdir(), 'agentdev-diagnose-'));
  process.env.CLAUDE_PROJECT_DIR = dir;
  return dir;
}

test.afterEach(() => {
  if (ORIGINAL === undefined) delete process.env.CLAUDE_PROJECT_DIR;
  else process.env.CLAUDE_PROJECT_DIR = ORIGINAL;
});

test('onFailure() returns null for non-Bash tool failures', () => {
  freshProject();
  assert.equal(onFailure({ tool_name: 'Read', session_id: 'sess-read' }), null);
  assert.equal(onFailure({ tool_name: 'Edit', session_id: 'sess-edit' }), null);
});

test('onFailure() returns null on the first Bash failure', () => {
  freshProject();
  const result = onFailure({ tool_name: 'Bash', session_id: 'sess-first' });
  assert.equal(result, null);
});

// THRESHOLD=2: nudge fires when failure count reaches exactly 2 (the second failure).
test('onFailure() nudges on the second Bash failure (at threshold)', () => {
  freshProject();
  const session = 'sess-second';
  onFailure({ tool_name: 'Bash', session_id: session }); // count 1 — silent
  const result = onFailure({ tool_name: 'Bash', session_id: session }); // count 2 — nudge
  assert.ok(result, 'expected a nudge on the second failure');
  assert.match(result, /diagnose/);
});

test('onFailure() does not nudge again after the threshold', () => {
  freshProject();
  const session = 'sess-after';
  onFailure({ tool_name: 'Bash', session_id: session }); // count 1
  onFailure({ tool_name: 'Bash', session_id: session }); // count 2 — nudge fires
  const third = onFailure({ tool_name: 'Bash', session_id: session }); // count 3 — silent
  assert.equal(third, null, 'should not nudge again past threshold');
});

test('onFailure() includes the error excerpt in the nudge message', () => {
  freshProject();
  const session = 'sess-excerpt';
  onFailure({ tool_name: 'Bash', session_id: session }); // count 1
  const result = onFailure({
    tool_name: 'Bash',
    session_id: session,
    tool_response: { stderr: 'command not found: npm\ncheck your PATH' },
  }); // count 2 — nudge
  assert.ok(result, 'expected a nudge');
  assert.match(result, /command not found/);
});

test('onFailure() nudges without crashing when tool_response is absent', () => {
  freshProject();
  const session = 'sess-noerr';
  onFailure({ tool_name: 'Bash', session_id: session }); // count 1
  const result = onFailure({ tool_name: 'Bash', session_id: session }); // count 2 — nudge
  assert.ok(result, 'nudge should still fire without error detail');
  assert.match(result, /diagnose/);
});

test('onFailure() counts failures beyond the last 50 entries', async () => {
  const dir = freshProject();
  const session = 'sess-beyond-tail';
  const STATE = join(dir, '.claude/state/diagnose-nudge.jsonl');
  const fs = await import('node:fs');
  const { mkdirSync, appendFileSync } = fs;
  mkdirSync(join(dir, '.claude/state'), { recursive: true });

  // Fill state with 200 irrelevant entries
  for (let i = 0; i < 200; i++) {
    appendFileSync(
      STATE,
      JSON.stringify({ ts: new Date().toISOString(), session: 'irrelevant' }) + '\n',
    );
  }

  // Add one failure for our session (now at position 201 from end)
  appendFileSync(STATE, JSON.stringify({ ts: new Date().toISOString(), session: session }) + '\n');

  // Add 10 more irrelevant entries (failure is now at position 11 from end relative to the 10, but total > 50)
  for (let i = 0; i < 10; i++) {
    appendFileSync(
      STATE,
      JSON.stringify({ ts: new Date().toISOString(), session: 'irrelevant' }) + '\n',
    );
  }

  // Call onFailure which should record 2nd failure for this session and nudge
  const result = onFailure({ tool_name: 'Bash', session_id: session });
  assert.ok(result, 'should nudge even if first failure was > 50 entries ago');
});
