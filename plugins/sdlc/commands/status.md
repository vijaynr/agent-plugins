---
name: status
description: >
  Read-only AI SDLC status, artifact freshness, drift, and git state.
argument-hint: "<feature>"
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../references/output-language.md), including for delegated work.

# /status

Use the `ai-sdlc` skill in `status` mode. Parse the arguments, resolve/reuse `.features/<feature>` when needed, follow the corresponding action section in `skills/ai-sdlc/SKILL.md`, update `status.json`, and preserve Conventional Commit / evidence rules.
