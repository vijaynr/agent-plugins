---
name: to-prd
disable-model-invocation: true
description: Turn the current conversation, product notes, backlog context, or feature idea into a clear PRD/feature draft with problem statement, solution, user stories, implementation/testing decisions, out-of-scope notes, and open questions.
---

# To PRD

Turn the current conversation context and available product/codebase context into
a PRD or backlog-ready feature description. This skill is adapted from Matt
Pocock's `to-prd` engineering skill and repurposed for this repository's product
owner workflows.

Do not interview the user if the existing context is sufficient. If the request
is too vague to create a useful PRD, ask only the minimum clarifying questions
needed, then synthesize.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user supplies
an issue, Octane item, document, URL, or file path, read it before drafting.

If useful and available, lightly explore the repository so the PRD uses the
project's domain vocabulary and respects known architecture/ADRs. Avoid deep
implementation planning unless explicitly requested.

For UI-facing features without approved UX designs, or when interaction behavior
is missing, explicitly read [ui-requirements](../ui-requirements/SKILL.md) unless
it is already in context. Add its applicable flow, UI-state, and design-flexibility
sections to the feature description. Apply its mandatory simplified-language
rules and final rewrite to the generated feature, stories, acceptance criteria,
and any final tracker payload. Keep unresolved policy decisions as open product
questions, not assumptions. Do not invent technical decisions to fill the
Implementation Decisions section; include only supplied or approved decisions.

### 2. Identify testing seams / validation points

Sketch the highest-level seams where the feature can be validated. Prefer
externally observable behavior over implementation details.

Examples:

- UI workflow or user journey
- API contract or CLI behavior
- Integration event or notification
- Permission / policy outcome
- Data import/export result

If seams are unclear, note them as assumptions or open questions.

### 3. Write the PRD

Use this template:

```markdown
# <Feature title>

## Problem Statement

The problem that the user or customer is facing, from their perspective.

## Goals

- <Goal 1>
- <Goal 2>

## Solution

The proposed solution, from the user's perspective.

## User Stories

A numbered list of user stories. Each user story should use this format:

1. As an <actor>, I want <feature/capability>, so that <benefit>.

Make the list broad enough to cover the meaningful behavior, edge cases,
permissions, error states, and operational needs of the feature.

## Feature Description

A backlog-ready description of the feature. Include expected behavior,
important constraints, user-visible flows, and key decisions. Avoid file paths
or brittle implementation specifics.

## Acceptance Criteria

- [ ] Given <context>, when <action>, then <observable result>.
- [ ] <Additional externally verifiable criterion.>

## Implementation Decisions

A list of implementation/product decisions that are known or assumed. This can
include:

- Modules or areas likely affected
- Interfaces or contracts likely involved
- Technical clarifications from the developer
- Architectural decisions
- Schema/API/interaction decisions

Do **not** include specific file paths or code snippets unless the user asked
for a technical PRD or a prototype produced a decision-rich snippet that is
clearer than prose.

## Testing Decisions

A list of validation decisions. Include:

- What makes a good test for this feature
- Which user-visible seams should be tested
- Prior art for similar tests, if known

## Out of Scope

Things that are explicitly not part of this PRD.

## Assumptions

Assumptions made because the source context did not answer everything.

## Open Questions

Questions that must be answered before implementation or publication.

## Further Notes

Any further notes, examples, links, or decisions.
```

### 4. Review before publishing

If the user asked only for a PRD draft, stop after producing it.

If the user asked to publish to ALM Octane, GitLab, GitHub, or another tracker:

1. Present the final PRD content first.
2. Ask for explicit confirmation.
3. Use the smallest available tracker command/API.
4. Verify the created or updated item with a read command.
5. Report the resulting ID/URL.

## Guardrails

- Do not invent hard requirements; mark assumptions clearly.
- Do not publish or update tracker items without explicit confirmation.
- Prefer product-facing language over implementation detail.
- Acceptance criteria must be externally observable and testable.
