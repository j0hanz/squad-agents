import test from 'node:test';
import assert from 'node:assert';
import { findCycles } from './graph.mjs';

test('finds simple cycles in an adjacency list', () => {
  const graph = {
    'a.ts': ['b.ts'],
    'b.ts': ['c.ts'],
    'c.ts': ['a.ts'],
    'd.ts': ['a.ts']
  };
  const cycles = findCycles(graph);
  assert.strictEqual(cycles.length, 1);
  assert.deepStrictEqual(cycles[0].sort(), ['a.ts', 'b.ts', 'c.ts'].sort());
});

test('handles graphs without cycles', () => {
    const graph = {
        'a.ts': ['b.ts'],
        'b.ts': ['c.ts'],
        'c.ts': []
    };
    const cycles = findCycles(graph);
    assert.strictEqual(cycles.length, 0);
});
