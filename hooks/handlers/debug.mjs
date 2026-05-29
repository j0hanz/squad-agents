import { execSync } from 'child_process';

const ARTIFACT_PATTERNS = [
  /\bconsole\.log\b/,
  /\bdebugger\b/,
  /\bprint\(/,
  /\bpdb\.set_trace\(\)/,
  /\bbreakpoint\(\)/,
  /\bbinding\.pry\b/,
  /\bbyebug\b/,
  /\/\/ FIXME\b/i,
  /\/\/ HACK\b/i,
  /# FIXME\b/i,
  /# HACK\b/i,
];

const EXEMPT_NAME_PATTERN = /\b(log|debug|util|helper)\b/i;
const INLINE_EXEMPT = /debug-keep/;

export async function check(_input) {
  let changedFiles;
  try {
    const output = execSync('git diff --name-only HEAD', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    }).trim();
    changedFiles = output ? output.split('\n').filter(Boolean) : [];
  } catch {
    return { decision: 'approve' };
  }

  const findings = [];

  for (const file of changedFiles) {
    if (EXEMPT_NAME_PATTERN.test(file)) continue;

    let lines;
    try {
      const content = execSync(`git diff HEAD -- "${file}"`, {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'ignore'],
      });
      lines = content.split('\n').filter((l) => l.startsWith('+') && !l.startsWith('+++'));
    } catch {
      continue;
    }

    lines.forEach((line, idx) => {
      if (INLINE_EXEMPT.test(line)) return;
      const code = line.slice(1);
      for (const pattern of ARTIFACT_PATTERNS) {
        if (pattern.test(code)) {
          findings.push({ file, line: idx + 1, match: pattern.source, content: code.trim() });
          break;
        }
      }
    });
  }

  if (findings.length > 0) {
    const detail = findings
      .slice(0, 5)
      .map((f) => `  ${f.file}:~${f.line}  ${f.content.slice(0, 80)}`)
      .join('\n');
    process.stderr.write(
      `[agent-dev] ⚠ Debug artifacts found — review before finishing:\n${detail}\n`,
    );
  }

  return { decision: 'approve' };
}

export async function hookChanged(input) {
  const file = input?.file_path || 'hooks/hooks.json';
  const base = file.split(/[\\/]/).pop();
  return `[agent-dev] ${base} changed on disk — run /agent-dev:check hooks to validate the updated configuration.`;
}
