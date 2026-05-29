const test = require('node:test');
const assert = require('node:assert');
const { execSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const scriptPath = path.join(__dirname, 'scaffold_c4.js');

test('scaffold_c4 generates basic C4 from package.json', () => {
    const testDir = path.join(__dirname, 'test_proj');
    fs.mkdirSync(testDir, { recursive: true });
    fs.writeFileSync(path.join(testDir, 'package.json'), JSON.stringify({ dependencies: { 'express': '*', 'pg': '*' } }));
    
    const output = execSync(`node ${scriptPath} ${testDir}`).toString();
    assert.match(output, /C4Context/);
    assert.match(output, /System\(app, "Application", "Main Application"\)/);
    assert.match(output, /SystemDb\(db, "Database", "Relational\/NoSQL Database"\)/);
    
    fs.unlinkSync(path.join(testDir, 'package.json'));
    fs.rmdirSync(testDir);
});