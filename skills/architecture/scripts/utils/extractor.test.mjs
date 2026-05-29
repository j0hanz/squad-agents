import test from 'node:test';
import assert from 'node:assert';
import { extractImports } from './extractor.mjs';

test('extracts imports from TypeScript file content', () => {
  const content = `
    import { a } from './a';
    import type { B } from '../b';
    import defaultExport from 'package';
    require('fs');
  `;
  const imports = extractImports(content);
  assert.deepStrictEqual(imports, ['./a', '../b', 'package', 'fs']);
});
