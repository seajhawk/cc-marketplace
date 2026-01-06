#!/usr/bin/env python3
"""
Simple logging hook for UserPromptSubmit.
Logs prompts to activity.jsonl without doing any classification.
Designed to run alongside a prompt-type classifier hook.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

LOG_FILE = Path(__file__).parent.parent / "logs" / "activity.jsonl"


def log_prompt(prompt_preview: str):
    """Log prompt submission to activity file."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "prompt_submitted",
            "hook": "UserPromptSubmit",
            "success": True,
            "data": {
                "prompt_preview": prompt_preview[:100]
            }
        }

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Silent fail - logging should never break the workflow


def main():
    try:
        input_data = json.load(sys.stdin)
        prompt = input_data.get("prompt", "")

        if prompt and prompt.strip():
            log_prompt(prompt)

        # Output nothing - let the prompt-type hook handle classification
        sys.exit(0)

    except Exception:
        sys.exit(0)  # Never fail


if __name__ == "__main__":
    main()
