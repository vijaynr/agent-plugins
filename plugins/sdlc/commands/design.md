---
name: design
description: >
  Add the technical design to the living specification, using DESIGN.md when warranted.
argument-hint: "<feature> [focus]"
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../references/output-language.md), including for delegated work.

# /design

First load `using-agent-skills` for the SDLC routing preflight; load `using-agents` only when custom-agent delegation is appropriate. Then use the `ai-sdlc` skill in `design` mode. Require `SPEC.md`, update its concise `## Design` summary, and create or update `DESIGN.md` for substantial designs. Link `DESIGN.md` from the spec when it exists.
