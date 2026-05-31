import { test } from 'node:test';
import assert from 'node:assert/strict';
import { announce } from './skills.mjs';

const KEY = 'AGENT_DEV_SKILLS_ANNOUNCE';
const ORIGINAL = process.env[KEY];

test.afterEach(() => {
  if (ORIGINAL === undefined) delete process.env[KEY];
  else process.env[KEY] = ORIGINAL;
});

test('announce() injects the full routing guide with frontmatter stripped', () => {
  delete process.env[KEY];
  const out = announce();
  assert.ok(out, 'expected routing-guide context');
  assert.match(out, /Skill Routing Map/);
  assert.match(out, /invoke it with the Skill tool/);
  // Reaches the end of the guide — proves the body wasn't truncated.
  assert.match(out, /If You're Stuck/);
  // Frontmatter must be gone — no YAML keys, no leading delimiter.
  assert.doesNotMatch(out, /^---/);
  assert.doesNotMatch(out, /name: using-agent-dev/);
});

test('announce() respects the disable flag', () => {
  process.env[KEY] = '0';
  assert.equal(announce(), null);
});

test('announce() output stays under the injection cap', () => {
  delete process.env[KEY];
  assert.ok(announce().length <= 10000);
});
