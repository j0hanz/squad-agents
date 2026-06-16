import fs from 'node:fs';
import path from 'node:path';

const PATTERNS = {
  hexagonal: {
    description: 'Ports & Adapters — domain isolated from all infrastructure',
    dirs: ['domain', 'ports', 'adapters/infra', 'adapters/http'],
    files: (domain) => [
      {
        rel: `domain/${domain}.ts`,
        content: `// Core domain entity — no infrastructure imports allowed here
export interface ${pascal(domain)} {
  id: string;
  // TODO: add domain fields
}
`,
      },
      {
        rel: `ports/${domain}-repository.port.ts`,
        content: `import type { ${pascal(domain)} } from '../domain/${domain}';

// Inbound port — what the domain exposes to the outside world
export interface ${pascal(domain)}Repository {
  findById(id: string): Promise<${pascal(domain)} | null>;
  save(entity: ${pascal(domain)}): Promise<void>;
  delete(id: string): Promise<void>;
}
`,
      },
      {
        rel: `ports/${domain}-service.port.ts`,
        content: `import type { ${pascal(domain)} } from '../domain/${domain}';

// Outbound port — what the application layer calls
export interface ${pascal(domain)}Service {
  get(id: string): Promise<${pascal(domain)} | null>;
  create(data: Omit<${pascal(domain)}, 'id'>): Promise<${pascal(domain)}>;
}
`,
      },
      {
        rel: `adapters/infra/${domain}-repository.adapter.ts`,
        content: `import type { ${pascal(domain)}Repository } from '../../ports/${domain}-repository.port';
import type { ${pascal(domain)} } from '../../domain/${domain}';

// Infrastructure adapter — implements the port using your DB/ORM
// ONLY this file should import Prisma, TypeORM, SQLAlchemy, etc.
export class ${pascal(domain)}RepositoryAdapter implements ${pascal(domain)}Repository {
  async findById(id: string): Promise<${pascal(domain)} | null> {
    throw new Error('Not implemented');
  }

  async save(entity: ${pascal(domain)}): Promise<void> {
    throw new Error('Not implemented');
  }

  async delete(id: string): Promise<void> {
    throw new Error('Not implemented');
  }
}
`,
      },
      {
        rel: `adapters/http/${domain}.controller.ts`,
        content: `import type { ${pascal(domain)}Service } from '../../ports/${domain}-service.port';

// HTTP adapter — translates HTTP request/response into domain calls
// ONLY this file should import Express, Fastify, etc.
export class ${pascal(domain)}Controller {
  constructor(private readonly service: ${pascal(domain)}Service) {}

  // async getById(req, res) { ... }
  // async create(req, res) { ... }
}
`,
      },
    ],
  },

  'vertical-slice': {
    description: 'Vertical Slices — each feature owns its full stack',
    dirs: [''],
    files: (domain) => [
      {
        rel: `${domain}.types.ts`,
        content: `// Types owned exclusively by the ${domain} feature slice
export interface ${pascal(domain)} {
  id: string;
  // TODO: add fields
}
`,
      },
      {
        rel: `${domain}.service.ts`,
        content: `import type { ${pascal(domain)} } from './${domain}.types';

// All ${domain} business logic lives here — no imports from other feature slices
export class ${pascal(domain)}Service {
  async get(id: string): Promise<${pascal(domain)} | null> {
    throw new Error('Not implemented');
  }

  async create(data: Omit<${pascal(domain)}, 'id'>): Promise<${pascal(domain)}> {
    throw new Error('Not implemented');
  }
}
`,
      },
      {
        rel: `${domain}.repository.ts`,
        content: `import type { ${pascal(domain)} } from './${domain}.types';

// Data access for ${domain} — DB/ORM calls stay here
export class ${pascal(domain)}Repository {
  async findById(id: string): Promise<${pascal(domain)} | null> {
    throw new Error('Not implemented');
  }

  async save(entity: ${pascal(domain)}): Promise<void> {
    throw new Error('Not implemented');
  }
}
`,
      },
      {
        rel: `${domain}.controller.ts`,
        content: `import { ${pascal(domain)}Service } from './${domain}.service';

// HTTP entry point for the ${domain} slice
export class ${pascal(domain)}Controller {
  constructor(private readonly service: ${pascal(domain)}Service) {}
  // TODO: add route handlers
}
`,
      },
      {
        rel: `${domain}.test.ts`,
        content: `import { ${pascal(domain)}Service } from './${domain}.service';

describe('${pascal(domain)}Service', () => {
  it('TODO: add tests', () => {
    expect(true).toBe(true);
  });
});
`,
      },
    ],
  },

  layered: {
    description: 'Layered — presentation / application / domain / infrastructure',
    dirs: ['presentation', 'application', 'domain', 'infrastructure'],
    files: (domain) => [
      {
        rel: `domain/${domain}.entity.ts`,
        content: `// Domain entity — pure business object, no framework or DB types
export class ${pascal(domain)} {
  constructor(
    public readonly id: string,
    // TODO: add fields
  ) {}
}
`,
      },
      {
        rel: `domain/${domain}.repository.interface.ts`,
        content: `import type { ${pascal(domain)} } from './${domain}.entity';

export interface I${pascal(domain)}Repository {
  findById(id: string): Promise<${pascal(domain)} | null>;
  save(entity: ${pascal(domain)}): Promise<void>;
}
`,
      },
      {
        rel: `application/${domain}.use-cases.ts`,
        content: `import type { I${pascal(domain)}Repository } from '../domain/${domain}.repository.interface';
import type { ${pascal(domain)} } from '../domain/${domain}.entity';

// Application layer: orchestrates domain objects, calls domain repos
export class ${pascal(domain)}UseCases {
  constructor(private readonly repo: I${pascal(domain)}Repository) {}

  async get(id: string): Promise<${pascal(domain)} | null> {
    return this.repo.findById(id);
  }
}
`,
      },
      {
        rel: `infrastructure/${domain}.repository.ts`,
        content: `import type { I${pascal(domain)}Repository } from '../domain/${domain}.repository.interface';
import type { ${pascal(domain)} } from '../domain/${domain}.entity';

// Infrastructure layer — ONLY file that imports ORM/DB
export class ${pascal(domain)}Repository implements I${pascal(domain)}Repository {
  async findById(id: string): Promise<${pascal(domain)} | null> {
    throw new Error('Not implemented');
  }

  async save(entity: ${pascal(domain)}): Promise<void> {
    throw new Error('Not implemented');
  }
}
`,
      },
      {
        rel: `presentation/${domain}.controller.ts`,
        content: `import { ${pascal(domain)}UseCases } from '../application/${domain}.use-cases';

// Presentation layer — HTTP/CLI/GraphQL adapter
export class ${pascal(domain)}Controller {
  constructor(private readonly useCases: ${pascal(domain)}UseCases) {}
}
`,
      },
    ],
  },

  'clean-architecture': {
    description: 'Clean Architecture — enterprise scale, strict dependency rule inward',
    dirs: ['entities', 'use-cases', 'interfaces', 'frameworks'],
    files: (domain) => [
      {
        rel: `entities/${domain}.ts`,
        content: `// Enterprise Business Rules — independent of anything else
export class ${pascal(domain)} {
  constructor(public readonly id: string) {}
}
`,
      },
      {
        rel: `use-cases/${domain}.interactor.ts`,
        content: `import type { ${pascal(domain)} } from '../entities/${domain}';
import type { I${pascal(domain)}Repository } from './${domain}.repository.interface';

// Application Business Rules
export class ${pascal(domain)}Interactor {
  constructor(private readonly repo: I${pascal(domain)}Repository) {}
  
  async execute(id: string): Promise<${pascal(domain)} | null> {
    return this.repo.findById(id);
  }
}
`,
      },
      {
        rel: `use-cases/${domain}.repository.interface.ts`,
        content: `import type { ${pascal(domain)} } from '../entities/${domain}';

export interface I${pascal(domain)}Repository {
  findById(id: string): Promise<${pascal(domain)} | null>;
  save(entity: ${pascal(domain)}): Promise<void>;
}
`,
      },
      {
        rel: `interfaces/${domain}.controller.ts`,
        content: `import type { ${pascal(domain)}Interactor } from '../use-cases/${domain}.interactor';

// Interface Adapters — converts data from format convenient for use cases to format convenient for external agencies
export class ${pascal(domain)}Controller {
  constructor(private readonly interactor: ${pascal(domain)}Interactor) {}
}
`,
      },
      {
        rel: `frameworks/${domain}.repository.ts`,
        content: `import type { I${pascal(domain)}Repository } from '../use-cases/${domain}.repository.interface';
import type { ${pascal(domain)} } from '../entities/${domain}';

// Frameworks & Drivers — lowest level, DB specifics
export class ${pascal(domain)}Repository implements I${pascal(domain)}Repository {
  async findById(id: string): Promise<${pascal(domain)} | null> {
    throw new Error('Not implemented');
  }
  async save(entity: ${pascal(domain)}): Promise<void> {
    throw new Error('Not implemented');
  }
}
`,
      },
    ],
  },

  cqrs: {
    description: 'CQRS — separate read (queries) and write (commands) models',
    dirs: ['commands', 'queries', 'models', 'events'],
    files: (domain) => [
      {
        rel: `models/${domain}.write-model.ts`,
        content: `// Write Model — optimized for domain logic and invariants
export class ${pascal(domain)}WriteModel {
  constructor(public readonly id: string) {}
}
`,
      },
      {
        rel: `models/${domain}.read-model.ts`,
        content: `// Read Model — optimized for queries, can be denormalized or flat
export interface ${pascal(domain)}ReadModel {
  id: string;
  // fast lookup fields
}
`,
      },
      {
        rel: `commands/create-${domain}.command.ts`,
        content: `// Command — intent to mutate state
export class Create${pascal(domain)}Command {
  constructor(public readonly payload: any) {}
}

export class Create${pascal(domain)}Handler {
  async handle(command: Create${pascal(domain)}Command): Promise<void> {
    // 1. Load write model
    // 2. Execute logic
    // 3. Save write model
    // 4. Dispatch event
  }
}
`,
      },
      {
        rel: `queries/get-${domain}.query.ts`,
        content: `import type { ${pascal(domain)}ReadModel } from '../models/${domain}.read-model';

// Query — intent to read state without mutating
export class Get${pascal(domain)}Query {
  constructor(public readonly id: string) {}
}

export class Get${pascal(domain)}Handler {
  async handle(query: Get${pascal(domain)}Query): Promise<${pascal(domain)}ReadModel | null> {
    // Read directly from DB or fast read replica, NO domain logic here
    return null;
  }
}
`,
      },
      {
        rel: `events/${domain}-created.event.ts`,
        content: `// Domain Event — a fact that occurred
export class ${pascal(domain)}CreatedEvent {
  constructor(public readonly id: string, public readonly payload: any) {}
}
`,
      },
    ],
  },
};

function pascal(str) {
  return str
    .split(/[-_\s]+/)
    .filter(Boolean) // drop empties from leading/trailing/doubled separators
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join('');
}

function scaffold(domain, pattern, outputDir, force = false) {
  const def = PATTERNS[pattern];
  if (!def) {
    console.error(`Unknown pattern: ${pattern}. Available: ${Object.keys(PATTERNS).join(', ')}`);
    process.exit(1);
  }

  const baseDir = path.resolve(outputDir, domain);
  console.log(`\nScaffolding "${pattern}" boundary for domain "${domain}"`);
  console.log(`Output: ${baseDir}\n`);

  // Create directories
  for (const dir of def.dirs) {
    const d = dir ? path.join(baseDir, dir) : baseDir;
    fs.mkdirSync(d, { recursive: true });
  }

  // Write files
  for (const { rel, content } of def.files(domain)) {
    const filePath = path.join(baseDir, rel);
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    if (fs.existsSync(filePath) && !force) {
      console.warn(
        `  skipped  ${path.relative(process.cwd(), filePath)} (exists; use --force to overwrite)`,
      );
      continue;
    }
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`  created  ${path.relative(process.cwd(), filePath)}`);
  }

  console.log(`\nDone. Pattern: ${def.description}`);
  console.log('Next steps:');
  console.log('  1. Fill in the TODO fields in the domain entity.');
  console.log('  2. Implement the repository adapter with your ORM/DB.');
  console.log('  3. Wire up the controller in your framework router.');
  console.log(
    '  4. Run the Swap Test: could you replace the DB adapter without touching domain files?',
  );
}

// CLI entry point
if (
  process.argv[1] &&
  (process.argv[1] === new URL(import.meta.url).pathname ||
    process.argv[1].endsWith('scaffold-boundary.mjs'))
) {
  const args = process.argv.slice(2).filter((a) => a !== '--force');
  const force = process.argv.includes('--force');
  const domain = args[0];
  const pattern = args[1] || 'hexagonal';
  const outputDir = args[2] || 'src';

  if (!domain) {
    console.error('Usage: node scaffold-boundary.mjs <domain> [pattern] [output-dir] [--force]');
    console.error(`Patterns: ${Object.keys(PATTERNS).join(', ')}`);
    process.exit(1);
  }

  scaffold(domain, pattern, path.resolve(process.cwd(), outputDir), force);
}
