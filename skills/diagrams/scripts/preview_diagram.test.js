const test = require('node:test');
const assert = require('node:assert');
const { execSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const scriptPath = path.join(__dirname, 'preview_diagram.js');

test('preview_diagram generates URL and HTML file', () => {
    const testFile = path.join(__dirname, 'test_diagram.mmd');
    fs.writeFileSync(testFile, 'graph TD\nA-->B');
    
    const output = execSync(`node ${scriptPath} ${testFile}`).toString();
    assert.match(output, /https:\/\/kroki\.io\/mermaid\/svg\//);
    assert.match(output, /preview\.html/);
    
    fs.unlinkSync(testFile);
});