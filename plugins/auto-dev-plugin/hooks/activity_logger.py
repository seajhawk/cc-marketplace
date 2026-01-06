#!/usr/bin/env python3
"""
Activity logger for autonomous-dev plugin.
Logs hook events to a JSONL file for analysis.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def get_plugin_dir() -> Path:
    """Get the plugin directory."""
    return Path(__file__).parent.parent


def get_config() -> dict:
    """Load plugin configuration."""
    config_path = get_plugin_dir() / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"logging": {"enabled": True, "logFile": "logs/activity.jsonl"}}


def get_log_path() -> Path:
    """Get the log file path, creating directory if needed."""
    config = get_config()
    log_file = config.get("logging", {}).get("logFile", "logs/activity.jsonl")
    log_path = get_plugin_dir() / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def log_activity(event_type: str, hook_name: str, data: dict = None, success: bool = True) -> None:
    """
    Log an activity event to the activity log.

    Args:
        event_type: Type of event (e.g., "prompt_classification", "subagent_test_gate")
        hook_name: Name of the hook that triggered this event
        data: Additional event-specific data
        success: Whether the event was successful
    """
    config = get_config()
    if not config.get("logging", {}).get("enabled", True):
        return

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "hook": hook_name,
        "success": success,
        "data": data or {}
    }

    try:
        log_path = get_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        # Silently fail - logging should never break the hook
        pass


def log_prompt_classification(
    prompt_preview: str,
    classification: str,
    is_multi_request: bool = False,
    request_count: int = 1,
    coding_count: int = 0,
    quick_count: int = 0
) -> None:
    """Log a prompt classification event."""
    log_activity(
        event_type="prompt_classification",
        hook_name="UserPromptSubmit",
        data={
            "prompt_preview": prompt_preview[:100],
            "classification": classification,
            "is_multi_request": is_multi_request,
            "request_count": request_count,
            "coding_count": coding_count,
            "quick_count": quick_count
        }
    )


def log_subagent_stop(
    tests_passed: bool,
    backend_passed: bool = None,
    frontend_passed: bool = None,
    blocked: bool = False,
    error_summary: str = None
) -> None:
    """Log a subagent stop test gate event."""
    log_activity(
        event_type="subagent_test_gate",
        hook_name="SubagentStop",
        success=tests_passed,
        data={
            "tests_passed": tests_passed,
            "backend_passed": backend_passed,
            "frontend_passed": frontend_passed,
            "blocked": blocked,
            "error_summary": error_summary[:500] if error_summary else None
        }
    )


def log_session_stop(
    code_modified: bool,
    tests_run: bool,
    tests_passed: bool = None,
    files_changed: list = None
) -> None:
    """Log a session stop event."""
    log_activity(
        event_type="session_stop",
        hook_name="Stop",
        success=tests_passed if tests_run else True,
        data={
            "code_modified": code_modified,
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "files_changed": files_changed or []
        }
    )
