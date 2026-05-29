export function extractImports(fileContent) {
  const imports = [];
  // Match `import ... from '...'` or `import '...'`
  const importRegex = /import(?:[\s.*{},_a-zA-Z0-9]+from\s+)?['"](.*?)['"]/g;
  // Match `require('...')`
  const requireRegex = /require\(['"](.*?)['"]\)/g;

  let match;
  while ((match = importRegex.exec(fileContent)) !== null) {
    imports.push(match[1]);
  }
  while ((match = requireRegex.exec(fileContent)) !== null) {
    imports.push(match[1]);
  }
  return imports;
}
