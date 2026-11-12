# Web Tools Agent Toolkit

## Context loading

Start with [using-web-tools](skills/using-web-tools/SKILL.md). Only the router allows automatic skill selection. Supporting skills set `disable-model-invocation: true`; direct user commands remain available. The router reads the selected skill file explicitly. Do not preload all browser or crawler instructions.

Copilot controls discovery metadata and system context. These rules do not guarantee a fixed token count or force the router to load at startup. Enable only the plugins needed for the task. Test loading in a fresh host session after updating.

Reusable, cross-domain agent skills that do not belong to a product-specific or lifecycle plugin.

## Skills

| Skill | Purpose |
|---|---|
| `web-crawler` | Captures a bounded same-origin set of HTML pages as local Markdown with a local catalog. |
| `agent-browser` | Vercel agent-browser discovery skill for browser automation, with local session and safety guidance. |

## Install

```bash
copilot plugin marketplace add .
copilot plugin install web-tools@vnr-agent-development-toolkit
```

For direct development install:

```bash
copilot plugin install plugins/web-tools
```

## Third-party content

The Vercel `agent-browser` discovery skill is included under Apache-2.0. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
