#!/usr/bin/env python3
"""Regression tests for lint.py"""

import sys
from pathlib import Path

# Add current directory to path so lint module can be imported
sys.path.insert(0, str(Path(__file__).parent))

import textwrap
import tempfile
import pathlib
from lint import check_file


def test_injection_at_minimum_block_indent():
    """Verify injection at exactly run_block_indent indentation is caught."""
    # Block scalar where content starts at minimum indent level
    content = textwrap.dedent("""\
        jobs:
          test:
            run: |
              echo ${{ github.event.pull_request.title }}
        permissions: write-all
        """)
    with tempfile.NamedTemporaryFile(suffix=".yml", mode="w", delete=False) as f:
        f.write(content)
        path = pathlib.Path(f.name)
    try:
        errors = check_file(path)
        assert any("injection" in e.lower() for e in errors), (
            f"Expected injection error, got: {errors}"
        )
        print("PASS: injection at minimum block indent is caught")
    finally:
        path.unlink()


def test_pull_request_target_two_line_footgun_caught():
    """The real-world vulnerable pattern spans two lines: `ref:` is nested under `with:`."""
    content = textwrap.dedent("""\
        on: pull_request_target
        permissions: read-all
        jobs:
          test:
            steps:
              - uses: actions/checkout@v4
                with:
                  ref: ${{ github.event.pull_request.head.sha }}
        """)
    with tempfile.NamedTemporaryFile(suffix=".yml", mode="w", delete=False) as f:
        f.write(content)
        path = pathlib.Path(f.name)
    try:
        errors = check_file(path)
        assert any("footgun" in e.lower() for e in errors), (
            f"Expected pull_request_target footgun error, got: {errors}"
        )
    finally:
        path.unlink()


def test_workflow_dispatch_input_injection_caught():
    """workflow_dispatch inputs interpolated into run: are an injection vector too."""
    content = textwrap.dedent("""\
        permissions: read-all
        jobs:
          test:
            steps:
              - name: echo input
                run: echo ${{ github.event.inputs.target }}
        """)
    with tempfile.NamedTemporaryFile(suffix=".yml", mode="w", delete=False) as f:
        f.write(content)
        path = pathlib.Path(f.name)
    try:
        errors = check_file(path)
        assert any("injection" in e.lower() for e in errors), (
            f"Expected injection error, got: {errors}"
        )
    finally:
        path.unlink()


if __name__ == "__main__":
    test_injection_at_minimum_block_indent()
    test_pull_request_target_two_line_footgun_caught()
    test_workflow_dispatch_input_injection_caught()
