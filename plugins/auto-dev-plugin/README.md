# auto-dev

**Autonomous development toolkit for Claude Code**

Enable "assign and walk away" workflows with test-gated subagents, intelligent prompt classification, and activity logging.

## Features

- **Test Gates** - Subagents are blocked from completing until tests pass
- **Prompt Classification** - Auto-routes coding tasks to subagents, answers questions directly
- **Multi-Request Detection** - Handles brain-dump prompts with multiple tasks
- **Smart Stop** - Only runs tests when code was actually modified
- **Activity Logging** - Track usage patterns and test gate effectiveness
- **Chrome MCP** - Browser automation for e2e testing

## Installation

### Local Testing

```bash
claude --plugin-dir ./auto-dev-plugin
```

### Permanent Installation

Copy to your Claude Code plugins directory or install from the plugin marketplace.

## Configuration

Edit `config.json` to customize for your project:

```json
{
  "testCommands": {
    "backend": {
      "enabled": true,
      "directory": ".",
      "command": "npm test",
      "timeout": 120
    },
    "frontend": {
      "enabled": false,
      "directory": "./frontend",
      "command": "npm test",
      "timeout": 120
    }
  },
  "codeExtensions": [".py", ".ts", ".tsx", ".js", ".jsx"],
  "logging": {
    "enabled": true,
    "logFile": "logs/activity.jsonl"
  }
}
```

### Test Command Options

| Field | Description |
|-------|-------------|
| `enabled` | Whether to run this test suite |
| `directory` | Working directory (relative to project root) |
| `command` | Shell command to run tests |
| `timeout` | Maximum seconds before timeout |

### Examples

**Node.js project:**
```json
{
  "testCommands": {
    "backend": {
      "enabled": true,
      "directory": ".",
      "command": "npm test"
    }
  }
}
```

**Python + React:**
```json
{
  "testCommands": {
    "backend": {
      "enabled": true,
      "directory": "./api",
      "command": "python -m pytest tests/ -q"
    },
    "frontend": {
      "enabled": true,
      "directory": "./web",
      "command": "npm test"
    }
  }
}
```

**Go project:**
```json
{
  "testCommands": {
    "backend": {
      "enabled": true,
      "directory": ".",
      "command": "go test ./..."
    }
  },
  "codeExtensions": [".go"]
}
```

## Hooks

### UserPromptSubmit - Prompt Classification

Analyzes every prompt and tells Claude how to handle it:

- **Coding tasks** → Suggests subagent delegation
- **Quick questions** → Answer directly
- **Multi-request** → Parallel subagents + direct answers

**Example classification:**
```
[MULTI_REQUEST: 5 tasks detected (3 coding, 2 quick)]
Tasks to handle:
  1. [CODING] Fix the bug where chart doesn't update
  2. [QUICK] Why is the API returning 404?
  3. [CODING] Add copy to clipboard button
  4. [QUICK] What's the difference between grid and spiral?
  5. [CODING] Refactor batch runner for cancellation

Execution guidance:
- PARALLEL: Launch multiple 'coder' subagents for CODING tasks
- Answer QUICK tasks directly
```

### SubagentStop - Test Gate

When a subagent completes, runs your test suite:

- **Tests pass** → Subagent completes normally
- **Tests fail** → Subagent is BLOCKED, must fix and retry

This creates a fundamentally different dynamic - the AI can't hand you broken code.

### Stop - Smart Stop

Only runs tests when code was modified:

- **No code changes** → Skip tests (fast exit for Q&A sessions)
- **Code changes** → Run full test suite

## Skills

### /auto-dev:subagents

Guide for effective subagent usage:
- When to delegate vs handle directly
- How to structure prompts for best results
- Best practices for autonomous workflows

### /auto-dev:interview

Deep-dive discovery before coding:
- Uncover hidden requirements
- Challenge assumptions
- Create specifications before implementation

## Commands

### /auto-dev:analyze

View activity metrics:

```bash
python hooks/analyze_activity.py
python hooks/analyze_activity.py --days 7
python hooks/analyze_activity.py --json
```

## MCP Servers

### Chrome DevTools

Browser automation for e2e testing. Claude can:
- Navigate to URLs
- Click elements
- Fill forms
- Take screenshots
- Verify UI behavior

Requires Chrome to be running with remote debugging enabled.

## How It Works

```
┌─────────────────┐
│  You type a     │
│  prompt         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ UserPromptSubmit│ ← Classifies as CODING or QUICK
│ Hook            │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ Quick │ │ Coding│ ← Spawns coder subagent
│ Answer│ │ Task  │
└───────┘ └───┬───┘
              │
              ▼
        ┌───────────┐
        │ Subagent  │ ← Works autonomously
        │ implements│
        └─────┬─────┘
              │
              ▼
        ┌───────────┐
        │SubagentStop│ ← Runs tests
        │ Hook       │
        └─────┬─────┘
              │
         Pass │ Fail
              │  ↓
              │ Block & retry
              ▼
        ┌───────────┐
        │ Complete  │
        └───────────┘
```

## Activity Logging

All hook events are logged to `logs/activity.jsonl`:

```json
{"timestamp": "2025-01-05T10:30:00Z", "event_type": "prompt_classification", "data": {...}}
{"timestamp": "2025-01-05T10:35:00Z", "event_type": "subagent_test_gate", "data": {...}}
```

Use `/auto-dev:analyze` to view metrics.

## Requirements

- Claude Code 1.0.33+
- Python 3.10+ (for hooks)
- Node.js (for Chrome MCP server)


## Test Prompt
1. create a file called "deleteme.py"
2. add a small python hello world script to the file
3. validate that it works
4. delete the file
5. tell me a joke
6. tell me if the python script worked

## License

MIT
