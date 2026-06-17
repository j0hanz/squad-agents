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
import shlex
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import IO, Any, ClassVar


class Config:
    """Central configuration for plugin audit utilities."""

    DEPENDENCY_DIRS: ClassVar[dict[str, str]] = {
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

    PACKAGE_MANAGERS: ClassVar[dict[str, str]] = {
        "pnpm-lock.yaml": "pnpm",
        "yarn.lock": "yarn",
        "package-lock.json": "npm",
        "bun.lockb": "bun",
        "uv.lock": "uv",
        "poetry.lock": "poetry",
        "Cargo.lock": "cargo",
        "go.sum": "go",
    }

    DEFAULT_IGNORE_PATTERNS: ClassVar[set[str]] = {
        ".git",
        ".vscode",
        ".idea",
        ".env",
        "*.log",
        "__pycache__",
        ".pytest_cache",
        ".DS_Store",
    }

    SKILL_REQUIRED_KEYS: tuple[str, ...] = (
        "name",
        "description",
    )
    MAX_DIR_SCAN_COUNT = 10000
    MAX_SKILL_LINES = 150
    MAX_AGENTS_MD_LINES = 100

    # Per-language scaffold defaults for `scaffold-agents-md`. Each entry supplies a
    # *starting point* only — the LLM must override any value Phase 1 discovered to
    # differ from the default (e.g. a repo using npm instead of pnpm).
    LANGUAGE_DEFAULTS: ClassVar[dict[str, dict[str, Any]]] = {
        "node": {
            "pm": "pnpm",
            "toolchain": {
                "install": "pnpm install",
                "dev": "pnpm dev",
                "test": "pnpm test",
            },
            "dependency_locations": {"node_modules": "node_modules/"},
            "commands": [
                ("Typecheck", "pnpm tsc --noEmit path/to/file.ts"),
                ("Lint", "pnpm eslint path/to/file.ts"),
                ("Test", "pnpm jest path/to/file.test.ts"),
            ],
        },
        "python": {
            "pm": "uv",
            "toolchain": {
                "sync": "uv sync",
                "test": "uv run pytest",
                "add-dep": "uv add <pkg>",
            },
            "dependency_locations": {
                "venv": ".venv/",
                "site-packages": ".venv/lib/python3.x/site-packages/",
            },
            "commands": [
                ("Typecheck", "uv run mypy path/to/file.py"),
                ("Lint", "uv run ruff check path/to/file.py"),
                ("Test", "uv run pytest path/to/test_file.py::test_name"),
            ],
        },
        "go": {
            "pm": "Go Modules",
            "toolchain": {
                "tidy": "go mod tidy",
                "build": "go build",
                "test": "go test",
            },
            "dependency_locations": {
                "vendor": "vendor/ (if used)",
                "module-cache": "$GOPATH/pkg/mod",
            },
            "commands": [
                ("Lint", "golangci-lint run path/to/file.go"),
                ("Test", "go test -run TestName path/to/package"),
            ],
        },
        "rust": {
            "pm": "Cargo",
            "toolchain": {
                "build": "cargo build",
                "test": "cargo test",
                "lint": "cargo clippy",
            },
            "dependency_locations": {"build-artifacts": "target/"},
            "commands": [
                ("Lint", "cargo clippy --package <pkg_name> -- -D warnings"),
                ("Test", "cargo test --package <pkg_name> test_name"),
            ],
        },
        "java": {
            "pm": "Maven or Gradle",
            "toolchain": {
                "maven-build": "mvn clean install",
                "maven-test": "mvn test",
                "gradle-build": "gradle build",
                "gradle-test": "gradle test",
            },
            "dependency_locations": {
                "maven": "build in target/, cache in ~/.m2/repository",
                "gradle": "build in build/, cache in ~/.gradle",
            },
            "commands": [
                (
                    "Compile",
                    "mvn compile -pl :<module_name> (or gradle -p :<module> build)",
                ),
                ("Test", "mvn test -Dtest=TestClass#testMethod -pl :<module>"),
            ],
        },
        "dotnet": {
            "pm": "dotnet",
            "toolchain": {
                "restore": "dotnet restore",
                "build": "dotnet build",
                "test": "dotnet test",
            },
            "dependency_locations": {
                "nuget-cache": "~/.nuget/packages",
                "build": "bin/, obj/",
            },
            "commands": [
                ("Build", "dotnet build -p :<ProjectName>"),
                ("Test", "dotnet test --filter FullyQualifiedName~TestClassName"),
            ],
        },
        "bun": {
            "pm": "bun",
            "toolchain": {
                "install": "bun install",
                "run": "bun run",
                "test": "bun test",
            },
            "dependency_locations": {"modules": "node_modules/"},
            "commands": [
                ("Test", "bun test path/to/file.test.ts"),
                ("Run", "bun path/to/file.ts"),
            ],
        },
    }

    # Phase 0 survey answers -> Hard Rules sentence. Keys must match the marker
    # value encoding in references/hard-rules.md.
    HARD_RULES_TEXT: ClassVar[dict[str, dict[str, str]]] = {
        "commit": {
            "strict": "Conventional Commits format (`type(scope): subject`) required; every AI commit MUST include a `Co-Authored-By:` trailer",
            "relaxed": "free-form commit messages allowed; every AI commit MUST include a `Co-Authored-By:` trailer",
            "minimal": "no enforced message format, no required attribution trailer",
        },
        "maturity": {
            "production": "stability first — avoid breaking changes, prefer additive changes, flag breaking changes explicitly before making them",
            "development": "breaking changes are fine — never add fallback/legacy-compat shims, rewrite to the better approach directly",
        },
        "testing": {
            "always": "every change must have passing tests before being called done",
            "touched-files": "test/typecheck files you changed; don't require full-suite runs",
            "not-enforced": "no automatic testing requirement, rely on existing CI",
        },
    }


class IssueLevel(Enum):
    """Levels for validation issues."""

    INFO = auto()
    WARN = auto()
    FAIL = auto()


@dataclass
class ValidationIssue:
    """Represents a single validation issue or warning."""

    level: IssueLevel
    message: str
    line_number: int | None = None

    def __str__(self) -> str:
        line_info = f" (line {self.line_number})" if self.line_number else ""
        return f"{self.message}{line_info}"


@dataclass
class ValidationResult:
    """Consolidated result of a validation check."""

    success: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(issue.level == IssueLevel.FAIL for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(issue.level == IssueLevel.WARN for issue in self.issues)


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
    size_mb: float
    size_truncated: bool = False


@dataclass
class AuditResults:
    """Consolidated results of the plugin audit."""

    structure: list[str] = field(default_factory=list)
    env: ProjectEnvironment = field(default_factory=ProjectEnvironment)
    dependencies: list[DependencyInfo] = field(default_factory=list)
    skills: ValidationResult = field(
        default_factory=lambda: ValidationResult(success=True)
    )
    agents_md: ValidationResult = field(
        default_factory=lambda: ValidationResult(success=True)
    )
    hooks: ValidationResult = field(
        default_factory=lambda: ValidationResult(success=True)
    )
    manifest: ValidationResult = field(
        default_factory=lambda: ValidationResult(success=True)
    )


def safe_print(text: str, file: IO[str] = sys.stdout) -> None:
    """Print text safely, handling encoding issues."""
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        encoded = text.encode(getattr(file, "encoding", "utf-8") or "utf-8", "replace")
        print(encoded.decode(getattr(file, "encoding", "utf-8") or "utf-8"), file=file)


def load_gitignore(target_dir: Path) -> set[str]:
    """Load ignore patterns from .gitignore file."""
    patterns: set[str] = set()
    try:
        content = (target_dir / ".gitignore").read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.add(line.rstrip("/"))
    except (OSError, UnicodeDecodeError):
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
        if "/" not in pattern and path.name == pattern.rstrip("/"):
            return True
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
        files = {entry.name for entry in target_dir.iterdir() if entry.is_file()}
    except (PermissionError, OSError):
        return env

    for lockfile, pm in Config.PACKAGE_MANAGERS.items():
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
        if entry.name in Config.DEPENDENCY_DIRS:
            try:
                size_mb = 0.0
                count = 0
                for f in entry.rglob("*"):
                    if f.is_file():
                        size_mb += f.stat().st_size
                        count += 1
                        if count > Config.MAX_DIR_SCAN_COUNT:
                            break
                size_mb /= 1024 * 1024

                found.append(
                    DependencyInfo(
                        name=entry.name,
                        type=Config.DEPENDENCY_DIRS[entry.name],
                        path=str(entry.relative_to(target_dir)),
                        size_mb=round(size_mb, 1),
                        size_truncated=count > Config.MAX_DIR_SCAN_COUNT,
                    )
                )
            except (PermissionError, OSError):
                found.append(
                    DependencyInfo(
                        name=entry.name,
                        type=Config.DEPENDENCY_DIRS[entry.name],
                        path=str(entry.relative_to(target_dir)),
                        size_mb=0.0,
                        size_truncated=True,
                    )
                )

    return found


def validate_skill_files(skills_dir: Path) -> ValidationResult:
    """Validate all SKILL.md files in the skills directory."""
    if not skills_dir.exists():
        return ValidationResult(
            success=False,
            issues=[
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message=f"Skills directory not found: {skills_dir}",
                )
            ],
        )

    issues: list[ValidationIssue] = []

    try:
        skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    except (PermissionError, OSError) as e:
        return ValidationResult(
            success=False,
            issues=[
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message=f"Failed to list skills directory: {e}",
                )
            ],
        )

    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL, message=f"{skill_dir.name}/ has no SKILL.md"
                )
            )
            continue

        try:
            content = skill_file.read_text(encoding="utf-8")
            fm = _parse_frontmatter(content)

            for key in Config.SKILL_REQUIRED_KEYS:
                if key not in fm:
                    issues.append(
                        ValidationIssue(
                            level=IssueLevel.FAIL,
                            message=f"{skill_dir.name}/SKILL.md missing frontmatter key: '{key}'",
                        )
                    )

            if len(content.splitlines()) > Config.MAX_SKILL_LINES:
                issues.append(
                    ValidationIssue(
                        level=IssueLevel.WARN,
                        message=f"{skill_dir.name}/SKILL.md is long (>{Config.MAX_SKILL_LINES} lines)",
                    )
                )
        except (OSError, UnicodeDecodeError) as e:
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL, message=f"Failed to read {skill_file}: {e}"
                )
            )

    return ValidationResult(
        success=not any(i.level == IssueLevel.FAIL for i in issues), issues=issues
    )


_FILLER_RE = re.compile(
    r"(welcome to|this document explains|you should)", re.IGNORECASE
)
_AUTO_DISCOVERY_RE = re.compile(
    r"(\d+\s+(tools|resources|prompts)|MCP server)", re.IGNORECASE
)
_GENERIC_ADVICE_RE = re.compile(
    r"\b(always|be sure|remember|carefully|thoroughly|best practice|make sure|important|test thoroughly|be careful)\b",
    re.IGNORECASE,
)
_FILE_SCOPED_COMMANDS_RE = re.compile(r"##\s+file-scoped commands", re.IGNORECASE)
_HARD_RULES_MARKER_RE = re.compile(
    r"<!--\s*codebase-init:hard-rules\s+v1\s+commit=\S+\s+maturity=\S+\s+testing=\S+\s*-->"
)


def render_hard_rules_marker(commit: str, maturity: str, testing: str) -> str:
    """Render the trailing hard-rules marker comment encoding the 3 survey answers."""
    return f"<!-- codebase-init:hard-rules v1 commit={commit} maturity={maturity} testing={testing} -->"


def has_hard_rules_marker(content: str) -> bool:
    """Return True if content contains a valid v1 hard-rules marker comment."""
    return bool(_HARD_RULES_MARKER_RE.search(content))


def render_agents_md_skeleton(
    language: str,
    purpose: str,
    commit: str,
    maturity: str,
    testing: str,
    pm_override: str | None = None,
    toolchain_overrides: dict[str, str] | None = None,
) -> str:
    """Render a markdown-kv AGENTS.md skeleton with Hard Rules first.

    `pm_override`/`toolchain_overrides` carry real commands discovered in Phase 1 —
    they replace the per-language defaults, which exist only as a starting point and
    must never be hallucinated as fact for a specific repo.
    """
    if language not in Config.LANGUAGE_DEFAULTS:
        raise ValueError(
            f"Unknown language {language!r}. Choices: {sorted(Config.LANGUAGE_DEFAULTS)}"
        )
    for category, value in (
        ("commit", commit),
        ("maturity", maturity),
        ("testing", testing),
    ):
        if value not in Config.HARD_RULES_TEXT[category]:
            raise ValueError(
                f"Unknown {category} {value!r}. Choices: {sorted(Config.HARD_RULES_TEXT[category])}"
            )

    defaults = Config.LANGUAGE_DEFAULTS[language]
    pm = pm_override or defaults["pm"]
    toolchain = dict(defaults["toolchain"])
    toolchain.update(toolchain_overrides or {})

    lines: list[str] = [
        "# Agent Instructions",
        "",
        f"purpose: {purpose}",
        "",
        "## Hard Rules",
        "",
        f"commit: {Config.HARD_RULES_TEXT['commit'][commit]}",
        f"maturity: {Config.HARD_RULES_TEXT['maturity'][maturity]}",
        f"testing: {Config.HARD_RULES_TEXT['testing'][testing]}",
        "",
        render_hard_rules_marker(commit, maturity, testing),
        "",
        "## Package Manager",
        "",
        f"pm: {pm}",
    ]
    for key, value in toolchain.items():
        lines.append(f"{key}: `{value}`")

    lines += ["", "## Dependency Locations", ""]
    for key, value in defaults["dependency_locations"].items():
        lines.append(f"{key}: `{value}`")

    lines += ["", "## File-Scoped Commands", "", "| Task | Command |", "| --- | --- |"]
    for task, command in defaults["commands"]:
        lines.append(f"| {task} | `{command}` |")

    lines += [
        "",
        "## Key Conventions",
        "",
        "# TODO: 3-7 kv lines grounded in real repo facts from Phase 1/1.5 — never invented",
        "",
        "## Commit Attribution",
        "",
        "Co-Authored-By: <Model Name>",
        "",
    ]
    return "\n".join(lines)


_HARD_RULES_SECTION_RE = re.compile(r"^##\s+Hard Rules\b", re.IGNORECASE | re.MULTILINE)
_PACKAGE_OVERRIDE_RE = re.compile(r"See\s+\[AGENTS\.md\]", re.IGNORECASE)


def is_package_level_override(content: str) -> bool:
    """Return True if content is a recognized package-level AGENTS.md override."""
    return bool(_PACKAGE_OVERRIDE_RE.search(content))


def validate_agents_md_file(file_path: Path) -> ValidationResult:
    """Validate the AGENTS.md file."""
    if not file_path.exists():
        return ValidationResult(
            success=False,
            issues=[
                ValidationIssue(
                    level=IssueLevel.FAIL, message=f"File not found at {file_path}"
                )
            ],
        )

    issues: list[ValidationIssue] = []
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        if len(lines) > Config.MAX_AGENTS_MD_LINES:
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message=f"File is {len(lines)} lines. Must be under {Config.MAX_AGENTS_MD_LINES}.",
                )
            )

        if not lines or not lines[0].startswith("# "):
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL, message="File must start with an H1 header."
                )
            )

        in_code_block = False
        for index, line in enumerate(lines):
            line_num = index + 1
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if line.strip().startswith("<!--") and line.strip().endswith("-->"):
                continue
            if _FILLER_RE.search(line):
                issues.append(
                    ValidationIssue(
                        level=IssueLevel.FAIL,
                        message=f'Filler text detected: "{line.strip()}"',
                        line_number=line_num,
                    )
                )
            if _AUTO_DISCOVERY_RE.search(line):
                issues.append(
                    ValidationIssue(
                        level=IssueLevel.FAIL,
                        message=f'Auto-discovered list detected: "{line.strip()}"',
                        line_number=line_num,
                    )
                )
            if _GENERIC_ADVICE_RE.search(line):
                issues.append(
                    ValidationIssue(
                        level=IssueLevel.WARN,
                        message=f'Generic advice detected: "{line.strip()}"',
                        line_number=line_num,
                    )
                )

        if "Co-Authored-By:" not in content:
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message='Missing "Co-Authored-By:" attribution.',
                )
            )

        if (
            not _FILE_SCOPED_COMMANDS_RE.search(content)
            and "| Tool | File | Command |" not in content
        ):
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message='Missing mandatory "File-scoped commands" table.',
                )
            )

        has_hard_rules_section = bool(_HARD_RULES_SECTION_RE.search(content))
        if not has_hard_rules_section and not is_package_level_override(content):
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message='Missing mandatory "## Hard Rules" section.',
                )
            )
        elif has_hard_rules_section and not has_hard_rules_marker(content):
            issues.append(
                ValidationIssue(
                    level=IssueLevel.WARN,
                    message='"## Hard Rules" section present but missing/malformed '
                    "codebase-init:hard-rules v1 marker comment.",
                )
            )
    except (OSError, UnicodeDecodeError) as e:
        issues.append(
            ValidationIssue(
                level=IssueLevel.FAIL, message=f"Failed to read {file_path}: {e}"
            )
        )

    return ValidationResult(
        success=not any(i.level == IssueLevel.FAIL for i in issues), issues=issues
    )


def validate_hooks_config(hooks_file: Path) -> ValidationResult:
    """Validate hooks.json and existence of handlers."""
    if not hooks_file.exists():
        return ValidationResult(
            success=False,
            issues=[
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message=f"hooks.json not found at {hooks_file}",
                )
            ],
        )

    issues: list[ValidationIssue] = []
    try:
        hooks_data = json.loads(hooks_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return ValidationResult(
            success=False,
            issues=[
                ValidationIssue(
                    level=IssueLevel.FAIL, message=f"Failed to parse hooks.json: {e}"
                )
            ],
        )

    plugin_root = hooks_file.parent.parent

    for event, event_hooks in hooks_data.get("hooks", {}).items():
        for hook_entry in event_hooks:
            for hook in hook_entry.get("hooks", []):
                cmd = hook.get("command", "")
                if not cmd:
                    continue

                if "runner.mjs" in cmd:
                    parts = shlex.split(cmd)
                    try:
                        domain_idx = (
                            next(i for i, p in enumerate(parts) if "runner.mjs" in p)
                            + 1
                        )
                        domain = parts[domain_idx]
                        handler_path = (
                            plugin_root / "hooks" / "handlers" / f"{domain}.mjs"
                        )
                        if not handler_path.exists():
                            issues.append(
                                ValidationIssue(
                                    level=IssueLevel.FAIL,
                                    message=f"Missing handler for hook '{event}': {handler_path}",
                                )
                            )
                    except (ValueError, IndexError):
                        issues.append(
                            ValidationIssue(
                                level=IssueLevel.WARN,
                                message=f"Could not determine handler for hook '{event}': {cmd!r}",
                            )
                        )

                elif (
                    "scripts" in cmd
                    or "hooks/handlers" in cmd
                    or "${CLAUDE_PLUGIN_ROOT}" in cmd
                ):
                    script_path_str = shlex.split(cmd)[-1].replace(
                        "${CLAUDE_PLUGIN_ROOT}", str(plugin_root)
                    )
                    if not Path(script_path_str).exists():
                        issues.append(
                            ValidationIssue(
                                level=IssueLevel.FAIL,
                                message=f"Missing script for hook '{event}': {script_path_str}",
                            )
                        )

    return ValidationResult(
        success=not any(i.level == IssueLevel.FAIL for i in issues), issues=issues
    )


def validate_manifest_file(manifest_file: Path) -> ValidationResult:
    """Validate plugin.json manifest."""
    if not manifest_file.exists():
        return ValidationResult(
            success=False,
            issues=[
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message=f"plugin.json not found at {manifest_file}",
                )
            ],
        )

    issues: list[ValidationIssue] = []
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        for key in ("name", "version", "description"):
            if key not in data:
                issues.append(
                    ValidationIssue(
                        level=IssueLevel.FAIL,
                        message=f"Manifest missing required key: '{key}'",
                    )
                )
    except (json.JSONDecodeError, OSError) as e:
        issues.append(
            ValidationIssue(
                level=IssueLevel.FAIL, message=f"Failed to parse plugin.json: {e}"
            )
        )

    return ValidationResult(
        success=not any(i.level == IssueLevel.FAIL for i in issues), issues=issues
    )


def wire_agents_files(source: Path, targets: list[Path]) -> int:
    """Write one-line redirect stubs (never full copies) pointing targets at source."""
    source = source.resolve()
    if not source.exists():
        safe_print(f"FAIL: Source file not found: {source}", file=sys.stderr)
        return 1

    exit_code = 0
    for target in targets:
        target = target.resolve()
        if target == source:
            safe_print(
                f"FAIL: target is the same file as source, skipping: {target}",
                file=sys.stderr,
            )
            exit_code = 1
            continue
        try:
            if target.is_dir():
                raise IsADirectoryError(f"target is a directory: {target}")
            if target.exists() or target.is_symlink():
                target.unlink()
            rel = os.path.relpath(source, target.parent).replace(os.sep, "/")
            target.write_text(
                f"# See [{source.name}]({rel})\n", encoding="utf-8", newline="\n"
            )
            safe_print(f"Stubbed: {target.name} -> {rel}")
        except OSError as e:
            safe_print(f"FAIL: Could not wire {target}: {e}", file=sys.stderr)
            exit_code = 1

    return exit_code


def print_validation_issues(result: ValidationResult) -> None:
    """Print validation issues with appropriate levels."""
    for issue in result.issues:
        prefix = "FAIL" if issue.level == IssueLevel.FAIL else "WARN"
        safe_print(f"{prefix}: {issue}", file=sys.stderr)


def print_audit_report(root_dir: Path, results: AuditResults) -> int:
    """Print the final formatted audit report."""
    safe_print(f"## Full Plugin Health Audit: {root_dir.name}\n")

    safe_print(f"### Directory Structure ({root_dir.name})")
    safe_print("```")
    for line in results.structure:
        safe_print(line)
    safe_print("```\n")

    safe_print("### Project Environment")
    safe_print(f"- **Package Manager:** {results.env.package_manager}")
    safe_print(f"- **Test Runner:** {results.env.test_runner}")
    safe_print(f"- **Linter/Formatter:** {results.env.linter}")
    safe_print(f"- **Monorepo:** {'Yes' if results.env.is_monorepo else 'No'}\n")

    safe_print("### Installed Dependencies")
    if results.dependencies:
        for dep in results.dependencies:
            prefix = ">" if dep.size_truncated else ""
            size_str = f"{prefix}{dep.size_mb} MB"
            safe_print(f"- **{dep.name}** ({dep.type}) → `{dep.path}` [{size_str}]")
    else:
        safe_print("- None detected in root directory.")
    safe_print("")

    safe_print(f"### Validating Skills in {root_dir / 'skills'}")
    if results.skills.success and not results.skills.issues:
        safe_print("PASS: All skills have valid frontmatter.")
    else:
        print_validation_issues(results.skills)
    safe_print("")

    safe_print(f"### Linting {root_dir / 'AGENTS.md'}")
    if results.agents_md.success and not results.agents_md.issues:
        safe_print(f"PASS: {root_dir / 'AGENTS.md'} looks correct.")
    else:
        print_validation_issues(results.agents_md)
    safe_print("")

    safe_print(f"### Validating Hooks in {root_dir / 'hooks' / 'hooks.json'}")
    if results.hooks.success and not results.hooks.issues:
        safe_print("PASS: Hook configuration and handlers are valid.")
    else:
        print_validation_issues(results.hooks)
    safe_print("")

    safe_print(
        f"### Validating Manifest in {root_dir / '.claude-plugin' / 'plugin.json'}"
    )
    if results.manifest.success and not results.manifest.issues:
        safe_print("PASS: Manifest is valid.")
    else:
        print_validation_issues(results.manifest)

    safe_print("\n## Audit Summary")
    checks = (results.skills, results.agents_md, results.hooks, results.manifest)
    if any(r.has_errors for r in checks):
        safe_print("FAIL: Audit failed with one or more errors.")
        return 1
    safe_print("PASS: Audit passed. Plugin is healthy.")
    return 0


def run_full_audit(root_dir: Path) -> int:
    """Orchestrate the full audit process."""
    results = AuditResults()
    patterns = load_gitignore(root_dir) | Config.DEFAULT_IGNORE_PATTERNS

    results.structure = get_tree_lines(root_dir, patterns)
    results.env = analyze_project_env(root_dir)
    results.dependencies = get_dependencies(root_dir)
    results.skills = validate_skill_files(root_dir / "skills")
    results.agents_md = validate_agents_md_file(root_dir / "AGENTS.md")
    results.hooks = validate_hooks_config(root_dir / "hooks" / "hooks.json")
    results.manifest = validate_manifest_file(
        root_dir / ".claude-plugin" / "plugin.json"
    )

    return print_audit_report(root_dir, results)


def _resolve_target(raw: Path | None, fallback: Path) -> Path:
    """Resolve an optional target_dir argument, falling back to cwd."""
    return (raw or fallback).resolve()


def _setup_parser() -> argparse.ArgumentParser:
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

    analyze_env_parser = subparsers.add_parser(
        "analyze-env", help="Detect project environment."
    )
    analyze_env_parser.add_argument(
        "target_dir",
        type=Path,
        nargs="?",
        default=None,
        help="Directory to analyze (default: current directory).",
    )

    find_deps_parser = subparsers.add_parser(
        "find-dependencies", help="Locate installed dependency directories."
    )
    find_deps_parser.add_argument(
        "target_dir",
        type=Path,
        nargs="?",
        default=None,
        help="Directory to search (default: current directory).",
    )

    scan_parser = subparsers.add_parser(
        "scan-structure", help="Show directory structure."
    )
    scan_parser.add_argument(
        "target_dir",
        type=Path,
        nargs="?",
        default=None,
        help="Directory to scan (default: current directory).",
    )
    scan_parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum depth to recurse (default: 3).",
    )

    analyze_all_parser = subparsers.add_parser(
        "analyze-all",
        help="Run analyze-env, find-dependencies, and scan-structure sequentially.",
    )
    analyze_all_parser.add_argument(
        "target_dir",
        type=Path,
        nargs="?",
        default=None,
        help="Directory to analyze (default: current directory).",
    )
    analyze_all_parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum depth for scan-structure (default: 3).",
    )

    wire_parser = subparsers.add_parser(
        "wire-agents",
        help="Write one-line redirect stubs in agent-specific files pointing to AGENTS.md.",
    )
    wire_parser.add_argument("source", type=Path, help="Source file (e.g. AGENTS.md).")
    wire_parser.add_argument(
        "targets",
        type=Path,
        nargs="+",
        help="Target files to create (e.g. CLAUDE.md GEMINI.md).",
    )

    scaffold_parser = subparsers.add_parser(
        "scaffold-agents-md",
        help="Print (or write) an AGENTS.md skeleton for a language, Hard Rules first.",
    )
    scaffold_parser.add_argument(
        "--language", required=True, choices=sorted(Config.LANGUAGE_DEFAULTS)
    )
    scaffold_parser.add_argument(
        "--purpose", default="<one sentence — what this repo does>"
    )
    scaffold_parser.add_argument(
        "--commit", required=True, choices=sorted(Config.HARD_RULES_TEXT["commit"])
    )
    scaffold_parser.add_argument(
        "--maturity", required=True, choices=sorted(Config.HARD_RULES_TEXT["maturity"])
    )
    scaffold_parser.add_argument(
        "--testing", required=True, choices=sorted(Config.HARD_RULES_TEXT["testing"])
    )
    scaffold_parser.add_argument(
        "--pm", default=None, help="Override the default package manager name."
    )
    scaffold_parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override a toolchain command discovered in Phase 1, e.g. --set test='npm test'.",
    )
    scaffold_parser.add_argument(
        "--out", type=Path, default=None, help="Write to this file instead of stdout."
    )
    return parser


def main() -> int:
    parser = _setup_parser()

    args = parser.parse_args()
    root = Path(".").resolve()

    match args.command:
        case "check-all":
            return run_full_audit(root)
        case "check-hooks":
            result = validate_hooks_config(root / "hooks" / "hooks.json")
            print_validation_issues(result)
            if result.success:
                safe_print("PASS: Hooks are valid.")
            return 0 if result.success else 1
        case "check-manifest":
            result = validate_manifest_file(root / ".claude-plugin" / "plugin.json")
            print_validation_issues(result)
            if result.success:
                safe_print("PASS: Manifest is valid.")
            return 0 if result.success else 1
        case "validate-skills":
            result = validate_skill_files(root / "skills")
            print_validation_issues(result)
            if result.success:
                safe_print("PASS: Skills are valid.")
            return 0 if result.success else 1
        case "lint-agents-md":
            result = validate_agents_md_file(args.file_path)
            print_validation_issues(result)
            if result.success:
                safe_print("PASS: AGENTS.md is valid.")
            return 0 if result.success else 1
        case "analyze-env":
            target = _resolve_target(args.target_dir, root)
            env = analyze_project_env(target)
            safe_print(f"Package Manager: {env.package_manager}")
            safe_print(f"Test Runner:     {env.test_runner}")
            safe_print(f"Linter:          {env.linter}")
            safe_print(f"Monorepo:        {env.is_monorepo}")
            return 0
        case "find-dependencies":
            target = _resolve_target(args.target_dir, root)
            deps = get_dependencies(target)
            if deps:
                for dep in deps:
                    prefix = ">" if dep.size_truncated else ""
                    size_str = f"{prefix}{dep.size_mb} MB"
                    safe_print(f"{dep.name} ({dep.type}) -> {dep.path} [{size_str}]")
            else:
                safe_print("No dependency directories found.")
            return 0
        case "scan-structure":
            target = _resolve_target(args.target_dir, root)
            patterns = load_gitignore(target) | Config.DEFAULT_IGNORE_PATTERNS
            lines = get_tree_lines(target, patterns, args.max_depth)
            for line in lines:
                safe_print(line)
            return 0
        case "analyze-all":
            target = _resolve_target(args.target_dir, root)
            safe_print("### Environment")
            env = analyze_project_env(target)
            safe_print(f"Package Manager: {env.package_manager}")
            safe_print(f"Test Runner:     {env.test_runner}")
            safe_print(f"Linter:          {env.linter}")
            safe_print(f"Monorepo:        {env.is_monorepo}")
            safe_print("")
            safe_print("### Dependencies")
            deps = get_dependencies(target)
            if deps:
                for dep in deps:
                    prefix = ">" if dep.size_truncated else ""
                    size_str = f"{prefix}{dep.size_mb} MB"
                    safe_print(f"{dep.name} ({dep.type}) -> {dep.path} [{size_str}]")
            else:
                safe_print("None found.")
            safe_print("")
            safe_print("### Structure")
            patterns = load_gitignore(target) | Config.DEFAULT_IGNORE_PATTERNS
            lines = get_tree_lines(target, patterns, args.max_depth)
            for line in lines:
                safe_print(line)
            return 0
        case "wire-agents":
            return wire_agents_files(args.source, args.targets)
        case "scaffold-agents-md":
            overrides: dict[str, str] = {}
            for pair in args.set:
                if "=" not in pair:
                    safe_print(
                        f"FAIL: --set expects KEY=VALUE, got: {pair}", file=sys.stderr
                    )
                    return 1
                key, _, value = pair.partition("=")
                overrides[key] = value
            try:
                content = render_agents_md_skeleton(
                    args.language,
                    args.purpose,
                    args.commit,
                    args.maturity,
                    args.testing,
                    pm_override=args.pm,
                    toolchain_overrides=overrides,
                )
            except ValueError as e:
                safe_print(f"FAIL: {e}", file=sys.stderr)
                return 1
            if args.out:
                args.out.write_text(content, encoding="utf-8", newline="\n")
                safe_print(f"Wrote skeleton to {args.out}")
            else:
                safe_print(content)
            return 0
        case _:
            return 1


if __name__ == "__main__":
    sys.exit(main())
