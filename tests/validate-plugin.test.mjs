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

  // Write a SKILL.md with invalid YAML frontmatter (line with no colon at all)
  const skillMdPath = path.join(tempSkillDir, 'SKILL.md');
  const invalidContent = `---
name: temp-invalid-skill
description
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
      assert.ok(
        output.includes('Invalid YAML frontmatter'),
        'Output should contain Invalid YAML frontmatter warning/error',
      );
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

test('validate-plugin detects missing description in agents/*.md', () => {
  const agentsDir = path.join(projectRoot, 'agents');
  const agentMdPath = path.join(agentsDir, 'temp-invalid-agent.md');
  const invalidContent = `---
name: temp-invalid-agent
tools: Read
---
Some instructions.
`;

  fs.writeFileSync(agentMdPath, invalidContent, 'utf-8');

  try {
    let errorOccurred = false;
    try {
      execSync(`node bin/validate-plugin.mjs`, { cwd: projectRoot, stdio: 'pipe' });
    } catch (err) {
      errorOccurred = true;
      const output = err.stdout.toString() + err.stderr.toString();
      assert.ok(
        output.includes("Missing or empty 'description'"),
        "Output should contain Missing or empty 'description' error",
      );
    }

    assert.ok(errorOccurred, 'Validator should have failed with exit code 1');
  } finally {
    if (fs.existsSync(agentMdPath)) {
      fs.unlinkSync(agentMdPath);
    }
  }
});

test('validate-plugin detects Bash(...) command-scoped tools syntax in agents/*.md', () => {
  const agentsDir = path.join(projectRoot, 'agents');
  const agentMdPath = path.join(agentsDir, 'temp-invalid-tools-agent.md');
  const invalidContent = `---
name: temp-invalid-tools-agent
description: Temp fixture for tool entry syntax validation.
tools: Read, Grep, Bash(git *)
---
Some instructions.
`;

  fs.writeFileSync(agentMdPath, invalidContent, 'utf-8');

  try {
    let errorOccurred = false;
    try {
      execSync(`node bin/validate-plugin.mjs`, { cwd: projectRoot, stdio: 'pipe' });
    } catch (err) {
      errorOccurred = true;
      const output = err.stdout.toString() + err.stderr.toString();
      assert.ok(
        output.includes("Invalid 'tools' entry") && output.includes('Bash(git *)'),
        'Output should flag the Bash(git *) command-scoped tools entry',
      );
    }
    assert.ok(errorOccurred, 'Validator should fail on Bash(git *) in tools:');
  } finally {
    if (fs.existsSync(agentMdPath)) {
      fs.unlinkSync(agentMdPath);
    }
  }
});

test('validate-plugin detects an agent name not matching ^[a-z][a-z0-9-]*$', () => {
  const agentsDir = path.join(projectRoot, 'agents');
  const agentMdPath = path.join(agentsDir, 'temp-bad-name-agent.md');
  const invalidContent = `---
name: TempBadName_Agent
description: Temp fixture for name pattern validation.
tools: Read
---
Some instructions.
`;

  fs.writeFileSync(agentMdPath, invalidContent, 'utf-8');

  try {
    let errorOccurred = false;
    try {
      execSync(`node bin/validate-plugin.mjs`, { cwd: projectRoot, stdio: 'pipe' });
    } catch (err) {
      errorOccurred = true;
      const output = err.stdout.toString() + err.stderr.toString();
      assert.ok(
        output.includes('must match ^[a-z][a-z0-9-]*$'),
        'Output should flag the invalid name pattern',
      );
    }
    assert.ok(errorOccurred, 'Validator should fail on an invalid agent name pattern');
  } finally {
    if (fs.existsSync(agentMdPath)) {
      fs.unlinkSync(agentMdPath);
    }
  }
});

test('validate-plugin detects duplicate agent names across files', () => {
  const agentsDir = path.join(projectRoot, 'agents');
  const firstPath = path.join(agentsDir, 'temp-dup-agent-one.md');
  const secondPath = path.join(agentsDir, 'temp-dup-agent-two.md');
  const content = (desc) => `---
name: temp-dup-agent
description: ${desc}
tools: Read
---
Some instructions.
`;

  fs.writeFileSync(
    firstPath,
    content('First temp fixture for duplicate-name validation.'),
    'utf-8',
  );
  fs.writeFileSync(
    secondPath,
    content('Second temp fixture for duplicate-name validation.'),
    'utf-8',
  );

  try {
    let errorOccurred = false;
    try {
      execSync(`node bin/validate-plugin.mjs`, { cwd: projectRoot, stdio: 'pipe' });
    } catch (err) {
      errorOccurred = true;
      const output = err.stdout.toString() + err.stderr.toString();
      assert.ok(
        output.includes('Duplicate agent') && output.includes('temp-dup-agent'),
        'Output should flag the duplicate agent name',
      );
    }
    assert.ok(errorOccurred, 'Validator should fail on a duplicate agent name');
  } finally {
    if (fs.existsSync(firstPath)) fs.unlinkSync(firstPath);
    if (fs.existsSync(secondPath)) fs.unlinkSync(secondPath);
  }
});

test('validate-plugin detects an invalid model enum value in agents/*.md', () => {
  const agentsDir = path.join(projectRoot, 'agents');
  const agentMdPath = path.join(agentsDir, 'temp-invalid-model-agent.md');
  const invalidContent = `---
name: temp-invalid-model-agent
description: Temp fixture for model enum validation.
tools: Read
model: gpt-4
---
Some instructions.
`;

  fs.writeFileSync(agentMdPath, invalidContent, 'utf-8');

  try {
    let errorOccurred = false;
    try {
      execSync(`node bin/validate-plugin.mjs`, { cwd: projectRoot, stdio: 'pipe' });
    } catch (err) {
      errorOccurred = true;
      const output = err.stdout.toString() + err.stderr.toString();
      assert.ok(
        output.includes("Invalid 'model' value"),
        'Output should flag the invalid model value',
      );
    }
    assert.ok(errorOccurred, 'Validator should fail on an invalid model enum value');
  } finally {
    if (fs.existsSync(agentMdPath)) {
      fs.unlinkSync(agentMdPath);
    }
  }
});

test('validate-plugin detects a dangling cross-skill routing reference', () => {
  const tempSkillDir = path.join(projectRoot, 'skills', 'temp-routing-skill');
  if (!fs.existsSync(tempSkillDir)) {
    fs.mkdirSync(tempSkillDir);
  }
  const skillMdPath = path.join(tempSkillDir, 'SKILL.md');
  // Valid frontmatter, but the body points at a skill that does not exist.
  const content = `---
name: temp-routing-skill
description: "Temp skill for routing validation. Trigger on: 'temp routing'."
---

See \`../no-such-skill/references/thing.md\` for details.
`;
  fs.writeFileSync(skillMdPath, content, 'utf-8');

  try {
    let errorOccurred = false;
    try {
      execSync(`node bin/validate-plugin.mjs`, { cwd: projectRoot, stdio: 'pipe' });
    } catch (err) {
      errorOccurred = true;
      const output = err.stdout.toString() + err.stderr.toString();
      assert.ok(
        output.includes('dangling cross-skill reference') && output.includes('no-such-skill'),
        'Output should flag the dangling cross-skill reference',
      );
    }
    assert.ok(errorOccurred, 'Validator should fail on a dangling cross-skill reference');
  } finally {
    if (fs.existsSync(skillMdPath)) {
      fs.unlinkSync(skillMdPath);
    }
    if (fs.existsSync(tempSkillDir)) {
      fs.rmdirSync(tempSkillDir);
    }
  }
});

test('validate-plugin handles block scalar YAML frontmatter', () => {
  const tempSkillDir = path.join(projectRoot, 'skills', 'temp-block-scalar-skill');
  if (!fs.existsSync(tempSkillDir)) {
    fs.mkdirSync(tempSkillDir);
  }
  const skillMdPath = path.join(tempSkillDir, 'SKILL.md');
  const content = `---
name: temp-block-scalar-skill
description: >
  A multiline description
  that should parse cleanly.
---
Some instructions.
`;

  fs.writeFileSync(skillMdPath, content, 'utf-8');

  try {
    execSync(`node bin/validate-plugin.mjs`, { cwd: projectRoot, stdio: 'pipe' });
  } finally {
    if (fs.existsSync(skillMdPath)) {
      fs.unlinkSync(skillMdPath);
    }
    if (fs.existsSync(tempSkillDir)) {
      fs.rmdirSync(tempSkillDir);
    }
  }
});
