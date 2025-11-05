"""
Utility functions for Claude Orchestrator.

This module provides helper functions for hashing, time management, git operations,
schema validation, and audit logging.
"""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union
import os


# ============================================================================
# Hash Functions
# ============================================================================

def sha256(obj: Any) -> str:
    """
    Generate a SHA-256 hash of a JSON object deterministically.

    Args:
        obj: Any JSON-serializable object (dict, list, str, int, etc.)

    Returns:
        Hexadecimal string representation of the SHA-256 hash

    Raises:
        TypeError: If object is not JSON-serializable

    Example:
        >>> sha256({"task": "example", "id": 1})
        'a1b2c3d4...'
    """
    try:
        # Ensure deterministic JSON serialization with sorted keys
        json_str = json.dumps(obj, sort_keys=True, separators=(',', ':'))
        # Encode to bytes and hash
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    except (TypeError, ValueError) as e:
        raise TypeError(f"Object is not JSON-serializable: {e}")


def hash_json(obj: Any) -> str:
    """
    Alias for sha256() function.

    Generate a SHA-256 hash of a JSON object deterministically.

    Args:
        obj: Any JSON-serializable object

    Returns:
        Hexadecimal string representation of the SHA-256 hash

    Example:
        >>> hash_json({"task": "example"})
        'a1b2c3d4...'
    """
    return sha256(obj)


# ============================================================================
# Time Utilities
# ============================================================================

def now_iso() -> str:
    """
    Return current UTC timestamp in ISO 8601 format.

    Returns:
        ISO 8601 formatted timestamp string (e.g., '2025-10-23T14:30:45.123456Z')

    Example:
        >>> now_iso()
        '2025-10-23T14:30:45.123456Z'
    """
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


# ============================================================================
# Git Utilities
# ============================================================================

def repo_root() -> str:
    """
    Return absolute path to current git repository root.

    Returns:
        Absolute path to repository root directory

    Raises:
        RuntimeError: If not in a git repository or git command fails

    Example:
        >>> repo_root()
        '/home/user/my-project'
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Not in a git repository or git command failed: {e.stderr.strip()}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git command timed out")
    except FileNotFoundError:
        raise RuntimeError("Git executable not found. Is git installed?")


def run(cmd: Union[str, list], cwd: Optional[str] = None) -> str:
    """
    Execute shell command and return output.

    Args:
        cmd: Command to execute (string or list of arguments)
        cwd: Working directory for command execution (defaults to current directory)

    Returns:
        Standard output from the command as a string

    Raises:
        RuntimeError: If command execution fails

    Example:
        >>> run("echo hello")
        'hello\\n'
        >>> run(["git", "status", "--short"], cwd="/path/to/repo")
        'M file.txt\\n'
    """
    try:
        # Convert string command to list for subprocess
        if isinstance(cmd, str):
            cmd_list = cmd.split()
        else:
            cmd_list = cmd

        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
            timeout=30
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Command failed with exit code {e.returncode}: {e.stderr.strip()}"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Command timed out: {cmd}")
    except FileNotFoundError:
        cmd_name = cmd_list[0] if cmd_list else "unknown"
        raise RuntimeError(f"Command not found: {cmd_name}")


# ============================================================================
# Schema Validation
# ============================================================================

def validate_schema(obj: Any, schema: Dict[str, Any]) -> bool:
    """
    Validate JSON object against schema using jsonschema library.

    Args:
        obj: JSON object to validate
        schema: JSON schema to validate against

    Returns:
        True if validation succeeds

    Raises:
        ValidationError: If object doesn't match schema
        ImportError: If jsonschema library is not installed

    Example:
        >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> validate_schema({"name": "test"}, schema)
        True
    """
    try:
        from jsonschema import validate, ValidationError

        validate(instance=obj, schema=schema)
        return True
    except ImportError:
        raise ImportError(
            "jsonschema library is required. Install it with: pip install jsonschema"
        )
    except ValidationError as e:
        raise ValidationError(f"Schema validation failed: {e.message}")


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load schema file from schemas directory.

    Args:
        schema_name: Name of schema file (with or without .json extension)

    Returns:
        Loaded JSON schema as a dictionary

    Raises:
        FileNotFoundError: If schema file doesn't exist
        json.JSONDecodeError: If schema file contains invalid JSON

    Example:
        >>> schema = load_schema("task_schema")
        >>> schema = load_schema("task_schema.json")
    """
    # Determine the schemas directory relative to this file
    utils_dir = Path(__file__).parent
    schemas_dir = utils_dir / "schemas"

    # Add .json extension if not present
    if not schema_name.endswith('.json'):
        schema_name = f"{schema_name}.json"

    schema_path = schemas_dir / schema_name

    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found: {schema_path}\n"
            f"Available schemas: {', '.join(f.name for f in schemas_dir.glob('*.json'))}"
            if schemas_dir.exists() else f"Schema directory not found: {schemas_dir}"
        )

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in schema file {schema_path}: {e.msg}",
            e.doc,
            e.pos
        )


# ============================================================================
# Audit Logging
# ============================================================================

def write_audit_log(entry: Dict[str, Any], log_path: str = "audit_trail.json") -> None:
    """
    Append audit entry to log file.

    The log file is maintained as a JSON array. If the file doesn't exist,
    it will be created. Entries are appended atomically.

    Args:
        entry: Audit entry dictionary to append
        log_path: Path to audit log file (relative or absolute)

    Raises:
        OSError: If file operations fail
        json.JSONDecodeError: If existing log file contains invalid JSON

    Example:
        >>> entry = create_audit_entry("task-123", "started", {"agent": "worker-1"})
        >>> write_audit_log(entry)
        >>> write_audit_log(entry, log_path="/var/log/audit.json")
    """
    # Convert to absolute path if relative
    log_file = Path(log_path)
    if not log_file.is_absolute():
        # Default to current working directory
        log_file = Path.cwd() / log_file

    # Ensure parent directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Read existing entries or start with empty list
    entries = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    entries = json.loads(content)
                    if not isinstance(entries, list):
                        raise ValueError("Audit log must be a JSON array")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Existing audit log file contains invalid JSON: {e.msg}",
                e.doc,
                e.pos
            )

    # Append new entry
    entries.append(entry)

    # Write back atomically using temporary file
    temp_file = log_file.with_suffix('.tmp')
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
            f.write('\n')

        # Atomic replace
        temp_file.replace(log_file)
    except Exception as e:
        # Clean up temp file on error
        if temp_file.exists():
            temp_file.unlink()
        raise OSError(f"Failed to write audit log: {e}")


def create_audit_entry(
    task_id: str,
    action: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create structured audit entry.

    Args:
        task_id: Unique identifier for the task
        action: Action being audited (e.g., 'started', 'completed', 'failed')
        details: Optional additional details about the action

    Returns:
        Structured audit entry dictionary with timestamp, task_id, action, and details

    Example:
        >>> entry = create_audit_entry("task-123", "started", {"agent": "worker-1"})
        >>> entry
        {
            'timestamp': '2025-10-23T14:30:45.123456Z',
            'task_id': 'task-123',
            'action': 'started',
            'details': {'agent': 'worker-1'}
        }
    """
    entry = {
        'timestamp': now_iso(),
        'task_id': task_id,
        'action': action
    }

    if details is not None:
        entry['details'] = details

    return entry


# ============================================================================
# Module Testing
# ============================================================================

if __name__ == "__main__":
    # Simple test cases
    print("Testing utility functions...")

    # Test hash functions
    test_obj = {"task": "example", "id": 1}
    hash1 = sha256(test_obj)
    hash2 = hash_json(test_obj)
    assert hash1 == hash2, "Hash functions should return same result"
    print(f"✓ Hash functions work: {hash1[:16]}...")

    # Test time utility
    timestamp = now_iso()
    assert timestamp.endswith('Z'), "Timestamp should end with Z"
    print(f"✓ Time utility works: {timestamp}")

    # Test audit entry creation
    entry = create_audit_entry("test-123", "test", {"key": "value"})
    assert entry['task_id'] == "test-123", "Task ID should match"
    assert entry['action'] == "test", "Action should match"
    assert 'timestamp' in entry, "Entry should have timestamp"
    print(f"✓ Audit entry creation works")

    # Test run command
    try:
        output = run("echo test")
        assert "test" in output, "Echo command should work"
        print(f"✓ Run command works")
    except RuntimeError as e:
        print(f"⚠ Run command test skipped: {e}")

    print("\nAll basic tests passed!")
