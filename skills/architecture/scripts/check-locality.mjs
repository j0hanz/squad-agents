import fs from 'fs';
import path from 'path';
import { extractImports } from './utils/extractor.mjs';
import { findCycles } from './utils/graph.mjs';

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
                // Skip files/dirs we can't read (permissions, symlinks, etc.)
                continue;
            }
            if (stat.isDirectory()) {
                files = files.concat(walkDir(fullPath, exclude));
            } else if (fullPath.endsWith('.ts') || fullPath.endsWith('.tsx') || fullPath.endsWith('.js')) {
                files.push(fullPath);
            }
        }
    } catch (e) {
        // Skip directories we can't read
    }
    return files;
}

export function runLocalityCheck(targetDir, exclude = [
    'node_modules', '.test.', '.spec.',
    '.git', '.svn', '.hg',
    '.pytest_cache', '.tox', '__pycache__',
    '.venv', 'venv', '.env',
    'dist', 'build', 'coverage', '.coverage',
    '.next', '.nuxt', '.cache', '.parcel',
    'node_modules', '.npm', '.yarn',
    'target', '.gradle', '.m2',
    '.pytest', '.mypy_cache', '.ruff_cache',
    '.vscode', '.idea', '.DS_Store'
]) {
    const files = walkDir(targetDir, exclude);
    const graph = {};

    for (const file of files) {
        const content = fs.readFileSync(file, 'utf8');
        const imports = extractImports(content);
        graph[file] = [];
        
        for (const imp of imports) {
            // Only care about relative imports for locality
            if (imp.startsWith('.')) {
                // Crude resolution: just append .ts (assumes fixtures logic for now)
                // A robust script would need proper node module resolution here
                const resolved = path.resolve(path.dirname(file), imp);
                if (fs.existsSync(`${resolved  }.ts`)) {
                     graph[file].push(`${resolved  }.ts`);
                } else if (fs.existsSync(`${resolved  }.tsx`)) {
                     graph[file].push(`${resolved  }.tsx`);
                } else if (fs.existsSync(`${resolved  }/index.ts`)) {
                     graph[file].push(`${resolved  }/index.ts`);
                }
            }
        }
    }

    const cycles = findCycles(graph);
    
    // Calculate Fan-out
    const fanOut = Object.entries(graph)
        .map(([file, deps]) => ({ file, count: deps.length }))
        .sort((a, b) => b.count - a.count);

    return { cycles, fanOut };
}

// CLI entry point
if (process.argv[1] && (process.argv[1] === new URL(import.meta.url).pathname || process.argv[1].endsWith('check-locality.mjs'))) {
    const dir = process.argv[2] || 'src';
    console.log(`Checking locality in ${dir}...`);
    try {
      const { cycles, fanOut } = runLocalityCheck(path.resolve(process.cwd(), dir));
      console.log('\n--- Circular Dependencies ---');
      cycles.forEach((cycle, i) => {
          console.log(`\nCycle ${i + 1}:`);
          cycle.forEach(c => console.log(`  - ${path.relative(process.cwd(), c)}`));
      });
      if (cycles.length === 0) console.log('None found.');

      console.log('\n--- Top 5 Fan-out (Highest Imports) ---');
      fanOut.slice(0, 5).forEach(f => {
          console.log(`  - ${path.relative(process.cwd(), f.file)} (${f.count} imports)`);
      });
    } catch (e) {
      if(e.code === 'ENOENT') {
         console.error(`Directory not found: ${dir}`);
      } else {
         console.error(e);
      }
    }
}
