# Context Engineering Agent Toolkit

## Context loading

Start with [using-context-engineering](skills/using-context-engineering/SKILL.md). Only the router allows automatic skill selection. Supporting skills set `disable-model-invocation: true`; direct user commands remain available. The router reads the selected skill file explicitly. Do not preload the whole plugin.

Copilot controls discovery metadata and system context. These rules do not guarantee a fixed token count or force the router to load at startup. Enable only the plugins needed for the task. Test loading in a fresh host session after updating.

This directory is the `context-engineering` plugin. It owns local context-preparation tooling skills that are useful before or alongside SDLC workflows, but are not part of project artifact generation.

## Plugin structure

```text
.
├── plugin.json
├── AGENTS.md
├── README.md
└── skills/
```

## Key skills

| Skill | Purpose |
|---|---|
| `setup-rtk` | Check and optionally install/initialize RTK with approval gates |
| `setup-ripgrep` | Check and optionally install ripgrep with approval gates |
| `setup-caveman` | Check and optionally install/uninstall Caveman for GitHub Copilot with approval gates |

## Quickstart examples

Start with the tool you are missing or want to verify. The skills inspect the machine first, explain what they found, and ask before they install or initialize anything.

1. Check local search tooling before codebase research:

   ```text
   Use the setup-ripgrep skill to verify ripgrep is available.
   ```

2. Check RTK availability before preparing large repository context:

   ```text
   Use the setup-rtk skill to verify RTK is installed and initialized.
   ```

3. Configure Caveman for GitHub Copilot in the current repository:

   ```text
   Use the setup-caveman skill to dry-run and then install Caveman for GitHub Copilot.
   ```

4. Approve installation only when the skill reports a missing prerequisite and shows the exact command it will run.

Expected output is structured setup status, including installed/found versions, missing tools, and approval-gated next actions.

## Relationship to SDLC

Use Context Engineering before or alongside SDLC work when the local environment needs context-search or project-tooling prerequisites. This plugin owns local setup checks and approval-gated installation/initialization for context tooling.

The [SDLC plugin](../sdlc/README.md) owns feature artifacts and lifecycle commands. A typical handoff is: use Context Engineering to prepare local tooling, then run `/spec`, `/research`, or `/resume` in the SDLC workflow with better repository context available.

## Install

From the repository root, register the local marketplace and install the plugin:

```bash
copilot plugin marketplace add .
copilot plugin install context-engineering@vnr-agent-development-toolkit
```

For direct development install:

```bash
copilot plugin install plugins/context-engineering
```

## Repository conventions

- Skill scripts return structured JSON where possible.
- Tool installation and initialization require explicit user approval unless non-interactive mode was requested.
- Secrets must stay out of source control.
