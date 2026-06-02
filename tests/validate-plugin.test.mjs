import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');

test('validate-plugin detects invalid YAML frontmatter in skills', () => {
  // Create a temporary directory under skills/ for testing
  const tempSkillDir = path.join(projectRoot, 'skills', 'temp-invalid-skill');
  if (!fs.existsSync(tempSkillDir)) {
    fs.mkdirSync(tempSkillDir);
  }
  
  // Write a SKILL.md with invalid YAML frontmatter (unquoted colon in value)
  const skillMdPath = path.join(tempSkillDir, 'SKILL.md');
  const invalidContent = `---
name: temp-invalid-skill
description: Invalid YAML description: which fails validation
---
Some instructions.
`;
  
  fs.writeFileSync(skillMdPath, invalidContent, 'utf-8');
  
  try {
    // Run the validator, it should fail and exit with code 1
    let errorOccurred = false;
    try {
      execSync(`node bin/validate-plugin.mjs`, { cwd: projectRoot, stdio: 'pipe' });
    } catch (err) {
      errorOccurred = true;
      const output = err.stdout.toString() + err.stderr.toString();
      assert.ok(output.includes('Invalid YAML frontmatter'), 'Output should contain Invalid YAML frontmatter warning/error');
    }
    
    assert.ok(errorOccurred, 'Validator should have failed with exit code 1');
  } finally {
    // Cleanup
    if (fs.existsSync(skillMdPath)) {
      fs.unlinkSync(skillMdPath);
    }
    if (fs.existsSync(tempSkillDir)) {
      fs.rmdirSync(tempSkillDir);
    }
  }
});
