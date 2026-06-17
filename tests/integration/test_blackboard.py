import subprocess
import sys
import os
import pytest
import concurrent.futures
from pathlib import Path
import json

# Path to blackboard.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BLACKBOARD_SCRIPT = PROJECT_ROOT / "skills" / "multi-agent-dispatch" / "scripts" / "blackboard.py"
BLACKBOARD_FILE = PROJECT_ROOT / ".agent_blackboard.json"

def run_blackboard_cli(*args):
    result = subprocess.run(
        [sys.executable, str(BLACKBOARD_SCRIPT)] + list(args),
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    return result

@pytest.fixture(autouse=True)
def cleanup_blackboard():
    if BLACKBOARD_FILE.exists():
        BLACKBOARD_FILE.unlink()
    lock_file = BLACKBOARD_FILE.with_suffix(".json.lock")
    if lock_file.exists():
        lock_file.unlink()
    yield
    if BLACKBOARD_FILE.exists():
        BLACKBOARD_FILE.unlink()
    if lock_file.exists():
        lock_file.unlink()

def test_basic_set_get():
    run_blackboard_cli("set", "test_key", "test_value")
    result = run_blackboard_cli("get", "test_key")
    assert result.stdout.strip() == "test_value"

def test_overwriting_value():
    run_blackboard_cli("set", "test_key", "value1")
    run_blackboard_cli("set", "test_key", "value2")
    result = run_blackboard_cli("get", "test_key")
    assert result.stdout.strip() == "value2"

def test_multiple_keys():
    run_blackboard_cli("set", "key1", "val1")
    run_blackboard_cli("set", "key2", "val2")
    
    assert run_blackboard_cli("get", "key1").stdout.strip() == "val1"
    assert run_blackboard_cli("get", "key2").stdout.strip() == "val2"

def worker_fn(worker_id):
    # Each worker writes its own key
    run_blackboard_cli("set", f"worker_{worker_id}", f"value_{worker_id}")
    return worker_id

def test_concurrency_robustness():
    """
    Spawn multiple processes to write to the blackboard simultaneously.
    Verifies that the lock mechanism prevents corruption and all writes eventually succeed.
    """
    num_workers = 15
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_fn, i) for i in range(num_workers)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    assert len(results) == num_workers
    
    # Verify all keys are present and correct
    with open(BLACKBOARD_FILE, 'r') as f:
        data = json.load(f)
        for i in range(num_workers):
            assert data.get(f"worker_{i}") == f"value_{i}"

def test_error_on_missing_key():
    result = run_blackboard_cli("get", "non_existent_key")
    assert result.returncode != 0
