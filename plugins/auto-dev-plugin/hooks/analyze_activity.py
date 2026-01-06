#!/usr/bin/env python3
"""
Analyze Claude Code activity logs and display usage metrics.

Usage:
    python hooks/analyze_activity.py
    python hooks/analyze_activity.py --days 7
    python hooks/analyze_activity.py --json

Part of the autonomous-dev plugin.
"""
import json
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict


def get_plugin_dir() -> Path:
    """Get the plugin directory."""
    return Path(__file__).parent.parent


def get_config() -> dict:
    """Load plugin configuration."""
    config_path = get_plugin_dir() / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"logging": {"logFile": "logs/activity.jsonl"}}


def load_activity_log(log_path: Path, days: int = None) -> list:
    """Load activity log entries, optionally filtering by date."""
    if not log_path.exists():
        return []

    entries = []
    cutoff = None
    if days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if cutoff:
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    if entry_time < cutoff:
                        continue
                entries.append(entry)
            except (json.JSONDecodeError, KeyError):
                continue

    return entries


def analyze_entries(entries: list) -> dict:
    """Analyze log entries and compute metrics."""
    metrics = {
        "total_events": len(entries),
        "date_range": {"start": None, "end": None},
        "prompts": {
            "total": 0,
            "coding_tasks": 0,
            "quick_questions": 0,
            "multi_request": 0,
        },
        "subagent_stops": {
            "total": 0,
            "passed": 0,
            "blocked": 0,
            "backend_failures": 0,
            "frontend_failures": 0,
        },
        "session_stops": {
            "total": 0,
            "with_code_changes": 0,
            "without_code_changes": 0,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
        },
        "by_day": defaultdict(lambda: {"prompts": 0, "subagent_stops": 0, "session_stops": 0}),
        "by_hour": defaultdict(int),
    }

    for entry in entries:
        timestamp = datetime.fromisoformat(entry["timestamp"])
        day_key = timestamp.strftime("%Y-%m-%d")
        hour_key = timestamp.hour

        if metrics["date_range"]["start"] is None or timestamp.isoformat() < metrics["date_range"]["start"]:
            metrics["date_range"]["start"] = timestamp.isoformat()
        if metrics["date_range"]["end"] is None or timestamp.isoformat() > metrics["date_range"]["end"]:
            metrics["date_range"]["end"] = timestamp.isoformat()

        event_type = entry.get("event_type", "")
        data = entry.get("data", {})

        if event_type == "prompt_classification":
            metrics["prompts"]["total"] += 1
            metrics["by_day"][day_key]["prompts"] += 1
            metrics["by_hour"][hour_key] += 1

            classification = data.get("classification", "")
            if classification == "CODING_TASK":
                metrics["prompts"]["coding_tasks"] += 1
            else:
                metrics["prompts"]["quick_questions"] += 1

            if data.get("is_multi_request"):
                metrics["prompts"]["multi_request"] += 1

        elif event_type == "subagent_test_gate":
            metrics["subagent_stops"]["total"] += 1
            metrics["by_day"][day_key]["subagent_stops"] += 1

            if data.get("tests_passed"):
                metrics["subagent_stops"]["passed"] += 1
            if data.get("blocked"):
                metrics["subagent_stops"]["blocked"] += 1
            if data.get("backend_passed") is False:
                metrics["subagent_stops"]["backend_failures"] += 1
            if data.get("frontend_passed") is False:
                metrics["subagent_stops"]["frontend_failures"] += 1

        elif event_type == "session_stop":
            metrics["session_stops"]["total"] += 1
            metrics["by_day"][day_key]["session_stops"] += 1

            if data.get("code_modified"):
                metrics["session_stops"]["with_code_changes"] += 1
            else:
                metrics["session_stops"]["without_code_changes"] += 1

            if data.get("tests_run"):
                metrics["session_stops"]["tests_run"] += 1
                if data.get("tests_passed"):
                    metrics["session_stops"]["tests_passed"] += 1
                else:
                    metrics["session_stops"]["tests_failed"] += 1

    metrics["by_day"] = dict(metrics["by_day"])
    metrics["by_hour"] = dict(metrics["by_hour"])

    return metrics


def print_report(metrics: dict):
    """Print a human-readable report."""
    print("=" * 60)
    print("AUTONOMOUS-DEV ACTIVITY REPORT")
    print("=" * 60)
    print()

    if metrics["date_range"]["start"]:
        print(f"Date Range: {metrics['date_range']['start'][:10]} to {metrics['date_range']['end'][:10]}")
    print(f"Total Events: {metrics['total_events']}")
    print()

    p = metrics["prompts"]
    print("PROMPT CLASSIFICATION")
    print("-" * 40)
    print(f"  Total Prompts:      {p['total']}")
    print(f"  Coding Tasks:       {p['coding_tasks']} ({p['coding_tasks']/max(1,p['total'])*100:.1f}%)")
    print(f"  Quick Questions:    {p['quick_questions']} ({p['quick_questions']/max(1,p['total'])*100:.1f}%)")
    print(f"  Multi-Request:      {p['multi_request']}")
    print()

    s = metrics["subagent_stops"]
    print("SUBAGENT TEST GATES")
    print("-" * 40)
    print(f"  Total Completions:  {s['total']}")
    print(f"  Tests Passed:       {s['passed']} ({s['passed']/max(1,s['total'])*100:.1f}%)")
    print(f"  Blocked:            {s['blocked']}")
    print(f"  Backend Failures:   {s['backend_failures']}")
    print(f"  Frontend Failures:  {s['frontend_failures']}")
    print()

    ss = metrics["session_stops"]
    print("SESSION STOPS")
    print("-" * 40)
    print(f"  Total Sessions:     {ss['total']}")
    print(f"  With Code Changes:  {ss['with_code_changes']}")
    print(f"  Without Changes:    {ss['without_code_changes']}")
    print(f"  Tests Run:          {ss['tests_run']}")
    print(f"  Tests Passed:       {ss['tests_passed']}")
    print(f"  Tests Failed:       {ss['tests_failed']}")
    print()

    if metrics["by_hour"]:
        print("ACTIVITY BY HOUR")
        print("-" * 40)
        for hour in sorted(metrics["by_hour"].keys()):
            count = metrics["by_hour"][hour]
            bar = "#" * min(count, 30)
            print(f"  {hour:02d}:00  {bar} ({count})")
        print()

    if metrics["by_day"]:
        print("DAILY ACTIVITY (last 7 days)")
        print("-" * 40)
        sorted_days = sorted(metrics["by_day"].keys(), reverse=True)[:7]
        for day in reversed(sorted_days):
            data = metrics["by_day"][day]
            print(f"  {day}: {data['prompts']} prompts, {data['subagent_stops']} subagents")

    print()
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Analyze autonomous-dev activity logs")
    parser.add_argument("--days", type=int, help="Only analyze last N days")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    config = get_config()
    log_file = config.get("logging", {}).get("logFile", "logs/activity.jsonl")
    log_path = get_plugin_dir() / log_file

    if not log_path.exists():
        print(f"No activity log found at {log_path}")
        print("Activity logging starts with your next Claude Code interaction.")
        return

    entries = load_activity_log(log_path, days=args.days)

    if not entries:
        print("No activity entries found.")
        return

    metrics = analyze_entries(entries)

    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print_report(metrics)


if __name__ == "__main__":
    main()
