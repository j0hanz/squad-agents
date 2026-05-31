"""Shared JSON utilities for skill-builder scripts."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_json(path: Path) -> Any:
    """Safely load JSON from a file, logging errors."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error(f"Failed to read file {path}: {e}")
        raise
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {path}: {e}")
        raise


def save_json(path: Path, data: Any, indent: int = 2) -> None:
    """Safely save JSON to a file."""
    try:
        path.write_text(json.dumps(data, indent=indent), encoding="utf-8")
    except OSError as e:
        logger.error(f"Failed to write JSON to {path}: {e}")
        raise
