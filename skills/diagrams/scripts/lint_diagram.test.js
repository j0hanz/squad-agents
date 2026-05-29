const test = require('node:test');
const assert = require('node:assert');
const { execSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const scriptPath = path.join(__dirname, 'lint_diagram.js');

test('lint_diagram fails on > 20 nodes', () => {
    const hugeDiagram = `graph TD\n${  Array.from({length: 25}, (_, i) => `A${i}-->B${i}`).join('\n')}`;
    const testFile = path.join(__dirname, 'test_huge.mmd');
    fs.writeFileSync(testFile, hugeDiagram);
    
    try {
        execSync(`node ${scriptPath} ${testFile}`);
        assert.fail('Should have thrown error');
    } catch (err) {
        assert.match(err.stdout.toString(), /Fail: Diagram exceeds 20 nodes/);
    }
    fs.unlinkSync(testFile);
});