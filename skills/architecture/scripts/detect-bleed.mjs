import fs from 'fs';
import path from 'path';
import { extractImports } from './utils/extractor.mjs';

function walkDir(dir, exclude) {
    let files = [];
    try {
        const list = fs.readdirSync(dir);
        for (const file of list) {
            if (exclude.some(ex => file.includes(ex))) continue;
            const fullPath = path.join(dir, file);
            let stat;
            try {
                stat = fs.statSync(fullPath);
            } catch (e) {
                continue;
            }
            if (stat.isDirectory()) {
                files = files.concat(walkDir(fullPath, exclude));
            } else if (fullPath.endsWith('.ts') || fullPath.endsWith('.tsx') || fullPath.endsWith('.js')) {
                files.push(fullPath);
            }
        }
    } catch (e) {
    }
    return files;
}

const defaultExclude = [
    'node_modules', '.test.', '.spec.',
    '.git', '.svn', '.hg',
    '.pytest_cache', '.tox', '__pycache__',
    '.venv', 'venv', '.env',
    'dist', 'build', 'coverage', '.coverage',
    '.next', '.nuxt', '.cache', '.parcel',
    '.npm', '.yarn',
    'target', '.gradle', '.m2',
    '.pytest', '.mypy_cache', '.ruff_cache',
    '.vscode', '.idea', '.DS_Store'
];

export function runBleedDetection(targetDir, infraPackages) {
    const files = walkDir(targetDir, defaultExclude);
    const violations = [];

    for (const file of files) {
        const content = fs.readFileSync(file, 'utf8');
        const lines = content.split('\n');
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const imports = extractImports(line);
            
            for (const imp of imports) {
                if (infraPackages.includes(imp) || infraPackages.some(pkg => imp.startsWith(`${pkg  }/`))) {
                    violations.push({
                        file,
                        violation: imp,
                        line: i + 1,
                        code: line.trim()
                    });
                }
            }
        }
    }
    return violations;
}

// CLI entry point
if (process.argv[1] && (process.argv[1] === new URL(import.meta.url).pathname || process.argv[1].endsWith('detect-bleed.mjs'))) {
    const dir = process.argv[2] || 'src/domain';
    const infraArg = process.argv[3] || 'express,typeorm,prisma,fs,path,react,mongoose';
    const infraPackages = infraArg.split(',');

    console.log(`Checking ${dir} for infrastructure bleeds (${infraPackages.join(', ')})...`);
    
    try {
        const violations = runBleedDetection(path.resolve(process.cwd(), dir), infraPackages);
        
        console.log('\n--- Infrastructure Leaks (Seam Test Failures) ---');
        if (violations.length === 0) {
            console.log('None found. Domain looks pure.');
        } else {
            console.table(violations.map(v => ({
                File: path.relative(process.cwd(), v.file),
                Leak: v.violation,
                Line: v.line
            })));
        }
    } catch (e) {
         if(e.code === 'ENOENT') {
             console.error(`Directory not found: ${dir}`);
         } else {
             console.error(e);
         }
    }
}
