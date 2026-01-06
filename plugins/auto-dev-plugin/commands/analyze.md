---
description: Analyze Claude Code activity logs and display usage metrics
---

# Analyze Activity

Run the activity analyzer to see usage metrics:

```bash
python hooks/analyze_activity.py
```

Options:
- `--days N` - Only analyze last N days
- `--json` - Output as JSON for programmatic use

The analyzer shows:
- Prompt classifications (coding vs quick questions)
- Subagent test gate results (passed, blocked, failures)
- Session stops (with/without code changes)
- Activity by hour and day
