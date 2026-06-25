#!/usr/bin/env node

/**
 * Plugin validation script
 * Validates: YAML frontmatter, descriptions, agent triggers, skill structure
 * Exit code 0 = all valid, 1 = validation errors found
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pluginRoot = path.resolve(__dirname, '..');

const errors = [];
const warnings = [];

// Helper to parse simple YAML frontmatter metadata
function parseFrontmatter(frontmatterStr) {
  const data = {};
  const lines = frontmatterStr.split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    if (line.match(/^[ \t]/)) continue; // skip nested/indented YAML (e.g. an agent hooks: block) — only top-level scalars are validated
    const colonIndex = trimmed.indexOf(':');
    if (colonIndex === -1) {
      throw new Error(`Invalid line in YAML frontmatter (missing colon): "${trimmed}"`);
    }
    const key = trimmed.slice(0, colonIndex).trim();
    let value = trimmed.slice(colonIndex + 1).trim();
    const isQuoted =
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"));
    if (isQuoted) {
      value = value.slice(1, -1);
    } else {
      if (value.includes(':')) {
        throw new Error(`Invalid unquoted colon in YAML value: "${value}"`);
      }
    }
    data[key] = value;
  }
  return data;
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
  let fmData;
  try {
    fmData = parseFrontmatter(frontmatter);
  } catch (err) {
    errors.push(`[${componentType}] ${filePath}: Invalid YAML frontmatter - ${err.message}`);
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

// A valid tools/disallowedTools entry is a bare tool name, an MCP reference
// (mcp__server, mcp__server__tool, mcp__server__*, or the disallowedTools-only
// mcp__* wildcard), an Agent(...) reference, or the deprecated Task(...) alias
// that still works per docs. Anything else with parens — e.g. the Bash(git *)
// command-scoped syntax valid in skill allowed-tools / settings.json
// permissions but NOT in agent tools: — is invalid here.
const VALID_TOOL_ENTRY =
  /^(mcp__\*|mcp__[\w-]+(__([\w-]+|\*))?|Agent\([^)]*\)|Task\([^)]*\)|[A-Za-z][\w-]*)$/;
const VALID_MODELS = new Set(['sonnet', 'opus', 'haiku', 'fable', 'inherit']);
const VALID_COLORS = new Set([
  'red',
  'blue',
  'green',
  'yellow',
  'purple',
  'orange',
  'pink',
  'cyan',
]);
const VALID_PERMISSION_MODES = new Set([
  'default',
  'acceptEdits',
  'auto',
  'dontAsk',
  'bypassPermissions',
  'plan',
]);
const VALID_MEMORY = new Set(['user', 'project', 'local']);
const AGENT_NAME_PATTERN = /^[a-z][a-z0-9-]*$/;

// Validates one tools/disallowedTools comma-joined string (parseFrontmatter's
// flat-line parser always produces these as a single string, never pre-split).
function validateToolList(agentMd, fieldName, rawValue) {
  rawValue
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .forEach((entry) => {
      if (!VALID_TOOL_ENTRY.test(entry)) {
        errors.push(
          `[Agent] ${agentMd}: Invalid '${fieldName}' entry "${entry}" — only bare tool names, mcp__server[__tool|__*], Agent(...), or Task(...) are valid (e.g. "Bash(git *)" is not documented for agent tools:)`,
        );
      }
    });
}

// Validate agent structure. agentNamesSeen: Map<name, firstFilePath> threaded
// in from main() so duplicate names across different agents/*.md files can be
// detected (docs warn duplicates are silently resolved with no runtime error).
function validateAgentStructure(agentMd, agentNamesSeen) {
  const result = validateFrontmatter(agentMd, 'Agent');
  if (!result) return;

  const { fmData } = result;

  if (typeof fmData.name !== 'string' || !fmData.name.trim()) {
    errors.push(`[Agent] ${agentMd}: Missing or empty 'name' field in frontmatter`);
  } else {
    const name = fmData.name.trim();
    if (!AGENT_NAME_PATTERN.test(name)) {
      errors.push(
        `[Agent] ${agentMd}: 'name' field "${name}" must match ^[a-z][a-z0-9-]*$ (lowercase letters, digits, hyphens, starting with a letter)`,
      );
    }
    if (agentNamesSeen.has(name)) {
      errors.push(
        `[Agent] ${agentMd}: Duplicate agent 'name' "${name}" — also defined in ${agentNamesSeen.get(name)}. Docs warn duplicates are silently resolved with no runtime error.`,
      );
    } else {
      agentNamesSeen.set(name, agentMd);
    }
  }

  if (typeof fmData.tools === 'string' && fmData.tools.trim()) {
    validateToolList(agentMd, 'tools', fmData.tools);
  }
  if (typeof fmData.disallowedTools === 'string' && fmData.disallowedTools.trim()) {
    validateToolList(agentMd, 'disallowedTools', fmData.disallowedTools);
  }

  if (typeof fmData.model === 'string' && fmData.model.trim()) {
    const model = fmData.model.trim();
    if (!VALID_MODELS.has(model) && !model.startsWith('claude-')) {
      errors.push(
        `[Agent] ${agentMd}: Invalid 'model' value "${model}" — expected one of ${[...VALID_MODELS].join('|')}, or a claude-* model id`,
      );
    }
  }

  if (typeof fmData.color === 'string' && fmData.color.trim()) {
    const color = fmData.color.trim();
    if (!VALID_COLORS.has(color)) {
      errors.push(
        `[Agent] ${agentMd}: Invalid 'color' value "${color}" — expected one of ${[...VALID_COLORS].join('|')}`,
      );
    }
  }

  if (typeof fmData.permissionMode === 'string' && fmData.permissionMode.trim()) {
    const mode = fmData.permissionMode.trim();
    if (!VALID_PERMISSION_MODES.has(mode)) {
      errors.push(
        `[Agent] ${agentMd}: Invalid 'permissionMode' value "${mode}" — expected one of ${[...VALID_PERMISSION_MODES].join('|')}`,
      );
    }
  }

  if (typeof fmData.memory === 'string' && fmData.memory.trim()) {
    const mem = fmData.memory.trim();
    if (!VALID_MEMORY.has(mem)) {
      errors.push(
        `[Agent] ${agentMd}: Invalid 'memory' value "${mem}" — expected one of ${[...VALID_MEMORY].join('|')}`,
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

    // Hook commands must invoke a bash handler under hooks/*.sh via
    // ${CLAUDE_PLUGIN_ROOT} (no hardcoded paths, no .mjs/.py handlers).
    Object.entries(hooks.hooks || {}).forEach(([event, matchers]) => {
      matchers.forEach((matcher) => {
        matcher.hooks?.forEach((hook) => {
          if (hook.type !== 'command') return;

          if (!hook.command.includes('${CLAUDE_PLUGIN_ROOT}')) {
            warnings.push(
              `[Hooks] Event ${event}: Command doesn't reference \${CLAUDE_PLUGIN_ROOT} — hardcoded paths break in other installs`,
            );
          }

          const match = hook.command.match(/hooks\/([\w-]+\.sh)/);
          if (!match) {
            warnings.push(`[Hooks] Event ${event}: Command doesn't reference a hooks/*.sh handler`);
            return;
          }

          const handlerPath = path.join(pluginRoot, 'hooks', match[1]);
          if (!fs.existsSync(handlerPath)) {
            errors.push(`[Hooks] Event ${event}: Handler file not found: hooks/${match[1]}`);
          }
        });
      });
    });
  } catch (e) {
    errors.push(`[Hooks] Failed to parse hooks.json: ${e.message}`);
  }
}

// Validate cross-skill routing references (see docs/adr/0001-routing-graph-duplication.md).
// Routing knowledge is intentionally duplicated between the central router and each skill;
// this guards the duplication against drift instead of deduplicating it.
const ROUTER_SKILL = 'using-agent-dev-skills';
function validateRouting(skillsDir) {
  let skillNames;
  try {
    skillNames = fs
      .readdirSync(skillsDir)
      .filter((d) => fs.existsSync(path.join(skillsDir, d, 'SKILL.md')));
  } catch {
    return; // skills-dir read failure is already reported by main()
  }
  const known = new Set(skillNames);

  // ERROR: every `../<sibling>/` cross-skill reference must resolve to a real skill dir.
  // Catches dangling links left by a rename/removal, including the shared
  // multi-agent-development/references/subagent-contract.md path.
  for (const name of skillNames) {
    const content = fs.readFileSync(path.join(skillsDir, name, 'SKILL.md'), 'utf-8');
    const seen = new Set();
    for (const m of content.matchAll(/\.\.\/([a-z0-9-]+)\//g)) {
      const target = m[1];
      if (seen.has(target)) continue;
      seen.add(target);
      if (!known.has(target)) {
        errors.push(
          `[Routing] skills/${name}/SKILL.md: dangling cross-skill reference '../${target}/' — no such skill`,
        );
      }
    }
  }

  // WARNING: every skill should be wired into the router graph by name.
  // Catches a skill added but never routed to from any gate.
  const routerMd = path.join(skillsDir, ROUTER_SKILL, 'SKILL.md');
  if (fs.existsSync(routerMd)) {
    const routerContent = fs.readFileSync(routerMd, 'utf-8');
    for (const name of skillNames) {
      if (name === ROUTER_SKILL) continue;
      if (!new RegExp(`\\b${name}\\b`).test(routerContent)) {
        warnings.push(
          `[Routing] Skill '${name}' is not referenced in the router (${ROUTER_SKILL}) graph — wire it into a gate`,
        );
      }
    }
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
    validateRouting(skillsDir);
  }

  // Validate agents
  const agentsDir = path.join(pluginRoot, 'agents');
  if (fs.existsSync(agentsDir)) {
    const agentNamesSeen = new Map();
    try {
      fs.readdirSync(agentsDir).forEach((file) => {
        if (!file.endsWith('.md')) return;
        const agentPath = path.join(agentsDir, file);
        try {
          if (fs.statSync(agentPath).isFile()) {
            validateAgentStructure(agentPath, agentNamesSeen);
          }
        } catch (e) {
          errors.push(`[Agents] Failed to stat agent ${file}: ${e.message}`);
        }
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
