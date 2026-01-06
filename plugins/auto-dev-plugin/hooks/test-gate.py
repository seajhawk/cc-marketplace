#!/usr/bin/env python3
"""
SubagentStop hook - Runs tests when a subagent completes.
Blocks completion if tests fail, forcing the agent to fix issues.

Part of the autonomous-dev plugin.
Configurable via config.json.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# Import activity logger
try:
    from activity_logger import log_subagent_stop
except ImportError:
    def log_subagent_stop(*args, **kwargs): pass


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

    # Normalize Windows path to have uppercase drive letter
    if len(path) >= 2 and path[1] == ':':
        path = path[0].upper() + path[1:]
    return path


def run_test_command(name: str, config: dict, project_dir: str) -> tuple[bool, str]:
    """Run a single test command. Returns (passed, output)."""
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


def run_tests(project_dir: str) -> tuple[bool, bool, bool, str]:
    """Run all configured tests. Returns (all_passed, backend_passed, frontend_passed, output)."""
    config = get_config()
    test_commands = config.get("testCommands", {})

    failures = []
    backend_passed = True
    frontend_passed = True

    # Run backend tests
    backend_config = test_commands.get("backend", {"enabled": False})
    if backend_config.get("enabled", False):
        passed, output = run_test_command("backend", backend_config, project_dir)
        backend_passed = passed
        if not passed:
            failures.append(output)

    # Run frontend tests
    frontend_config = test_commands.get("frontend", {"enabled": False})
    if frontend_config.get("enabled", False):
        passed, output = run_test_command("frontend", frontend_config, project_dir)
        frontend_passed = passed
        if not passed:
            failures.append(output)

    all_passed = backend_passed and frontend_passed
    return all_passed, backend_passed, frontend_passed, "\n\n".join(failures)


def main():
    print("=== SubagentStop Test Gate ===", file=sys.stderr)
    print("Running tests to verify subagent work...", file=sys.stderr)

    project_dir = get_project_dir()
    all_passed, backend_passed, frontend_passed, output = run_tests(project_dir)

    # Log the test gate result
    log_subagent_stop(
        tests_passed=all_passed,
        backend_passed=backend_passed,
        frontend_passed=frontend_passed,
        blocked=not all_passed,
        error_summary=output if not all_passed else None
    )

    if not all_passed:
        print("Tests failed! Blocking subagent completion.", file=sys.stderr)
        result = {
            "decision": "block",
            "reason": f"Tests failed. Please fix the issues before completing:\n\n{output}"
        }
        print(json.dumps(result))
    else:
        print("All tests passed! Subagent may complete.", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
