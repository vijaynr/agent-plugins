# AGENTS.md

## Context loading

Start with `skills/using-context-engineering/SKILL.md`. Only this router allows automatic skill selection. Read a supporting skill explicitly only after selection. Do not preload all skill, agent, or reference bodies. Keep existing approval gates. See the README for host limits.

This `plugins/context-engineering` directory contains the Context Engineering plugin: local prerequisite tooling and context-preparation support skills.

## Plugin Structure

```text
plugins/context-engineering/
├── plugin.json
├── AGENTS.md
├── README.md
└── skills/
```

## Key Skills

- `setup-rtk` — checks and optionally installs/initializes RTK (Rust Token Killer) with explicit approval gates.
- `setup-ripgrep` — checks and optionally installs ripgrep with explicit approval gates.
- `setup-caveman` — checks and optionally installs/uninstalls Caveman for GitHub Copilot with explicit approval gates.

## Conventions

- Work from this plugin root when running plugin-local scripts: `cd plugins/context-engineering`.
- Skill scripts return JSON where possible; parse outputs directly.
- Prefer explicit user approval before installing or initializing local tools.
- Never commit `.env` files or machine-local secrets.
- After any write operation, verify with the corresponding read command.
- When adding, removing, renaming, or materially changing a skill or agent, update this file and the plugin README.
