const fs = require('node:fs');
const path = require('node:path');

const targetDir = process.argv[2] || process.cwd();
const pkgPath = path.join(targetDir, 'package.json');

let output = 'C4Context\n  title System Context Diagram\n';

if (fs.existsSync(pkgPath)) {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
    const deps = pkg.dependencies || {};
    
    if (deps['express'] || deps['react']) {
        output += `  System(app, "Application", "Main Application")\n`;
    }
    if (deps['pg'] || deps['mongoose']) {
        output += `  SystemDb(db, "Database", "Relational/NoSQL Database")\n  Rel(app, db, "Reads from and writes to")\n`;
    }
} else {
    output += `  System(app, "Application", "Generic App")\n`;
}

console.log(output);