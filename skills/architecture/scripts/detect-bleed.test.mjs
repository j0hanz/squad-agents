import test from 'node:test';
import assert from 'node:assert';
import { runBleedDetection } from './detect-bleed.mjs';
import path from 'path';

test('detects infrastructure imports in domain file', () => {
    const fixtureDir = path.join(process.cwd(), 'skills/architecture/scripts/fixtures');
    const result = runBleedDetection(fixtureDir, ['express']);
    
    assert.strictEqual(result.length, 1);
    assert.ok(result[0].file.endsWith('domain.ts'));
    assert.strictEqual(result[0].violation, 'express');
});
