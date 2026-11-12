---
name: resume
description: >
  Smart AI SDLC resume. Inspect status, artifacts, drift, and git state; run the next safe action or ask when ambiguous.
argument-hint: "<feature> [context]"
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../references/output-language.md), including for delegated work.

# /resume

Use the `ai-sdlc` skill in `resume` mode. Parse the arguments, resolve/reuse `.features/<feature>` when needed, follow the corresponding action section in `skills/ai-sdlc/SKILL.md`, update `status.json`, and preserve Conventional Commit / evidence rules.
