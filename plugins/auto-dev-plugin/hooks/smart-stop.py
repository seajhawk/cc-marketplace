#!/usr/bin/env python3
"""
Stop hook - Only runs tests if code was modified.
Prevents unnecessary test runs for quick questions/exploration.

Part of the autonomous-dev plugin.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# Import activity logger
try:
    from activity_logger import log_session_stop
except ImportError:
    def log_session_stop(*args, **kwargs): pass


def get_plugin_dir() -> Path:
    """Get the plugin directory."""
    return Path(__file__).parent.parent


def get_config() -> dict:
    """Load plugin configuration."""
    config_path = get_plugin_dir() / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_project_dir() -> str:
    """Get project directory from env or current working directory."""
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        path = os.environ["CLAUDE_PROJECT_DIR"]
    else:
        path = os.getcwd()

    # Normalize Windows path
    if len(path) >= 2 and path[1] == ':':
        path = path[0].upper() + path[1:]
    return path


def get_code_changes(project_dir: str) -> list:
    """Check if any source code files were modified. Returns list of changed files."""
    config = get_config()
    code_extensions = set(config.get("codeExtensions", [".py", ".ts", ".tsx", ".js", ".jsx"]))
    code_files_changed = []

    try:
        # Check unstaged changes
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        modified = result.stdout.strip().split('\n') if result.stdout.strip() else []

        # Check staged changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        staged = result.stdout.strip().split('\n') if result.stdout.strip() else []

        # Check if any have code extensions
        all_changes = modified + staged
        for filename in all_changes:
            ext = os.path.splitext(filename)[1]
            if ext in code_extensions:
                code_files_changed.append(filename)

        return code_files_changed
    except Exception:
        return []


def run_test_command(name: str, config: dict, project_dir: str) -> tuple[bool, str]:
    """Run a single test command."""
    if not config.get("enabled", True):
        return True, ""

    directory = os.path.join(project_dir, config.get("directory", "."))
    command = config.get("command", "npm test")
    timeout = config.get("timeout", 120)

    print(f"Running {name} tests...", file=sys.stderr)

    try:
        result = subprocess.run(
            command,
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True
        )
        if result.returncode != 0:
            return False, f"{name} tests failed:\n{result.stdout}\n{result.stderr}"
        return True, ""
    except subprocess.TimeoutExpired:
        return False, f"{name} tests timed out after {timeout} seconds"
    except Exception as e:
        return False, f"{name} tests error: {e}"


def run_tests(project_dir: str) -> tuple[bool, str]:
    """Run all configured tests."""
    config = get_config()
    test_commands = config.get("testCommands", {})
    failures = []

    for name, test_config in test_commands.items():
        if test_config.get("enabled", False):
            passed, output = run_test_command(name, test_config, project_dir)
            if not passed:
                failures.append(output)

    return len(failures) == 0, "\n\n".join(failures)


def main():
    print("=== Smart Stop Hook ===", file=sys.stderr)

    project_dir = get_project_dir()

    # Check if any code changes exist
    changed_files = get_code_changes(project_dir)
    if not changed_files:
        print("No code changes detected, skipping tests.", file=sys.stderr)
        log_session_stop(
            code_modified=False,
            tests_run=False,
            tests_passed=None,
            files_changed=[]
        )
        sys.exit(0)

    print(f"Code changes detected ({len(changed_files)} files), running tests...", file=sys.stderr)
    success, output = run_tests(project_dir)

    log_session_stop(
        code_modified=True,
        tests_run=True,
        tests_passed=success,
        files_changed=changed_files
    )

    if not success:
        print("Tests failed! Blocking stop.", file=sys.stderr)
        result = {
            "decision": "block",
            "reason": f"Tests failed. Please fix the issues before stopping:\n\n{output}"
        }
        print(json.dumps(result))
    else:
        print("All tests passed!", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
