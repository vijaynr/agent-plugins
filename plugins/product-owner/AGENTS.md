# AGENTS.md

## Context loading

Start with `skills/using-product-owner/SKILL.md`. Only this router allows automatic skill selection. Read a supporting skill explicitly only after selection. Do not preload all skill, agent, or reference bodies. Keep existing approval gates. See the README for host limits.

This directory is the standalone Product Owner plugin.

## Structure

```text
plugins/product-owner/
├── plugin.json
├── agents/
│   └── product-owner.agent.md
└── skills/
    ├── to-prd/
    ├── to-backlogs/
    ├── ui-requirements/
    ├── grilling/
    ├── zoom-out/
    └── zoom-in/
```

## Guidance

- Use `to-prd` to draft a product-ready PRD/feature.
- Use `to-backlogs` to split approved features into vertical slices.
- Use `ui-requirements` to create or review UI features and stories without UX
  designs. Include applicable UI states and testable criteria. Apply its mandatory
  simplified-language rewrite to generated backlog content.
- Use `grilling` for one-question-at-a-time clarification on uncertain product
  decisions.
- Use `zoom-out` and `zoom-in` to move up or down the ladder of abstraction as
  needed during product and requirements conversations.
- For ALM Octane read/write operations, use the `alm-octane` skill from the
  companion `octane` plugin.
