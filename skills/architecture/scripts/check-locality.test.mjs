import test from 'node:test';
import assert from 'node:assert';
import { runLocalityCheck } from './check-locality.mjs';
import path from 'path';

test('identifies circular dependencies in fixtures', () => {
    const fixtureDir = path.join(process.cwd(), 'skills/architecture/scripts/fixtures');
    const result = runLocalityCheck(fixtureDir, ['domain.ts']);
    assert.strictEqual(result.cycles.length, 1);
    const cycleFiles = result.cycles[0].map(f => path.basename(f));
    assert.ok(cycleFiles.includes('a.ts'));
    assert.ok(cycleFiles.includes('b.ts'));
    assert.ok(cycleFiles.includes('c.ts'));
});
