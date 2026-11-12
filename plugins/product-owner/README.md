# Product Owner Agent Toolkit

## Context loading

Start with [using-product-owner](skills/using-product-owner/SKILL.md). Only the router allows automatic skill selection. Supporting skills set `disable-model-invocation: true`; direct user commands remain available. The router reads the selected skill file explicitly. Agents load their own instructions when invoked. Do not preload the whole plugin.

Copilot controls discovery metadata and system context. These rules do not guarantee a fixed token count or force the router to load at startup. Enable only the plugins needed for the task. Test loading in a fresh host session after updating.

This plugin provides product-owner workflows for shaping ideas into clear PRDs
and backlog-ready vertical slices.

## Contents

- `agents/product-owner.agent.md` — Product owner agent for PRD/story drafting,
  review, and optional publishing flow.
- `skills/to-prd/` — PRD/feature draft generation.
- `skills/to-backlogs/` — Vertical-slice backlog/story breakdown.
- `skills/ui-requirements/` — Engineering-ready UI features, flows, stories, and
  acceptance criteria when UX designs are not available. Includes review and
  decomposition modes, applicable UI states, and mandatory simplified language.
- `skills/grilling/` (`grilling`) — One-question-at-a-time stress testing for unclear
  requirements.
- `skills/zoom-out/` and `skills/zoom-in/` — abstraction ladder support for
  moving between high-level concepts and concrete implementation details.

## Quickstart examples

1. Turn a rough idea into a PRD:

   ```text
   Ask the product-owner agent: turn this idea into a PRD for admins who need expiring public links.
   ```

2. Stress-test unclear requirements one question at a time:

   ```text
   Ask the product-owner agent to grill this feature idea before drafting stories.
   ```

3. Split an approved PRD into vertical backlog slices:

   ```text
   Ask the product-owner agent: split this PRD into backlog-ready vertical user stories.
   ```

4. Create a backlog without UX designs:

   ```text
   Ask the product-owner agent: create stories for this feature without UX designs.
   Define the user flow, UI states, errors, permissions, and acceptance criteria.
   ```

5. Review a UI story before engineering starts:

   ```text
   Ask the product-owner agent: review this UI story for missing behavior and unclear requirements.
   ```

The UI requirements workflow separates required behavior from design suggestions.
It gives engineering design flexibility. It reuses known product patterns and
marks assumptions and open product questions. It does not invent permission or
other policy decisions. Stories with blocking product questions stay draft or
blocked for the affected behavior.

Generated UI features, stories, acceptance criteria, and final tracker content
must use short active sentences, one main action or condition per sentence,
consistent product terms, and testable behavior. The final rewrite removes vague
words. This follows simplified technical English principles; it does not claim
validated ASD-STE100 compliance. Backlog breakdown approval and explicit tracker
write confirmation remain required.

Expected output is a PRD, clarified assumptions/open questions, or backlog-ready slices. Start with the roughest version of the idea you have; the agent will help expose missing decisions instead of expecting a finished brief. Publishing to Octane requires an explicit user request and confirmation.

## Relationship to SDLC

Use Product Owner when an idea needs to become a clear PRD, a set of backlog-ready vertical slices, or better-scoped requirements before engineering starts. This plugin owns product shaping, PRD drafting, backlog breakdown, abstraction-ladder guidance, and one-question-at-a-time requirement stress testing.

The [SDLC plugin](../sdlc/README.md) starts once the team is ready to produce engineering artifacts such as requirements, research, design, implementation plans, implementation logs, and verification reports. A typical handoff is: use Product Owner to shape the product intent, then pass the PRD or backlog slices into `/spec` in the SDLC workflow.

## Related plugins

- [Octane](../octane/README.md) owns ALM Octane operations used for optional backlog publishing.

## Install

From the repository root:

```bash
copilot plugin marketplace add .
copilot plugin install product-owner@vnr-agent-development-toolkit
```

Direct development install:

```bash
copilot plugin install plugins/product-owner
```
