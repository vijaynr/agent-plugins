---
name: research
description: >
  Perform optional deep research and update the living specification.
argument-hint: "<feature> [focus] [--workspaces <path> [<path> ...]]"
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../references/output-language.md), including for delegated work.

# /research

Use this command only when `/spec`'s focused research is insufficient—for example, for multi-workspace investigation, complex integrations, or material unknowns. First load `using-agent-skills` for the SDLC routing preflight; load `using-agents` only when custom-agent delegation is appropriate. Then use the `ai-sdlc` skill in `research` mode. Require `SPEC.md`, inspect the relevant codebase, and update its `## Research` section. With `--workspaces`, follow the `ai-sdlc` multi-workspace procedure: send one `sdlc_research_request` to `codebase-researcher` for each workspace, and merge each returned section. Keep multi-workspace research focused and concise; do not create a separate research report.
