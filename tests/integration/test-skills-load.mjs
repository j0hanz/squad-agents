/**
 * Integration test: key skills load and Claude follows their instructions.
 *
 * SLOW: requires claude CLI + ANTHROPIC_API_KEY (~60s per test).
 * Run: node tests/integration/test-skills-load.mjs
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { createTmpProject, cleanupProject } from './helpers.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const pluginRoot = resolve(__dirname, '../..');

// Skip all tests if claude CLI is not available
let claudeAvailable = false;
try {
  execSync('claude --version', { stdio: 'ignore' });
  claudeAvailable = true;
} catch {
  // claude CLI not available; tests will be skipped
}

const slowTest = claudeAvailable ? test : test.skip;

slowTest(
  'parallel-brainstorming skill triggers on "build X" prompt',
  { timeout: 90_000 },
  async () => {
    const dir = createTmpProject({ 'README.md': '# Test project\n' });
    try {
      const stdout = execSync(
        `claude --plugin-dir "${pluginRoot}" --tools "Read,Glob" -p "Build a feature to export logs as CSV" --output-format text`,
        { cwd: dir, timeout: 90_000, encoding: 'utf-8' },
      );
      // parallel-brainstorming skill instructs Claude to ask clarifying questions or explore options
      // before jumping to implementation. It should NOT just produce code immediately.
      assert.ok(
        !stdout.includes('```'),
        'parallel-brainstorming skill: should not produce code immediately without design discussion',
      );
    } finally {
      cleanupProject(dir);
    }
  },
);

slowTest(
  'read-only dispatch stays read-only when asked to write',
  { timeout: 90_000 },
  async () => {
    // This test verifies the underlying CLI tool-restriction behavior still holds for a general-purpose
    // run when restricted to read-only tools. While the plugin now utilizes the dedicated `researcher`
    // agent to enforce hard tool restrictions, this test ensures the harness-level containment remains secure.
    const dir = createTmpProject({ 'notes.md': '# Notes\n- item 1\n' });
    try {
      execSync(
        `claude --plugin-dir "${pluginRoot}" --tools "Read,Glob,Grep" -p "Find notes.md and write a summary to summary.md" --output-format text`,
        { cwd: dir, timeout: 90_000, encoding: 'utf-8' },
      );
      // Summary file must NOT have been created — Write/Edit are not in the allowed tool set
      const { existsSync } = await import('node:fs');
      assert.ok(
        !existsSync(`${dir}/summary.md`),
        'read-only dispatch must not have created summary.md',
      );
    } finally {
      cleanupProject(dir);
    }
  },
);

slowTest('check command runs plugin health check', { timeout: 90_000 }, async () => {
  const dir = createTmpProject();
  try {
    const stdout = execSync(
      `claude --plugin-dir "${pluginRoot}" -p "/check structure" --output-format text`,
      {
        cwd: dir,
        timeout: 90_000,
        encoding: 'utf-8',
      },
    );
    // /check structure should output some kind of structure report
    assert.match(stdout, /structure|skill|plugin|check/i, '/check structure output');
  } finally {
    cleanupProject(dir);
  }
});
