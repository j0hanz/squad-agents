#!/usr/bin/env python3
"""
Consolidated health check script for the agent-dev plugin.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --- Constants & Configuration ---
DEPENDENCY_DIRS: dict[str, str] = {
    "node_modules": "Node.js (npm/pnpm/yarn/bun)",
    "venv": "Python (virtualenv)",
    ".venv": "Python (virtualenv)",
    "env": "Python (virtualenv)",
    ".env": "Python (virtualenv)",
    "__pypackages__": "Python (PEP 582)",
    ".direnv": "direnv",
    ".conda": "Conda environment",
    "vendor": "PHP (Composer) / Go (vendoring)",
    "Pods": "iOS (CocoaPods)",
    "target": "Rust (Cargo)",
    "dist": "Build output",
    "build": "Build output",
    ".next": "Next.js build",
    "out": "Build output",
    "bin": "Executables / scripts",
    "lib": "Shared libraries / dependencies",
    "extern": "External dependencies",
}

PACKAGE_MANAGERS: dict[str, str] = {
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "package-lock.json": "npm",
    "bun.lockb": "bun",
    "uv.lock": "uv",
    "poetry.lock": "poetry",
    "Cargo.lock": "cargo",
    "go.sum": "go",
}

DEFAULT_IGNORE_PATTERNS: set[str] = {
    ".git",
    ".vscode",
    ".idea",
    ".env",
    "*.log",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
}


@dataclass
class ProjectEnvironment:
    """DTO for the project environment."""

    package_manager: str = "Unknown"
    test_runner: str = "Unknown"
    linter: str = "Unknown"
    is_monorepo: bool = False


@dataclass
class DependencyInfo:
    """DTO for found dependencies."""

    name: str
    type: str
    path: str
    size_mb: float | str


@dataclass
class AuditResults:
    """Consolidated results of the plugin audit."""

    structure: list[str] = field(default_factory=list)
    env: ProjectEnvironment = field(default_factory=ProjectEnvironment)
    dependencies: list[DependencyInfo] = field(default_factory=list)
    skills_valid: bool = True
    skills_errors: list[str] = field(default_factory=list)
    agents_md_valid: bool = True
    agents_md_errors: list[str] = field(default_factory=list)
    hooks_valid: bool = True
    hooks_errors: list[str] = field(default_factory=list)
    manifest_valid: bool = True
    manifest_errors: list[str] = field(default_factory=list)


# --- Utility Functions ---


def load_gitignore(target_dir: Path) -> set[str]:
    """Load ignore patterns from .gitignore file."""
    patterns: set[str] = set()
    gitignore_file = target_dir / ".gitignore"

    if gitignore_file.exists():
        try:
            content = gitignore_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line.rstrip("/"))
        except (OSError, UnicodeDecodeError):
            # Log specific error if needed, but don't crash
            pass

    return patterns


def should_ignore(path: Path, patterns: set[str], root: Path) -> bool:
    """Check if a path should be ignored based on patterns."""
    try:
        rel_path = path.relative_to(root)
    except ValueError:
        return False

    rel_str = str(rel_path).replace("\\", "/")
    for pattern in patterns:
        if rel_str == pattern or rel_str.startswith(pattern + "/"):
            return True
        if "*" in pattern:
            if fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch(
                rel_str, pattern + "/*"
            ):
                return True

    return False


def _parse_frontmatter(content: str) -> dict[str, str]:
    """Simple parser for YAML frontmatter."""
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end == -1:
        return {}
    yaml_text = content[3:end]
    result: dict[str, str] = {}
    for line in yaml_text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


# --- Core Logic (Discovery/Analysis) ---


def get_tree_lines(
    target_dir: Path, patterns: set[str], max_depth: int = 3
) -> list[str]:
    """Generate directory tree lines without printing."""
    lines: list[str] = []
    use_unicode = True
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "└".encode(encoding)
    except (UnicodeEncodeError, LookupError):
        use_unicode = False

    branch_last = "└── " if use_unicode else "+-- "
    branch_mid = "├── " if use_unicode else "|-- "
    spacer_last = "    "
    spacer_mid = "│   " if use_unicode else "|   "

    def build_tree(path: Path, prefix: str = "", depth: int = 0) -> None:
        if depth > max_depth:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except (PermissionError, OSError):
            return

        non_ignored = [
            entry for entry in entries if not should_ignore(entry, patterns, target_dir)
        ]

        for i, entry in enumerate(non_ignored):
            is_last = i == len(non_ignored) - 1
            current = branch_last if is_last else branch_mid
            extension = spacer_last if is_last else spacer_mid

            if entry.is_dir():
                lines.append(f"{prefix}{current}{entry.name}/")
                build_tree(entry, prefix + extension, depth + 1)
            else:
                lines.append(f"{prefix}{current}{entry.name}")

    build_tree(target_dir)
    return lines


def analyze_project_env(target_dir: Path) -> ProjectEnvironment:
    """Analyze the project environment files."""
    env = ProjectEnvironment()
    try:
        files = [entry.name for entry in target_dir.iterdir() if entry.is_file()]
    except (PermissionError, OSError):
        return env

    for lockfile, pm in PACKAGE_MANAGERS.items():
        if lockfile in files:
            env.package_manager = pm
            break

    if any(name.startswith("jest.config") for name in files):
        env.test_runner = "jest"
    elif any(name.startswith("vitest.config") for name in files):
        env.test_runner = "vitest"
    elif "pytest.ini" in files:
        env.test_runner = "pytest"

    if any(name.startswith(".eslintrc") for name in files):
        env.linter = "eslint"
    elif "biome.json" in files:
        env.linter = "biome"
    elif "ruff.toml" in files:
        env.linter = "ruff"

    monorepo_markers = {"turbo.json", "pnpm-workspace.yaml", "nx.json", "lerna.json"}
    if any(name in files for name in monorepo_markers):
        env.is_monorepo = True

    package_json = target_dir / "package.json"
    if package_json.exists():
        try:
            pkg: dict[str, Any] = json.loads(package_json.read_text(encoding="utf-8"))
            scripts = pkg.get("scripts", {})
            if env.test_runner == "Unknown" and scripts.get("test"):
                env.test_runner = "See package.json test script"
            if env.linter == "Unknown" and scripts.get("lint"):
                env.linter = "See package.json lint script"
        except (json.JSONDecodeError, OSError):
            pass

    return env


def get_dependencies(target_dir: Path) -> list[DependencyInfo]:
    """Find and measure installed dependencies."""
    found: list[DependencyInfo] = []

    try:
        dirs = [e for e in target_dir.iterdir() if e.is_dir()]
    except (PermissionError, OSError):
        return found

    for entry in dirs:
        if entry.name in DEPENDENCY_DIRS:
            try:
                size_mb = 0.0
                count = 0
                for f in entry.rglob("*"):
                    if f.is_file():
                        size_mb += f.stat().st_size
                        count += 1
                        if count > 10000:
                            break
                size_mb /= 1024 * 1024

                found.append(
                    DependencyInfo(
                        name=entry.name,
                        type=DEPENDENCY_DIRS[entry.name],
                        path=str(entry.relative_to(target_dir)),
                        size_mb=round(size_mb, 1)
                        if count <= 10000
                        else f">{round(size_mb, 1)}",
                    )
                )
            except (PermissionError, OSError):
                found.append(
                    DependencyInfo(
                        name=entry.name,
                        type=DEPENDENCY_DIRS[entry.name],
                        path=str(entry.relative_to(target_dir)),
                        size_mb="unknown",
                    )
                )

    return found


def validate_skill_files(skills_dir: Path) -> tuple[bool, list[str]]:
    """Validate all SKILL.md files in the skills directory."""
    if not skills_dir.exists():
        return False, [f"Skills directory not found: {skills_dir}"]

    errors: list[str] = []
    REQUIRED_KEYS = ("name", "description", "disable-model-invocation")

    try:
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
    except (PermissionError, OSError) as e:
        return False, [f"Failed to list skills directory: {e}"]

    for skill_dir in sorted(skill_dirs):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            errors.append(f"{skill_dir.name}/ has no SKILL.md")
            continue

        try:
            content = skill_file.read_text(encoding="utf-8")
            fm = _parse_frontmatter(content)

            for key in REQUIRED_KEYS:
                if key not in fm:
                    errors.append(
                        f"{skill_dir.name}/SKILL.md missing frontmatter key: '{key}'"
                    )

            if len(content.splitlines()) > 150:
                # Using a pseudo-error/warn list
                errors.append(f"WARN: {skill_dir.name}/SKILL.md is long (>150 lines)")
        except (OSError, UnicodeDecodeError) as e:
            errors.append(f"Failed to read {skill_file}: {e}")

    return len([e for e in errors if not e.startswith("WARN")]) == 0, errors


def validate_agents_md_file(file_path: Path) -> tuple[bool, list[str]]:
    """Validate the AGENTS.md file."""
    if not file_path.exists():
        return False, [f"File not found at {file_path}"]

    errors: list[str] = []
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        if len(lines) > 100:
            errors.append(f"File is {len(lines)} lines. Must be under 100.")

        if not lines or not lines[0].startswith("# "):
            errors.append("File must start with an H1 header.")

        filler_regex = re.compile(
            r"(welcome to|this document explains|you should)", re.IGNORECASE
        )
        auto_discovery_regex = re.compile(
            r"(\d+\s+(tools|resources|prompts)|MCP server)", re.IGNORECASE
        )
        generic_advice_regex = re.compile(
            r"\b(always|be sure|remember|carefully|thoroughly|best practice|make sure|important|test thoroughly|be careful)\b",
            re.IGNORECASE,
        )

        for index, line in enumerate(lines):
            if filler_regex.search(line):
                errors.append(
                    f'Line {index + 1} contains filler text: "{line.strip()}"'
                )
            if auto_discovery_regex.search(line):
                errors.append(
                    f'Line {index + 1} lists auto-discovered tools: "{line.strip()}"'
                )
            if generic_advice_regex.search(line):
                errors.append(
                    f'WARN: Line {index + 1} contains generic advice: "{line.strip()}"'
                )

        if "Co-Authored-By:" not in content:
            errors.append('Missing "Co-Authored-By:" attribution.')

        if (
            "## File-scoped commands" not in content
            and "| Tool | File | Command |" not in content
        ):
            errors.append('Missing mandatory "File-scoped commands" table.')
    except (OSError, UnicodeDecodeError) as e:
        errors.append(f"Failed to read {file_path}: {e}")

    return len([e for e in errors if not e.startswith("WARN")]) == 0, errors


def validate_hooks_config(hooks_file: Path) -> tuple[bool, list[str]]:
    """Validate hooks.json and existence of handlers."""
    if not hooks_file.exists():
        return False, [f"hooks.json not found at {hooks_file}"]

    errors: list[str] = []
    try:
        hooks_data = json.loads(hooks_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return False, [f"Failed to parse hooks.json: {e}"]

    plugin_root = hooks_file.parent.parent

    for event, event_hooks in hooks_data.get("hooks", {}).items():
        for hook_entry in event_hooks:
            for hook in hook_entry.get("hooks", []):
                cmd = hook.get("command", "")
                if not cmd:
                    continue

                if "runner.mjs" in cmd:
                    parts = cmd.split()
                    try:
                        domain_idx = parts.index("runner.mjs") + 1
                        domain = parts[domain_idx]
                        handler_path = (
                            plugin_root / "hooks" / "handlers" / f"{domain}.mjs"
                        )
                        if not handler_path.exists():
                            errors.append(
                                f"Missing handler for hook '{event}': {handler_path}"
                            )
                    except (ValueError, IndexError):
                        pass

                elif "scripts" in cmd:
                    script_path_str = cmd.split()[-1].replace(
                        "${CLAUDE_PLUGIN_ROOT}", str(plugin_root)
                    )
                    if not Path(script_path_str).exists():
                        errors.append(
                            f"Missing script for hook '{event}': {script_path_str}"
                        )

    return len(errors) == 0, errors


def validate_manifest_file(manifest_file: Path) -> tuple[bool, list[str]]:
    """Validate plugin.json manifest."""
    if not manifest_file.exists():
        return False, [f"plugin.json not found at {manifest_file}"]

    errors: list[str] = []
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        required = ["name", "version", "description"]
        for key in required:
            if key not in data:
                errors.append(f"Manifest missing required key: '{key}'")
    except (json.JSONDecodeError, OSError) as e:
        return False, [f"Failed to parse plugin.json: {e}"]

    return len(errors) == 0, errors


# --- Reporting ---


def print_audit_report(root_dir: Path, results: AuditResults) -> int:
    """Print the final formatted audit report."""
    print(f"## Full Plugin Health Audit: {root_dir.name}\n")

    print(f"### Directory Structure ({root_dir.name})")
    print("```")
    for line in results.structure:
        print(line)
    print("```\n")

    print("### Project Environment")
    print(f"- **Package Manager:** {results.env.package_manager}")
    print(f"- **Test Runner:** {results.env.test_runner}")
    print(f"- **Linter/Formatter:** {results.env.linter}")
    print(f"- **Monorepo:** {'Yes' if results.env.is_monorepo else 'No'}\n")

    if results.dependencies:
        print("### Installed Dependencies")
        for dep in results.dependencies:
            size_str = (
                f"{dep.size_mb} MB"
                if isinstance(dep.size_mb, (int, float))
                else dep.size_mb
            )
            print(f"- **{dep.name}** ({dep.type}) → `{dep.path}` [{size_str}]")
    else:
        print("### Installed Dependencies")
        print("- None detected in root directory.")
    print("")

    # Skill validation
    print(f"### Validating Skills in {root_dir / 'skills'}")
    if not results.skills_errors:
        print("PASS: All skills have valid frontmatter.")
    else:
        for err in results.skills_errors:
            print(
                f"{'WARN' if err.startswith('WARN') else 'FAIL'}: {err}",
                file=sys.stderr,
            )
    print("")

    # AGENTS.md validation
    print(f"### Linting {root_dir / 'AGENTS.md'}")
    if not results.agents_md_errors:
        print(f"PASS: {root_dir / 'AGENTS.md'} looks correct.")
    else:
        for err in results.agents_md_errors:
            print(
                f"{'WARN' if err.startswith('WARN') else 'FAIL'}: {err}",
                file=sys.stderr,
            )
    print("")

    # Hooks validation
    print(f"### Validating Hooks in {root_dir / 'hooks' / 'hooks.json'}")
    if not results.hooks_errors:
        print("PASS: Hook configuration and handlers are valid.")
    else:
        for err in results.hooks_errors:
            print(f"FAIL: {err}", file=sys.stderr)
    print("")

    # Manifest validation
    print(f"### Validating Manifest in {root_dir / '.claude-plugin' / 'plugin.json'}")
    if not results.manifest_errors:
        print("PASS: Manifest is valid.")
    else:
        for err in results.manifest_errors:
            print(f"FAIL: {err}", file=sys.stderr)

    print("\n## Audit Summary")
    if any(
        [
            not results.skills_valid,
            not results.agents_md_valid,
            not results.hooks_valid,
            not results.manifest_valid,
        ]
    ):
        print("❌ Audit failed with one or more errors.")
        return 1
    print("✅ Audit passed. Plugin is healthy.")
    return 0


def run_full_audit(root_dir: Path) -> int:
    """Orchestrate the full audit process."""
    results = AuditResults()
    patterns = load_gitignore(root_dir) | DEFAULT_IGNORE_PATTERNS

    results.structure = get_tree_lines(root_dir, patterns)
    results.env = analyze_project_env(root_dir)
    results.dependencies = get_dependencies(root_dir)
    results.skills_valid, results.skills_errors = validate_skill_files(
        root_dir / "skills"
    )
    results.agents_md_valid, results.agents_md_errors = validate_agents_md_file(
        root_dir / "AGENTS.md"
    )
    results.hooks_valid, results.hooks_errors = validate_hooks_config(
        root_dir / "hooks" / "hooks.json"
    )
    results.manifest_valid, results.manifest_errors = validate_manifest_file(
        root_dir / ".claude-plugin" / "plugin.json"
    )

    return print_audit_report(root_dir, results)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Consolidated plugin maintenance utilities."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("check-all", help="Run all health checks.")
    subparsers.add_parser(
        "check-hooks", help="Validate hook configuration and handlers."
    )
    subparsers.add_parser("check-manifest", help="Validate plugin manifest.")
    subparsers.add_parser("validate-skills", help="Check SKILL.md frontmatter.")
    lint_parser = subparsers.add_parser("lint-agents-md", help="Validate AGENTS.md.")
    lint_parser.add_argument(
        "file_path", type=Path, nargs="?", default=Path("AGENTS.md")
    )

    subparsers.add_parser("analyze-env", help="Detect project environment.")
    subparsers.add_parser("scan-structure", help="Show directory structure.")

    args = parser.parse_args()
    root = Path(".").resolve()

    match args.command:
        case "check-all":
            return run_full_audit(root)
        case "check-hooks":
            valid, errors = validate_hooks_config(root / "hooks" / "hooks.json")
            for err in errors:
                print(f"FAIL: {err}", file=sys.stderr)
            if valid:
                print("PASS: Hooks are valid.")
            return 0 if valid else 1
        case "check-manifest":
            valid, errors = validate_manifest_file(
                root / ".claude-plugin" / "plugin.json"
            )
            for err in errors:
                print(f"FAIL: {err}", file=sys.stderr)
            if valid:
                print("PASS: Manifest is valid.")
            return 0 if valid else 1
        case "validate-skills":
            valid, errors = validate_skill_files(root / "skills")
            for err in errors:
                print(f"FAIL: {err}", file=sys.stderr)
            if valid:
                print("PASS: Skills are valid.")
            return 0 if valid else 1
        case "lint-agents-md":
            valid, errors = validate_agents_md_file(args.file_path)
            for err in errors:
                print(f"FAIL: {err}", file=sys.stderr)
            if valid:
                print("PASS: AGENTS.md is valid.")
            return 0 if valid else 1
        case "analyze-env":
            env = analyze_project_env(root)
            print(f"Env: {env}")
            return 0
        case "scan-structure":
            patterns = load_gitignore(root) | DEFAULT_IGNORE_PATTERNS
            lines = get_tree_lines(root, patterns)
            for line in lines:
                print(line)
            return 0
        case _:
            return 1


if __name__ == "__main__":
    sys.exit(main())
