#!/usr/bin/env node
import { readFileSync, existsSync, appendFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { join, dirname } from 'path';

const debug = process.env.CLAUDE_HOOKS_DEBUG === '1';
const handlersDir = join(dirname(fileURLToPath(import.meta.url)), 'handlers');
const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

async function main() {
  const start = Date.now();
  const domain = process.argv[2];
  const action = process.argv[3];

  if (!domain || !action) {
    process.exit(0);
  }

  const handlerPath = join(handlersDir, `${domain}.mjs`);
  if (!existsSync(handlerPath)) {
    if (debug) {
      process.stderr.write(
        `[hooks/runner] Unknown handler domain: "${domain}". No file at ${handlerPath}\n`,
      );
    }
    logTelemetry(domain, action, Date.now() - start, 'missing_handler');
    process.exit(0);
  }

  let input = {};
  try {
    const stdin = readFileSync(0, 'utf-8').trim();
    if (stdin) {
      input = JSON.parse(stdin);
    }
  } catch (e) {
    // Silently ignore stdin parse errors
  }

  try {
    const module = await import(`./handlers/${domain}.mjs`);
    if (typeof module[action] === 'function') {
      const result = await module[action](input);
      if (result) {
        process.stdout.write(`${JSON.stringify(result)}\n`);
      }
      logTelemetry(domain, action, Date.now() - start, 'success');
    } else {
      if (debug) {
        process.stderr.write(
          `[hooks/runner] Handler "${domain}" has no action "${action}". Available: ${Object.keys(
            module,
          )
            .filter((k) => typeof module[k] === 'function')
            .join(', ')}\n`,
        );
      }
      logTelemetry(domain, action, Date.now() - start, 'missing_action');
    }
  } catch (e) {
    if (debug) {
      process.stderr.write(`[hooks/runner] ${domain}.${action} failed: ${e.message}\n${e.stack}\n`);
    }
    logTelemetry(domain, action, Date.now() - start, 'error', e.message);
  }
}

function logTelemetry(domain, action, duration, status, error = '') {
  if (process.env.CLAUDE_USER_CONFIG_TELEMETRY_ENABLED === 'false') return;
  try {
    const claudeDir = join(projectDir, '.claude');
    if (!existsSync(claudeDir)) {
      mkdirSync(claudeDir, { recursive: true });
    }
    const logPath = join(claudeDir, 'telemetry.log');
    const timestamp = new Date().toISOString();
    const entry = `${JSON.stringify({ timestamp, domain, action, duration, status, error })}\n`;
    appendFileSync(logPath, entry);
  } catch (e) {
    // Fail silently if we can't log telemetry
  }
}

main();
