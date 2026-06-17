import os
import json
import time
import sys
import argparse
from pathlib import Path

# Detect PROJECT_ROOT relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BLACKBOARD_FILE = PROJECT_ROOT / ".agent_blackboard.json"
LOCK_FILE = BLACKBOARD_FILE.with_suffix(".json.lock")

def acquire_lock(timeout=10, retry_interval=0.05):
    """
    Acquire a lock using a lock file. 
    Uses os.O_EXCL for atomic creation on Windows and Linux.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # os.O_CREAT | os.O_EXCL ensures atomicity
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode('utf-8'))
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            time.sleep(retry_interval)
        except PermissionError:
            # On Windows, sometimes PermissionError is raised if the file is being deleted or in a weird state
            time.sleep(retry_interval)
    return False

def release_lock():
    """
    Release the lock by removing the lock file.
    """
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except (FileNotFoundError, PermissionError):
        pass

def read_blackboard():
    """
    Reads the blackboard JSON file. Assumes lock is held.
    """
    if not BLACKBOARD_FILE.exists():
        return {}
    try:
        with open(BLACKBOARD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        # Re-raise to avoid overwriting blackboard with {} on transient read failures
        raise

def write_blackboard(data):
    """
    Writes the blackboard JSON file. Assumes lock is held.
    """
    # Write to a temporary file first for extra safety, though lock should handle it
    temp_file = BLACKBOARD_FILE.with_suffix(".json.tmp")
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    # Atomic replace
    os.replace(temp_file, BLACKBOARD_FILE)

def read(key):
    """
    Read a key from the blackboard with locking.
    """
    if acquire_lock():
        try:
            data = read_blackboard()
            return data.get(key)
        finally:
            release_lock()
    else:
        raise TimeoutError(f"Could not acquire lock for reading {key}")

def write(key, value):
    """
    Write a key-value pair to the blackboard with locking.
    """
    if acquire_lock():
        try:
            data = read_blackboard()
            data[key] = value
            write_blackboard(data)
        finally:
            release_lock()
    else:
        raise TimeoutError(f"Could not acquire lock for writing {key}={value}")

def main():
    parser = argparse.ArgumentParser(description="Shared Context Blackboard CLI")
    subparsers = parser.add_subparsers(dest="command")

    set_parser = subparsers.add_parser("set")
    set_parser.add_argument("key")
    set_parser.add_argument("value")

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("key")

    args = parser.parse_args()

    try:
        if args.command == "set":
            write(args.key, args.value)
            # print(f"Set {args.key} = {args.value}")
        elif args.command == "get":
            val = read(args.key)
            if val is not None:
                print(val)
            else:
                sys.exit(1)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
