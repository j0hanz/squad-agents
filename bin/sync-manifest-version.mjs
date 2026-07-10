#!/usr/bin/env node

// Runs as npm's "version" lifecycle script: keeps the Claude-plugin manifests
// in sync with the version npm just wrote to package.json, then stages them
// so they land in the same commit npm is about to create.

import fs from 'fs';
import { execFileSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');

const { version } = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));

const pluginPath = path.join(root, '.claude-plugin', 'plugin.json');
const plugin = JSON.parse(fs.readFileSync(pluginPath, 'utf8'));
plugin.version = version;
fs.writeFileSync(pluginPath, `${JSON.stringify(plugin, null, 2)}\n`);

const marketplacePath = path.join(root, '.claude-plugin', 'marketplace.json');
const marketplace = JSON.parse(fs.readFileSync(marketplacePath, 'utf8'));
if (!marketplace.plugins || !Array.isArray(marketplace.plugins) || marketplace.plugins.length === 0) {
  console.error("Error: 'plugins' list is missing or empty in marketplace.json");
  process.exit(1);
}
marketplace.plugins[0].version = version;
fs.writeFileSync(marketplacePath, `${JSON.stringify(marketplace, null, 2)}\n`);

const pyprojectPath = path.join(root, 'pyproject.toml');
let pyproject = fs.readFileSync(pyprojectPath, 'utf8');
pyproject = pyproject.replace(/version\s*=\s*"[^"]*"/, `version = "${version}"`);
fs.writeFileSync(pyprojectPath, pyproject, 'utf8');

execFileSync('git', ['add', pluginPath, marketplacePath, pyprojectPath], { cwd: root });
