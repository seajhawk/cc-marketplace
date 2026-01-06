# Claude Code Marketplace

A community-driven collection of plugins for Claude Code.

## Installation

Add this marketplace to Claude Code:

```
/plugin marketplace add CHarrisTech/cc-marketplace
```

Then install plugins:

```
/plugin install plugin-name@cc-marketplace
```

## Directory Structure

```
cc-marketplace/
├── .claude-plugin/
│   └── marketplace.json    # Marketplace registry
├── plugins/                # Plugin source files
└── README.md
```

## Plugin Types

Plugins can include:

| Type | Description |
|------|-------------|
| **Commands** | Slash commands that extend Claude's capabilities |
| **Agents** | Custom agent configurations |
| **Hooks** | Event-driven scripts that run on Claude Code actions |
| **MCP Servers** | Model Context Protocol servers for external integrations |

## Contributing a Plugin

1. Create a folder for your plugin under `plugins/`
2. Add your plugin files (commands, agents, hooks, or MCP server configs)
3. Add an entry to `.claude-plugin/marketplace.json`
4. Submit a pull request

### Plugin Entry Format

Add to the `plugins` array in `.claude-plugin/marketplace.json`:

```json
{
  "name": "my-plugin",
  "source": "./plugins/my-plugin",
  "description": "A brief description of what this plugin does",
  "version": "1.0.0",
  "author": {
    "name": "Your Name"
  },
  "license": "MIT",
  "keywords": ["utility", "productivity"],
  "commands": ["./commands/"],
  "agents": ["./agents/my-agent.md"],
  "hooks": {},
  "mcpServers": {}
}
```

### Plugin Folder Structure

```
plugins/my-plugin/
├── commands/           # Command markdown files
│   └── my-command.md
├── agents/             # Agent configurations
│   └── my-agent.md
├── hooks/              # Hook scripts
└── servers/            # MCP server binaries/scripts
```

## Validation

Test your plugin locally:

```
/plugin marketplace add ./path/to/cc-marketplace
/plugin install my-plugin@cc-marketplace
```

## License

Each plugin is licensed under its own terms as specified in its entry.
