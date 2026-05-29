/**
 * Integration test: key skills load and Claude follows their instructions.
 *
 * SLOW: requires claude CLI + ANTHROPIC_API_KEY (~60s per test).
 * Run: node tests/integration/test-skills-load.mjs
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import { assertContains, assertNotContains, createTmpProject, cleanupProject } from './helpers.mjs';

// Skip all tests if claude CLI is not available
let claudeAvailable = false;
try {
  execSync('claude --version', { stdio: 'ignore' });
  claudeAvailable = true;
} catch {
  // claude CLI not available; tests will be skipped
}

const slowTest = claudeAvailable ? test : test.skip;

slowTest('brainstorming skill triggers on "build X" prompt', { timeout: 90_000 }, async () => {
  const dir = createTmpProject({ 'README.md': '# Test project\n' });
  try {
    const stdout = execSync(
      `claude -p "Build a feature to export logs as CSV" --allowedTools "Read,Glob" --output-format text`,
      { cwd: dir, timeout: 90_000, encoding: 'utf-8' },
    );
    // Brainstorming skill instructs Claude to ask clarifying questions or explore options
    // before jumping to implementation. It should NOT just produce code immediately.
    assertNotContains(
      stdout,
      '```',
      'brainstorming skill: should not produce code immediately without design discussion',
    );
  } finally {
    cleanupProject(dir);
  }
});

slowTest('explorer agent stays read-only when asked to write', { timeout: 90_000 }, async () => {
  const dir = createTmpProject({ 'notes.md': '# Notes\n- item 1\n' });
  try {
    execSync(
      `claude -p "Use the explorer agent to find notes.md and write a summary to summary.md" --output-format text`,
      { cwd: dir, timeout: 90_000, encoding: 'utf-8' },
    );
    // Summary file must NOT have been created — explorer is read-only
    const { existsSync } = await import('node:fs');
    assert.ok(!existsSync(`${dir}/summary.md`), 'explorer must not have created summary.md');
  } finally {
    cleanupProject(dir);
  }
});

slowTest('check command runs plugin health check', { timeout: 90_000 }, async () => {
  const dir = createTmpProject();
  try {
    const stdout = execSync(`claude -p "/check structure" --output-format text`, {
      cwd: dir,
      timeout: 90_000,
      encoding: 'utf-8',
    });
    // /check structure should output some kind of structure report
    assertContains(stdout, /structure|skill|plugin|check/i, '/check structure output');
  } finally {
    cleanupProject(dir);
  }
});
