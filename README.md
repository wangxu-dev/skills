# AI Skills

A personal collection of custom AI assistant skills created and maintained by [wangxu](https://github.com/wangxu-dev).

## Overview

This repository houses custom skills I've built to enhance my workflow with AI assistants. Each skill is a self-contained module that extends AI capabilities through slash commands.

## What are AI Skills?

AI Skills are reusable assistant modules that can be invoked via slash commands (e.g., `/skill-name`). They allow you to package complex behaviors, workflows, or specialized functionality into easy-to-use commands.

These skills are compatible with multiple AI assistants that support custom skills, including:
- Claude (Claude Code, Cursor, etc.)
- OpenAI (Codex, ChatGPT, etc.)
- Gemini
- And other AI assistants with skill support

## Installation via mcp-skill-cli

The recommended way to install and manage these skills is through [mcp-skill-cli](https://github.com/wangxu-dev/mcp-skill-cli), a cross-platform CLI tool for managing MCP servers and skills.

```bash
# Install the CLI tool globally
npm install -g mcp-skill-cli

# List installed skills
skill list

# Install a skill from this repository
skill install work-session

# Uninstall a skill
skill uninstall work-session
```

The mcp-skill-cli tool handles:
- Automatic installation to the correct directory
- Client configuration updates
- Local cache management under `~/.mcp-skill/`
- Support for multiple AI clients (claude, codex, gemini, opencode)

See [mcp-skill-cli documentation](https://github.com/wangxu-dev/mcp-skill-cli) for more details.

## Manual Installation

Alternatively, clone this repository and configure manually:

```bash
git clone https://github.com/wangxu-dev/skills.git
```

Then configure your AI assistant to recognize the skills directory. Refer to your specific assistant's documentation for setup instructions.

## Repository Structure

```
skills/
├── README.md              # This file
├── LICENSE                # Apache License 2.0
└── work-session/          # Work session continuity skill
    ├── SKILL.md           # Skill definition and implementation
    ├── metadata.json      # Skill metadata (version, author, description)
    └── README.md          # Skill-specific documentation
```

## Available Skills

### work-session

Maintains development continuity across disconnected conversations by preserving progress, modified files, TODOs, and git state between work sessions.

```bash
# Save current session state at the end of work
/work-session save

# Restore previous session at the start of new work
/work-session restore
```

**Use case:** Perfect for developers who work in short, focused sessions and need to quickly pick up where they left off.

See [work-session/README.md](./work-session/README.md) for detailed documentation.

## Usage

Once installed, invoke any skill using its slash command:

```bash
/work-session save
```

Each skill may accept additional arguments or options. Refer to the individual skill's documentation for details.

## Development

This is a personal collection of skills I use in my daily workflow. Skills are designed to be:

- **Focused:** Each skill does one thing well
- **Documented:** Clear usage instructions and examples
- **Versioned:** Tracked changes via metadata.json
- **Minimal:** No unnecessary dependencies or complexity
- **Portable:** Works across multiple AI assistants

## Author

**wangxu**
- GitHub: [@wangxu-dev](https://github.com/wangxu-dev)
- Email: [wx@aurise.dev](mailto:wx@aurise.dev)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [mcp-skill-cli](https://github.com/wangxu-dev/mcp-skill-cli) - CLI tool for managing MCP servers and skills across multiple AI assistants
