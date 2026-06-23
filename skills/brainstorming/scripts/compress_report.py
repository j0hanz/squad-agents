#!/usr/bin/env python3
"""
Compresses a Codebase Context Report JSON to minimal token form.

Deduplicates and truncates low-signal fields before the report is passed
to the design-proposer in Phase 4. Reads from a file or stdin.

Usage:
    python compress_report.py report.json
    cat report.json | python compress_report.py
    python compress_report.py report.json --max-files 3 --max-log-lines 2
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CompressConfig:
    max_files: int = 5
    max_log_lines: int = 3
    max_constraints: int = 5
    max_interface_shapes: int = 10
    max_unknowns: int = 4
    max_design_docs: int = 3
    max_analogous: int = 2


def _dedupe_stable(items: list[Any]) -> list[str]:
    """Deduplicate preserving first-occurrence order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        item = item if isinstance(item, str) else str(item)
        key = item.strip().lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _truncate_git_log(log: str, max_lines: int) -> str:
    if not log or not log.strip() or log == "no history":
        return "no history"
    lines = [line for line in log.splitlines() if line.strip()]
    truncated = lines[:max_lines]
    omitted = len(lines) - len(truncated)
    suffix = f" … +{omitted} more" if omitted > 0 else ""
    body = "\n".join(truncated)
    return body + suffix if body else (suffix.strip() or "no history")


def _trim_str(value: str, max_chars: int = 200) -> str:
    return value[:max_chars] + "…" if len(value) > max_chars else value


def compress(report: dict[str, Any], cfg: CompressConfig) -> dict[str, Any]:
    """Compress a Codebase Context Report to minimal token form.

    Deduplicates and truncates each field according to cfg limits.
    Returns a new dict with a ``_compressed`` savings annotation.
    """
    if not isinstance(report, dict):
        raise TypeError(f"expected a JSON object (dict), got {type(report).__name__}")
    out: dict[str, Any] = {}

    # Always keep — zero token cost to preserve
    out["feature_area"] = report.get("feature_area", "")
    out["scope"] = report.get("scope", "M")
    out["scope_reasoning"] = _trim_str(report.get("scope_reasoning", ""), 150)

    # Related files — cap count, truncate git log, preserve test coverage signals
    raw_files: list[Any] = report.get("related_files", [])
    out["related_files"] = []
    for f in raw_files[: cfg.max_files]:
        if not isinstance(f, dict):
            raise TypeError(
                f"expected related_files entries to be objects, got {type(f).__name__}"
            )
        out["related_files"].append(
            {
                "path": f.get("path", ""),
                "last_commit": _truncate_git_log(
                    f.get("last_commit", ""), cfg.max_log_lines
                ),
                "has_tests": f.get("has_tests", False),
                "test_file": f.get("test_file", ""),
            }
        )

    # Deduplicate and cap list fields
    out["interface_shapes"] = _dedupe_stable(report.get("interface_shapes", []))[
        : cfg.max_interface_shapes
    ]
    out["constraints"] = _dedupe_stable(report.get("constraints", []))[
        : cfg.max_constraints
    ]
    out["design_docs"] = _dedupe_stable(report.get("design_docs", []))[
        : cfg.max_design_docs
    ]
    out["unknowns"] = _dedupe_stable(report.get("unknowns", []))[: cfg.max_unknowns]

    # Analogous features — key for Creative Checkpoint and design-proposer Step 0
    out["analogous_features"] = _dedupe_stable(report.get("analogous_features", []))[
        : cfg.max_analogous
    ]

    _annotate_savings(report, out)
    return out


def _annotate_savings(original: dict[str, Any], compressed: dict[str, Any]) -> None:
    """Attach a brief savings summary so the agent knows what was trimmed."""
    orig_files = len(original.get("related_files", []))
    kept_files = len(compressed.get("related_files", []))
    orig_shapes = len(original.get("interface_shapes", []))
    kept_shapes = len(compressed.get("interface_shapes", []))

    notes: list[str] = []
    if orig_files > kept_files:
        notes.append(f"files {orig_files}→{kept_files}")
    if orig_shapes > kept_shapes:
        notes.append(f"shapes {orig_shapes}→{kept_shapes}")

    compressed["_compressed"] = (
        "trimmed: " + ", ".join(notes) if notes else "no trimming needed"
    )


def _non_negative_int(value: str) -> int:
    try:
        val = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid int value: {value!r}") from None
    if val < 0:
        raise argparse.ArgumentTypeError(f"value must be >= 0, got {val}")
    return val


_DEFAULTS = CompressConfig()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compress a Codebase Context Report for Phase 4"
    )
    parser.add_argument(
        "report", nargs="?", help="Path to report JSON (omit to read from stdin)"
    )
    parser.add_argument(
        "--max-files", type=_non_negative_int, default=_DEFAULTS.max_files
    )
    parser.add_argument(
        "--max-log-lines", type=_non_negative_int, default=_DEFAULTS.max_log_lines
    )
    parser.add_argument(
        "--max-constraints", type=_non_negative_int, default=_DEFAULTS.max_constraints
    )
    parser.add_argument(
        "--max-interface-shapes",
        type=_non_negative_int,
        default=_DEFAULTS.max_interface_shapes,
    )
    parser.add_argument(
        "--max-unknowns", type=_non_negative_int, default=_DEFAULTS.max_unknowns
    )
    parser.add_argument(
        "--max-design-docs", type=_non_negative_int, default=_DEFAULTS.max_design_docs
    )
    parser.add_argument(
        "--max-analogous", type=_non_negative_int, default=_DEFAULTS.max_analogous
    )
    args = parser.parse_args()

    try:
        if args.report:
            raw = json.loads(Path(args.report).read_text(encoding="utf-8"))
        else:
            raw = json.loads(sys.stdin.read())
    except FileNotFoundError as exc:
        sys.exit(f"error: report file not found — {exc}")
    except PermissionError as exc:
        sys.exit(f"error: cannot read report file — {exc}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: invalid JSON — {exc}")
    except (OSError, EOFError) as exc:
        sys.exit(f"error: failed to read input — {exc}")

    cfg = CompressConfig(
        max_files=args.max_files,
        max_log_lines=args.max_log_lines,
        max_constraints=args.max_constraints,
        max_interface_shapes=args.max_interface_shapes,
        max_unknowns=args.max_unknowns,
        max_design_docs=args.max_design_docs,
        max_analogous=args.max_analogous,
    )
    try:
        compressed = compress(raw, cfg)
    except TypeError as exc:
        sys.exit(f"error: {exc}")
    print(json.dumps(compressed, indent=2))


if __name__ == "__main__":
    main()
