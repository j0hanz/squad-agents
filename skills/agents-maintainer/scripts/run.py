#!/usr/bin/env python3
"""
Consolidated health check script for the agent-dev plugin.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Set, Any

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


# --- Utility Functions ---


def load_gitignore(target_dir: Path) -> Set[str]:
    patterns: Set[str] = set()
    gitignore_file = target_dir / ".gitignore"

    if gitignore_file.exists():
        try:
            for line in gitignore_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line.rstrip("/"))
        except (OSError, UnicodeDecodeError):
            pass

    return patterns


def should_ignore(path: Path, patterns: Set[str], root: Path) -> bool:
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


# --- Core Commands ---


def scan_structure(target_dir: Path, max_depth: int = 3) -> int:
    target_dir = target_dir.resolve()
    patterns = load_gitignore(target_dir) | DEFAULT_IGNORE_PATTERNS

    use_unicode = True
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "└".encode(encoding)
    except Exception:
        use_unicode = False

    branch_last = "└── " if use_unicode else "+-- "
    branch_mid = "├── " if use_unicode else "|-- "
    spacer_last = "    "
    spacer_mid = "│   " if use_unicode else "|   "

    def print_tree(path: Path, prefix: str = "", depth: int = 0) -> None:
        if depth > max_depth:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return

        non_ignored = [
            entry for entry in entries if not should_ignore(entry, patterns, target_dir)
        ]

        for i, entry in enumerate(non_ignored):
            is_last = i == len(non_ignored) - 1
            current = branch_last if is_last else branch_mid
            extension = spacer_last if is_last else spacer_mid

            if entry.is_dir():
                print(f"{prefix}{current}{entry.name}/")
                print_tree(entry, prefix + extension, depth + 1)
            else:
                print(f"{prefix}{current}{entry.name}")

    display_name = target_dir.name or target_dir.resolve().name
    print(f"### Directory Structure ({display_name})")
    print("```")
    print_tree(target_dir)
    print("```")
    return 0


def analyze_env(target_dir: Path) -> int:
    env = ProjectEnvironment()
    files = [entry.name for entry in target_dir.iterdir() if entry.is_file()]

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

    print("### Project Environment")
    print(f"- **Package Manager:** {env.package_manager}")
    print(f"- **Test Runner:** {env.test_runner}")
    print(f"- **Linter/Formatter:** {env.linter}")
    print(f"- **Monorepo:** {'Yes' if env.is_monorepo else 'No'}")
    return 0


def find_dependencies(target_dir: Path) -> int:
    found: list[DependencyInfo] = []

    for entry in (e for e in target_dir.iterdir() if e.is_dir()):
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

    if found:
        print("### Installed Dependencies")
        for dep in found:
            size_str = (
                f"{dep.size_mb} MB"
                if isinstance(dep.size_mb, (int, float))
                else dep.size_mb
            )
            print(f"- **{dep.name}** ({dep.type}) → `{dep.path}` [{size_str}]")
    else:
        print("### Installed Dependencies")
        print("- None detected in root directory.")

    return 0


def lint_agents_md(file_path: Path) -> int:
    if not file_path.exists():
        print(f"FAIL: File not found at {file_path}", file=sys.stderr)
        return 1

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    has_errors = False

    print(f"### Linting {file_path}")

    if len(lines) > 100:
        print(f"FAIL: File is {len(lines)} lines. Must be under 100.", file=sys.stderr)
        has_errors = True

    if not lines or not lines[0].startswith("# "):
        print("FAIL: File must start with an H1 header.", file=sys.stderr)
        has_errors = True

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
            print(
                f'FAIL: Line {index + 1} contains filler text: "{line.strip()}"',
                file=sys.stderr,
            )
            has_errors = True
        if auto_discovery_regex.search(line):
            print(
                f'FAIL: Line {index + 1} lists auto-discovered tools: "{line.strip()}"',
                file=sys.stderr,
            )
            has_errors = True
        if generic_advice_regex.search(line):
            print(
                f'WARN: Line {index + 1} contains generic advice: "{line.strip()}"',
                file=sys.stderr,
            )

    if "Co-Authored-By:" not in content:
        print('FAIL: Missing "Co-Authored-By:" attribution.', file=sys.stderr)
        has_errors = True

    if not has_errors:
        print(f"PASS: {file_path} looks correct.")
    return 1 if has_errors else 0


def validate_skills(skills_dir: Path) -> int:
    if not skills_dir.exists():
        print(f"FAIL: Skills directory not found: {skills_dir}", file=sys.stderr)
        return 1

    print(f"### Validating Skills in {skills_dir}")
    has_errors = False
    REQUIRED_KEYS = ("name", "description", "disable-model-invocation")

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            print(f"FAIL: {skill_dir.name}/ has no SKILL.md", file=sys.stderr)
            has_errors = True
            continue

        content = skill_file.read_text(encoding="utf-8")
        fm = _parse_frontmatter(content)

        for key in REQUIRED_KEYS:
            if key not in fm:
                print(
                    f"FAIL: {skill_dir.name}/SKILL.md missing frontmatter key: '{key}'",
                    file=sys.stderr,
                )
                has_errors = True

        if len(content.splitlines()) > 150:
            print(
                f"WARN: {skill_dir.name}/SKILL.md is long (>150 lines). Consider splitting to references/.",
                file=sys.stderr,
            )

    if not has_errors:
        print("PASS: All skills have valid frontmatter.")
    return 1 if has_errors else 0


def check_hooks(hooks_file: Path) -> int:
    if not hooks_file.exists():
        print(f"FAIL: hooks.json not found at {hooks_file}", file=sys.stderr)
        return 1

    print(f"### Validating Hooks in {hooks_file}")
    has_errors = False
    try:
        with open(hooks_file, "r", encoding="utf-8") as f:
            hooks_data = json.load(f)
    except Exception as e:
        print(f"FAIL: Failed to parse hooks.json: {e}", file=sys.stderr)
        return 1

    plugin_root = hooks_file.parent.parent

    for event, event_hooks in hooks_data.get("hooks", {}).items():
        for hook_entry in event_hooks:
            for hook in hook_entry.get("hooks", []):
                cmd = hook.get("command", "")
                if not cmd:
                    continue

                # Check for handler existence if using runner.mjs
                if "runner.mjs" in cmd:
                    parts = cmd.split()
                    try:
                        domain_idx = parts.index("runner.mjs") + 1
                        domain = parts[domain_idx]
                        handler_path = (
                            plugin_root / "hooks" / "handlers" / f"{domain}.mjs"
                        )
                        if not handler_path.exists():
                            print(
                                f"FAIL: Missing handler for hook '{event}': {handler_path}",
                                file=sys.stderr,
                            )
                            has_errors = True
                    except (ValueError, IndexError):
                        pass

                # Check for direct script existence
                elif "scripts" in cmd:
                    script_path = cmd.split()[-1].replace(
                        "${CLAUDE_PLUGIN_ROOT}", str(plugin_root)
                    )
                    if not os.path.exists(script_path):
                        print(
                            f"FAIL: Missing script for hook '{event}': {script_path}",
                            file=sys.stderr,
                        )
                        has_errors = True

    if not has_errors:
        print("PASS: Hook configuration and handlers are valid.")
    return 1 if has_errors else 0


def check_manifest(manifest_file: Path) -> int:
    if not manifest_file.exists():
        print(f"FAIL: plugin.json not found at {manifest_file}", file=sys.stderr)
        return 1

    print(f"### Validating Manifest in {manifest_file}")
    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"FAIL: Failed to parse plugin.json: {e}", file=sys.stderr)
        return 1

    required = ["name", "version", "description"]
    has_errors = False
    for key in required:
        if key not in data:
            print(f"FAIL: Manifest missing required key: '{key}'", file=sys.stderr)
            has_errors = True

    if not has_errors:
        print("PASS: Manifest is valid.")
    return 1 if has_errors else 0


def check_all(root_dir: Path) -> int:
    print(f"## Full Plugin Health Audit: {root_dir.name}\n")
    exit_codes = [
        scan_structure(root_dir, max_depth=2),
        analyze_env(root_dir),
        validate_skills(root_dir / "skills"),
        lint_agents_md(root_dir / "AGENTS.md"),
        check_hooks(root_dir / "hooks" / "hooks.json"),
        check_manifest(root_dir / ".claude-plugin" / "plugin.json"),
    ]
    print("\n## Audit Summary")
    if any(code != 0 for code in exit_codes):
        print("❌ Audit failed with one or more errors.")
        return 1
    print("✅ Audit passed. Plugin is healthy.")
    return 0


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
            return check_all(root)
        case "check-hooks":
            return check_hooks(root / "hooks" / "hooks.json")
        case "check-manifest":
            return check_manifest(root / ".claude-plugin" / "plugin.json")
        case "validate-skills":
            return validate_skills(root / "skills")
        case "lint-agents-md":
            return lint_agents_md(args.file_path)
        case "analyze-env":
            return analyze_env(root)
        case "scan-structure":
            return scan_structure(root)
        case _:
            return 1


if __name__ == "__main__":
    sys.exit(main())
