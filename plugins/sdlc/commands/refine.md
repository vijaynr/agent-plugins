---
name: refine
description: >
  Refine AI SDLC planning artifacts, using grilling unless --apply is safe and unambiguous.
argument-hint: "<feature> [requirements|research|design|plan] [--apply] [request]"
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../references/output-language.md), including for delegated work.

# /refine

Use the `ai-sdlc` skill in `refine` mode. Parse the arguments, resolve/reuse `.features/<feature>` when needed, follow the corresponding action section in `skills/ai-sdlc/SKILL.md`, update `status.json`, and preserve Conventional Commit / evidence rules.
