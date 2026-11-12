# Documentation Index

This directory contains repository-wide guidance for maintaining the Agent Development Toolkit plugin workspace. If you want to **use** a marketplace plugin rather than maintain it, start with the [root README](../README.md) and the README in that plugin's directory.

## Development conventions

Use these documents when changing repository structure, plugin assets, scripts, dependencies, or tests.

| Document | Use when |
|---|---|
| [Agent Skills Guide](agent-skills-guide.md) | Adding or changing executable scripts, third-party Python packages, external tools, or dependency metadata under `plugins/<plugin>/skills/<skill>/scripts/`. |
| [Testing Guidelines](testing-guidelines.md) | Running and maintaining existing tests for active plugin and skill scripts. |

## Maintenance rules

- Keep root-level docs focused on workspace-wide conventions or cross-plugin workflows.
- Keep plugin-specific quickstarts in `plugins/<plugin>/README.md`.
- Link from plugin docs to detailed root docs instead of duplicating long process descriptions.
- Update this index when adding, renaming, or removing files in `docs/`.
- Prefer one source of truth for each topic:
  - script conventions and dependency inventory: `agent-skills-guide.md`,
  - test conventions: `testing-guidelines.md`.

## Redundancy review

Current docs are intentionally distinct:

- `agent-skills-guide.md` defines how scripts should be designed and operated, and includes the dependency inventory and maintenance rule for those scripts.
- `testing-guidelines.md` defines pytest layout and extension rules.

`runtime-dependencies.md` was merged into `agent-skills-guide.md` because dependency rules only apply to skill scripts and did not need a separate source of truth. If future docs overlap, merge the durable guidance into the relevant source-of-truth document above and replace duplicate content with a link.
