import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const tmpDir = mkdtempSync(path.join(os.tmpdir(), 'runner-test-'));
process.env.CLAUDE_PROJECT_DIR = tmpDir;

// We'll run the actual runner.mjs script via execSync to test its process behavior
const runnerPath = path.resolve('hooks/runner.mjs');

test('runner: succeeds for valid handler and action', () => {
  // session.start should work and return JSON
  const result = execSync(`node ${runnerPath} session env`, {
    encoding: 'utf-8',
    env: { ...process.env, CLAUDE_PROJECT_DIR: tmpDir },
  });

  if (result.trim()) {
    assert.doesNotThrow(() => JSON.parse(result));
  }
});

test('runner: fails gracefully for unknown handler', () => {
  const result = execSync(`node ${runnerPath} unknown_domain action`, {
    encoding: 'utf-8',
    env: { ...process.env, CLAUDE_PROJECT_DIR: tmpDir },
  });
  assert.strictEqual(result.trim(), '');
});

test('runner: fails gracefully for unknown action', () => {
  const result = execSync(`node ${runnerPath} session unknown_action`, {
    encoding: 'utf-8',
    env: { ...process.env, CLAUDE_PROJECT_DIR: tmpDir },
  });
  assert.strictEqual(result.trim(), '');
});
