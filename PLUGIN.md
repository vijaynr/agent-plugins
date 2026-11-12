# Agent Development Toolkit

This repository contains plugins for VS Code and GitHub Copilot. Each plugin is
independently installable. The SDLC plugin is in [`plugins/sdlc`](plugins/sdlc/).
See the [repository README](README.md) for the complete plugin list.

## SDLC plugin

The SDLC plugin provides:

- [`plugins/sdlc/skills/`](plugins/sdlc/skills/) — SDLC skills and tools.
- [`plugins/sdlc/agents/`](plugins/sdlc/agents/) — Optional support agents.
- [`plugins/sdlc/commands/`](plugins/sdlc/commands/) — Slash commands.
- [`plugins/sdlc/plugin.json`](plugins/sdlc/plugin.json) — Plugin manifest.

## Install

From the repository root:

```bash
copilot plugin marketplace add .
copilot plugin install sdlc@vnr-agent-development-toolkit
```

Direct development install:

```bash
copilot plugin install plugins/sdlc
```

Workspace checks (run from the repository root):

```bash
./agents.sh list
./agents.sh validate
```

## SDLC plugin development

- Keep plugin component names kebab-case.
- Skill directory names must match each `SKILL.md` `name` field.
- Keep `commands/` command filenames aligned with frontmatter `name`.
- Do not commit service credentials. Skill `.env` files are local only.
- Follow [`docs/agent-skills-guide.md`](docs/agent-skills-guide.md) when adding or changing skill scripts.
