import fs from 'fs';
import path from 'path';

const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || process.cwd();

function generateDiagram() {
  const commands = fs.readdirSync(path.join(pluginRoot, 'commands'))
    .filter(f => f.endsWith('.md'))
    .map(f => f.replace('.md', ''));
  
  const agents = fs.readdirSync(path.join(pluginRoot, 'agents'))
    .filter(f => f.endsWith('.md'))
    .map(f => f.replace('.md', ''));
  
  const skills = fs.readdirSync(path.join(pluginRoot, 'skills'))
    .filter(f => fs.statSync(path.join(pluginRoot, 'skills', f)).isDirectory());

  let mermaid = 'graph TD\n';
  
  mermaid += '  subgraph Commands\n';
  commands.forEach(c => {
    mermaid += `    C_${c.replace(/-/g, '_')}(/${c})\n`;
  });
  mermaid += '  end\n\n';

  mermaid += '  subgraph Agents\n';
  agents.forEach(a => {
    mermaid += `    A_${a.replace(/-/g, '_')}[${a} agent]\n`;
  });
  mermaid += '  end\n\n';

  mermaid += '  subgraph Skills\n';
  skills.forEach(s => {
    mermaid += `    S_${s.replace(/-/g, '_')}((skill: ${s}))\n`;
  });
  mermaid += '  end\n\n';

  // Basic wiring heuristics
  if (commands.includes('plan')) {
    mermaid += '  C_plan --> S_brainstorming\n';
    mermaid += '  C_plan --> S_create_specs\n';
    mermaid += '  C_plan --> S_create_plan\n';
  }
  
  if (commands.includes('eval')) {
    mermaid += '  C_eval --> S_skill_builder\n';
  }
  
  if (commands.includes('deliver')) {
    mermaid += '  C_deliver --> S_delivery_manager\n';
  }

  return mermaid;
}

const diagram = generateDiagram();
const outPath = path.join(pluginRoot, 'docs', 'plugin-architecture.mmd');
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, diagram);
console.log(`Diagram generated at ${outPath}`);
console.log('To view, run: node skills/diagrams/scripts/preview_diagram.js docs/plugin-architecture.mmd');
