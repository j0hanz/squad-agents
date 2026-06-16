"""Tests for brainstorming compress_report."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import compress_report  # noqa: E402


def test_compress_report_empty():
    report = {"feature_area": "Test", "related_files": []}
    cfg = compress_report.CompressConfig()
    compressed = compress_report.compress(report, cfg)
    assert isinstance(compressed, dict)
    assert compressed["feature_area"] == "Test"
    assert "_compressed" in compressed


def test_compress_report_with_data():
    report = {
        "feature_area": "Test",
        "related_files": [
            {"path": "src/main.py", "last_commit": "Initial commit", "has_tests": True}
        ],
        "unknowns": ["How is auth handled?"],
        "analogous_features": ["Auth"],
    }
    cfg = compress_report.CompressConfig()
    compressed = compress_report.compress(report, cfg)
    assert compressed["related_files"][0]["path"] == "src/main.py"
    assert "How is auth handled?" in compressed["unknowns"]
    assert "Auth" in compressed["analogous_features"]
