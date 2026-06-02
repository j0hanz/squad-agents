#!/usr/bin/env node

/**
 * Plugin validation script
 * Validates: YAML frontmatter, descriptions, agent triggers, skill structure
 * Exit code 0 = all valid, 1 = validation errors found
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

import { execSync } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pluginRoot = path.resolve(__dirname, '..');

const errors = [];
const warnings = [];

function getPythonPath() {
  const paths = [
    path.join(pluginRoot, '.venv', 'Scripts', 'python.exe'),
    path.join(pluginRoot, '.venv', 'bin', 'python'),
    'python3',
    'python',
  ];
  for (const p of paths) {
    try {
      if (fs.existsSync(p)) {
        return p;
      }
    } catch (e) {}
  }
  return 'python';
}

// Validate YAML frontmatter and description
function validateFrontmatter(filePath, componentType) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);

  if (!match) {
    errors.push(`[${componentType}] ${filePath}: Missing YAML frontmatter`);
    return null;
  }

  const frontmatter = match[1];
  const pythonPath = getPythonPath();
  const helperPath = path.join(pluginRoot, 'bin', 'validate_yaml.py');

  let fmData;
  try {
    const jsonStr = execSync(`"${pythonPath}" "${helperPath}"`, {
      input: frontmatter,
      stdio: ['pipe', 'pipe', 'pipe'],
    }).toString();
    fmData = JSON.parse(jsonStr);
  } catch (err) {
    const errMsg = err.stderr ? err.stderr.toString().trim() : err.message;
    errors.push(`[${componentType}] ${filePath}: Invalid YAML frontmatter - ${errMsg}`);
    return null;
  }

  if (!fmData || typeof fmData.description !== 'string' || !fmData.description.trim()) {
    errors.push(
      `[${componentType}] ${filePath}: Missing or empty 'description' field in frontmatter`,
    );
    return null;
  }

  return { frontmatter, content, fmData };
}

// Validate skill structure
function validateSkillStructure(skillDir) {
  const skillMd = path.join(skillDir, 'SKILL.md');

  if (!fs.existsSync(skillMd)) {
    errors.push(`[Skill] ${skillDir}: Missing SKILL.md`);
    return;
  }

  const result = validateFrontmatter(skillMd, 'Skill');
  if (!result) return;

  // Check for progressive disclosure structure in large skills
  const { content } = result;
  const lineCount = content.split('\n').length;

  if (lineCount > 300) {
    const hasReferences = fs.existsSync(path.join(skillDir, 'references'));
    if (!hasReferences) {
      warnings.push(
        `[Skill] ${skillDir}: Large skill (${lineCount} lines) should extract content to references/`,
      );
    }
  }
}

// Validate hook configuration
function validateHooks() {
  const hooksJson = path.join(pluginRoot, 'hooks', 'hooks.json');
  if (!fs.existsSync(hooksJson)) {
    errors.push('[Hooks] hooks/hooks.json not found');
    return;
  }

  try {
    const hooks = JSON.parse(fs.readFileSync(hooksJson, 'utf-8'));

    // Check that hook commands use runner.mjs pattern
    Object.entries(hooks.hooks || {}).forEach(([event, matchers]) => {
      matchers.forEach((matcher) => {
        matcher.hooks?.forEach((hook) => {
          if (hook.type === 'command' && !hook.command.includes('hooks/runner.mjs')) {
            errors.push(`[Hooks] Event ${event}: Command doesn't use hooks/runner.mjs pattern`);
          }
        });
      });
    });
  } catch (e) {
    errors.push(`[Hooks] Failed to parse hooks.json: ${e.message}`);
  }
}

// Main validation
function main() {
  console.log('🔍 Validating agent-dev plugin structure...\n');

  // Validate skills
  const skillsDir = path.join(pluginRoot, 'skills');
  if (fs.existsSync(skillsDir)) {
    try {
      fs.readdirSync(skillsDir).forEach((skill) => {
        const skillPath = path.join(skillsDir, skill);
        try {
          if (fs.statSync(skillPath).isDirectory()) {
            validateSkillStructure(skillPath);
          }
        } catch (e) {
          errors.push(`[Skills] Failed to stat skill ${skill}: ${e.message}`);
        }
      });
    } catch (e) {
      errors.push(`[Skills] Failed to read skills directory: ${e.message}`);
    }
  }

  // Validate agents
  const agentsDir = path.join(pluginRoot, 'agents');
  if (fs.existsSync(agentsDir)) {
    try {
      fs.readdirSync(agentsDir)
        .filter((f) => f.endsWith('.md'))
        .forEach((agent) => {
          const agentPath = path.join(agentsDir, agent);
          validateFrontmatter(agentPath, 'Agent');
        });
    } catch (e) {
      errors.push(`[Agents] Failed to read agents directory: ${e.message}`);
    }
  }

  // Validate hooks
  validateHooks();

  // Validate plugin.json
  const pluginJson = path.join(pluginRoot, '.claude-plugin', 'plugin.json');
  if (fs.existsSync(pluginJson)) {
    try {
      const plugin = JSON.parse(fs.readFileSync(pluginJson, 'utf-8'));
      if (typeof plugin.author !== 'object' || !plugin.author.name) {
        errors.push('[Plugin.json] author must be an object with "name" field');
      }
      if (typeof plugin.version !== 'string') {
        errors.push('[Plugin.json] version must be a string (e.g., "1.0.0")');
      }
      if (!Array.isArray(plugin.keywords)) {
        errors.push('[Plugin.json] keywords must be an array');
      }
    } catch (e) {
      errors.push(`[Plugin.json] Failed to parse: ${e.message}`);
    }
  }

  // Report results
  if (warnings.length > 0) {
    console.log('⚠️  Warnings:\n');
    warnings.forEach((w) => console.log(`  ${w}`));
    console.log();
  }

  if (errors.length > 0) {
    console.log('❌ Errors:\n');
    errors.forEach((e) => console.log(`  ${e}`));
    console.log(`\n${errors.length} error(s) found.\n`);
    process.exit(1);
  }

  console.log('✅ All validations passed!\n');
  process.exit(0);
}

main();
