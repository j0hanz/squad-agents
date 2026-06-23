import os
import sys
import re

PATTERNS = {
    "hexagonal": {
        "description": "Ports & Adapters — domain isolated from all infrastructure",
        "dirs": ["domain", "ports", "adapters/infra", "adapters/http"],
        "files": lambda domain, pascal_name: [
            {
                "rel": f"domain/{domain}.ts",
                "content": f"// Core domain entity — no infrastructure imports allowed here\nexport interface {pascal_name} {{\n  id: string;\n  // TODO: add domain fields\n}}\n",
            },
            {
                "rel": f"ports/{domain}-repository.port.ts",
                "content": f"import type {{ {pascal_name} }} from '../domain/{domain}';\n\n// Inbound port — what the domain exposes to the outside world\nexport interface {pascal_name}Repository {{\n  findById(id: string): Promise<{pascal_name} | null>;\n  save(entity: {pascal_name}): Promise<void>;\n  delete(id: string): Promise<void>;\n}}\n",
            },
            {
                "rel": f"ports/{domain}-service.port.ts",
                "content": f"import type {{ {pascal_name} }} from '../domain/{domain}';\n\n// Outbound port — what the application layer calls\nexport interface {pascal_name}Service {{\n  get(id: string): Promise<{pascal_name} | null>;\n  create(data: Omit<{pascal_name}, 'id'>): Promise<{pascal_name}>;\n}}\n",
            },
            {
                "rel": f"adapters/infra/{domain}-repository.adapter.ts",
                "content": f"import type {{ {pascal_name}Repository }} from '../../ports/{domain}-repository.port';\nimport type {{ {pascal_name} }} from '../../domain/{domain}';\n\n// Infrastructure adapter — implements the port using your DB/ORM\n// ONLY this file should import Prisma, TypeORM, SQLAlchemy, etc.\nexport class {pascal_name}RepositoryAdapter implements {pascal_name}Repository {{\n  async findById(id: string): Promise<{pascal_name} | null> {{\n    throw new Error('Not implemented');\n  }}\n\n  async save(entity: {pascal_name}): Promise<void> {{\n    throw new Error('Not implemented');\n  }}\n\n  async delete(id: string): Promise<void> {{\n    throw new Error('Not implemented');\n  }}\n}}\n",
            },
            {
                "rel": f"adapters/http/{domain}.controller.ts",
                "content": f"import type {{ {pascal_name}Service }} from '../../ports/{domain}-service.port';\n\n// HTTP adapter — translates HTTP request/response into domain calls\n// ONLY this file should import Express, Fastify, etc.\nexport class {pascal_name}Controller {{\n  constructor(private readonly service: {pascal_name}Service) {{}}\n\n  // async getById(req, res) {{ ... }}\n  // async create(req, res) {{ ... }}\n}}\n",
            },
        ],
    },
    "vertical-slice": {
        "description": "Vertical Slices — each feature owns its full stack",
        "dirs": [""],
        "files": lambda domain, pascal_name: [
            {
                "rel": f"{domain}.types.ts",
                "content": f"// Types owned exclusively by the {domain} feature slice\nexport interface {pascal_name} {{\n  id: string;\n  // TODO: add fields\n}}\n",
            },
            {
                "rel": f"{domain}.service.ts",
                "content": f"import type {{ {pascal_name} }} from './{domain}.types';\n\n// All {domain} business logic lives here — no imports from other feature slices\nexport class {pascal_name}Service {{\n  async get(id: string): Promise<{pascal_name} | null> {{\n    throw new Error('Not implemented');\n  }}\n\n  async create(data: Omit<{pascal_name}, 'id'>): Promise<{pascal_name}> {{\n    throw new Error('Not implemented');\n  }}\n}}\n",
            },
            {
                "rel": f"{domain}.repository.ts",
                "content": f"import type {{ {pascal_name} }} from './{domain}.types';\n\n// Data access for {domain} — DB/ORM calls stay here\nexport class {pascal_name}Repository {{\n  async findById(id: string): Promise<{pascal_name} | null> {{\n    throw new Error('Not implemented');\n  }}\n\n  async save(entity: {pascal_name}): Promise<void> {{\n    throw new Error('Not implemented');\n  }}\n}}\n",
            },
            {
                "rel": f"{domain}.controller.ts",
                "content": f"import {{ {pascal_name}Service }} from './{domain}.service';\n\n// HTTP entry point for the {domain} slice\nexport class {pascal_name}Controller {{\n  constructor(private readonly service: {pascal_name}Service) {{}}\n  // TODO: add route handlers\n}}\n",
            },
            {
                "rel": f"{domain}.test.ts",
                "content": f"import {{ {pascal_name}Service }} from './{domain}.service';\n\ndescribe('{pascal_name}Service', () => {{\n  it('TODO: add tests', () => {{\n    expect(true).toBe(true);\n  }});\n}});\n",
            },
        ],
    },
    "layered": {
        "description": "Layered — presentation / application / domain / infrastructure",
        "dirs": ["presentation", "application", "domain", "infrastructure"],
        "files": lambda domain, pascal_name: [
            {
                "rel": f"domain/{domain}.entity.ts",
                "content": f"// Domain entity — pure business object, no framework or DB types\nexport class {pascal_name} {{\n  constructor(\n    public readonly id: string,\n    // TODO: add fields\n  ) {{}}\n}}\n",
            },
            {
                "rel": f"domain/{domain}.repository.interface.ts",
                "content": f"import type {{ {pascal_name} }} from './{domain}.entity';\n\nexport interface I{pascal_name}Repository {{\n  findById(id: string): Promise<{pascal_name} | null>;\n  save(entity: {pascal_name}): Promise<void>;\n}}\n",
            },
            {
                "rel": f"application/{domain}.use-cases.ts",
                "content": f"import type {{ I{pascal_name}Repository }} from '../domain/{domain}.repository.interface';\nimport type {{ {pascal_name} }} from '../domain/{domain}.entity';\n\n// Application layer: orchestrates domain objects, calls domain repos\nexport class {pascal_name}UseCases {{\n  constructor(private readonly repo: I{pascal_name}Repository) {{}}\n\n  async get(id: string): Promise<{pascal_name} | null> {{\n    return this.repo.findById(id);\n  }}\n}}\n",
            },
            {
                "rel": f"infrastructure/{domain}.repository.ts",
                "content": f"import type {{ I{pascal_name}Repository }} from '../domain/{domain}.repository.interface';\nimport type {{ {pascal_name} }} from '../domain/{domain}.entity';\n\n// Infrastructure layer — ONLY file that imports ORM/DB\nexport class {pascal_name}Repository implements I{pascal_name}Repository {{\n  async findById(id: string): Promise<{pascal_name} | null> {{\n    throw new Error('Not implemented');\n  }}\n\n  async save(entity: {pascal_name}): Promise<void> {{\n    throw new Error('Not implemented');\n  }}\n}}\n",
            },
            {
                "rel": f"presentation/{domain}.controller.ts",
                "content": f"import {{ {pascal_name}UseCases }} from '../application/{domain}.use-cases';\n\n// Presentation layer — HTTP/CLI/GraphQL adapter\nexport class {pascal_name}Controller {{\n  constructor(private readonly useCases: {pascal_name}UseCases) {{}}\n}}\n",
            },
        ],
    },
    "clean-architecture": {
        "description": "Clean Architecture — enterprise scale, strict dependency rule inward",
        "dirs": ["entities", "use-cases", "interfaces", "frameworks"],
        "files": lambda domain, pascal_name: [
            {
                "rel": f"entities/{domain}.ts",
                "content": f"// Enterprise Business Rules — independent of anything else\nexport class {pascal_name} {{\n  constructor(public readonly id: string) {{}}\n}}\n",
            },
            {
                "rel": f"use-cases/{domain}.interactor.ts",
                "content": f"import type {{ {pascal_name} }} from '../entities/{domain}';\nimport type {{ I{pascal_name}Repository }} from './{domain}.repository.interface';\n\n// Application Business Rules\nexport class {pascal_name}Interactor {{\n  constructor(private readonly repo: I{pascal_name}Repository) {{}}\n  \n  async execute(id: string): Promise<{pascal_name} | null> {{\n    return this.repo.findById(id);\n  }}\n}}\n",
            },
            {
                "rel": f"use-cases/{domain}.repository.interface.ts",
                "content": f"import type {{ {pascal_name} }} from '../entities/{domain}';\n\nexport interface I{pascal_name}Repository {{\n  findById(id: string): Promise<{pascal_name} | null>;\n  save(entity: {pascal_name}): Promise<void>;\n}}\n",
            },
            {
                "rel": f"interfaces/{domain}.controller.ts",
                "content": f"import type {{ {pascal_name}Interactor }} from '../use-cases/{domain}.interactor';\n\n// Interface Adapters — converts data from format convenient for use cases to format convenient for external agencies\nexport class {pascal_name}Controller {{\n  constructor(private readonly interactor: {pascal_name}Interactor) {{}}\n}}\n",
            },
            {
                "rel": f"frameworks/{domain}.repository.ts",
                "content": f"import type {{ I{pascal_name}Repository }} from '../use-cases/{domain}.repository.interface';\nimport type {{ {pascal_name} }} from '../entities/{domain}';\n\n// Frameworks & Drivers — lowest level, DB specifics\nexport class {pascal_name}Repository implements I{pascal_name}Repository {{\n  async findById(id: string): Promise<{pascal_name} | null> {{\n    throw new Error('Not implemented');\n  }}\n  async save(entity: {pascal_name}): Promise<void> {{\n    throw new Error('Not implemented');\n  }}\n}}\n",
            },
        ],
    },
    "cqrs": {
        "description": "CQRS — separate read (queries) and write (commands) models",
        "dirs": ["commands", "queries", "models", "events"],
        "files": lambda domain, pascal_name: [
            {
                "rel": f"models/{domain}.write-model.ts",
                "content": f"// Write Model — optimized for domain logic and invariants\nexport class {pascal_name}WriteModel {{\n  constructor(public readonly id: string) {{}}\n}}\n",
            },
            {
                "rel": f"models/{domain}.read-model.ts",
                "content": f"// Read Model — optimized for queries, can be denormalized or flat\nexport interface {pascal_name}ReadModel {{\n  id: string;\n  // fast lookup fields\n}}\n",
            },
            {
                "rel": f"commands/create-{domain}.command.ts",
                "content": f"// Command — intent to mutate state\nexport class Create{pascal_name}Command {{\n  constructor(public readonly payload: any) {{}}\n}}\n\nexport class Create{pascal_name}Handler {{\n  async handle(command: Create{pascal_name}Command): Promise<void> {{\n    // 1. Load write model\n    // 2. Execute logic\n    // 3. Save write model\n    // 4. Dispatch event\n  }}\n}}\n",
            },
            {
                "rel": f"queries/get-{domain}.query.ts",
                "content": f"import type {{ {pascal_name}ReadModel }} from '../models/{domain}.read-model';\n\n// Query — intent to read state without mutating\nexport class Get{pascal_name}Query {{\n  constructor(public readonly id: string) {{}}\n}}\n\nexport class Get{pascal_name}Handler {{\n  async handle(query: Get{pascal_name}Query): Promise<{pascal_name}ReadModel | null> {{\n    // Read directly from DB or fast read replica, NO domain logic here\n    return null;\n  }}\n}}\n",
            },
            {
                "rel": f"events/{domain}-created.event.ts",
                "content": f"// Domain Event — a fact that occurred\nexport class {pascal_name}CreatedEvent {{\n  constructor(public readonly id: string, public readonly payload: any) {{}}\n}}\n",
            },
        ],
    },
}


def to_pascal(s: str) -> str:
    words = re.split(r"[-_\s]+", s)
    return "".join(w.capitalize() for w in words if w)


_SAFE_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _require_within(parent: str, child: str, error_msg: str) -> None:
    try:
        within = os.path.commonpath([parent, child]) == parent
    except ValueError:
        # e.g. paths on different drives/UNC roots on Windows
        within = False
    if not within:
        print(error_msg, file=sys.stderr)
        sys.exit(1)


def scaffold(domain: str, pattern: str, output_dir: str, force: bool = False) -> None:
    if not _SAFE_DOMAIN_RE.match(domain):
        print(
            f"Invalid domain: {domain!r}. Domain must match {_SAFE_DOMAIN_RE.pattern} "
            "(no path separators or traversal segments).",
            file=sys.stderr,
        )
        sys.exit(1)

    if pattern not in PATTERNS:
        print(
            f"Unknown pattern: {pattern}. Available: {', '.join(PATTERNS.keys())}",
            file=sys.stderr,
        )
        sys.exit(1)

    def_pattern = PATTERNS[pattern]
    out_root = os.path.abspath(output_dir)
    _require_within(
        os.getcwd(),
        out_root,
        f"Refusing to scaffold outside the current directory: {out_root}",
    )
    base_dir = os.path.abspath(os.path.join(out_root, domain))
    _require_within(
        out_root,
        base_dir,
        f"Refusing to scaffold outside output_dir: {base_dir}",
    )
    pascal_name = to_pascal(domain)

    print(f'\nScaffolding "{pattern}" boundary for domain "{domain}"')
    print(f"Output: {base_dir}\n")

    # Create directories
    for d in def_pattern["dirs"]:
        dir_path = os.path.join(base_dir, d) if d else base_dir
        os.makedirs(dir_path, exist_ok=True)

    # Write files
    for f_info in def_pattern["files"](domain, pascal_name):
        file_path = os.path.join(base_dir, f_info["rel"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if os.path.exists(file_path) and not force:
            rel_p = os.path.relpath(file_path, os.getcwd())
            print(f"  skipped  {rel_p} (exists; use --force to overwrite)")
            continue

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f_info["content"])

        rel_p = os.path.relpath(file_path, os.getcwd())
        print(f"  created  {rel_p}")

    print(f"\nDone. Pattern: {def_pattern['description']}")
    print("Next steps:")
    print("  1. Fill in the TODO fields in the domain entity.")
    print("  2. Implement the repository adapter with your ORM/DB.")
    print("  3. Wire up the controller in your framework router.")
    print(
        "  4. Run the Swap Test: could you replace the DB adapter without touching domain files?"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scaffold a new domain boundary.")
    parser.add_argument("domain", help="Domain name (e.g. user-profile)")
    parser.add_argument(
        "pattern", nargs="?", default="hexagonal", help="Architectural pattern"
    )
    parser.add_argument(
        "output_dir", nargs="?", default="src", help="Output base directory"
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")

    args = parser.parse_args()

    scaffold(args.domain, args.pattern, args.output_dir, args.force)
