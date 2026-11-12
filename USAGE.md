# agents.sh usage

Use `agents.sh` to list, install, remove, and inspect this repository's agent assets.

## Quick install

```bash
bash agents.sh install all
```

Default targets:

- `skills`, `agents`, `hooks` → `~/.copilot/<type>/`
- `prompts`, `commands` → VS Code user prompts directory

## Common commands

```bash
bash agents.sh list                  # List available assets and where they are installed
bash agents.sh status                # Show installed assets in known targets
bash agents.sh install all           # Install everything to default locations
bash agents.sh install agents        # Install all agents
bash agents.sh install skills        # Install all skills
bash agents.sh install commands      # Install all slash commands as VS Code prompt files
bash agents.sh env                   # Create missing skills/*/.env files from .env.example
bash agents.sh plugin                # Register/install this repo as an agent plugin when supported
```

## Install one asset

```bash
bash agents.sh install skills gitlab
bash agents.sh install skills setup
```

## Install to a specific target

```bash
bash agents.sh install all copilot
bash agents.sh install all agents
bash agents.sh install prompts vscode
bash agents.sh install commands vscode
```

Supported named targets:

- `default` — prompts/commands to VS Code; everything else to `~/.copilot`
- `copilot` — `~/.copilot/<type>/`
- `agents` — `~/.agents/<type>/`
- `vscode` — VS Code prompts directory; prompts and commands only

## Install into a project repository

Pass a project path to install into that repository's `.github` folders:

```bash
bash agents.sh install all ./my-project
bash agents.sh install agents ./my-project
bash agents.sh install commands ./my-project
```

Project-path layout:

- prompts and commands → `.github/prompts/`
- agents → `.github/agents/`
- skills → `.github/skills/`
- hooks → `.github/hooks/` as `*.json` hook configuration files

## Remove assets

```bash
bash agents.sh remove skills copilot gitlab
bash agents.sh remove skills copilot setup
bash agents.sh remove commands ./my-project all
```

Remove all installed assets of a type from a target:

```bash
bash agents.sh remove agents copilot all
bash agents.sh remove skills copilot all
```

## Deprecated asset cleanup

During install, `agents.sh` first removes known deprecated/renamed assets from the destination. The cleanup list is maintained in the `REMOVED_ASSETS` array inside `agents.sh`; entries may be exact names or globs such as `skills:feat-*` and `commands:feat-*`.
