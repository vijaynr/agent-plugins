---
name: documentation-and-adrs
disable-model-invocation: true
description: Records decisions and documentation in a stack-neutral way. Use when making architectural decisions, changing public interfaces, shipping features, or preserving context future engineers/agents will need.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Documentation and ADRs

## Overview

Good documentation preserves intent. Code shows what exists; documentation explains why it exists, how to use it safely, and what trade-offs were accepted.

This skill is stack-neutral and applies to any project, language, or runtime.

## When to Use

- Making or changing an architectural decision
- Introducing or changing a public API/interface/contract
- Adding operational behavior users or maintainers must understand
- Shipping a feature with setup, migration, rollout, or support implications
- Capturing a trade-off that future maintainers may revisit
- Updating behavior that existing docs describe

## Documentation Types

| Type | Use for |
|---|---|
| README / getting started | How to install, configure, run, and verify common flows |
| API/interface docs | Inputs, outputs, errors, compatibility, examples |
| Architecture overview | System boundaries, components, data/control flow |
| ADR | A decision, context, alternatives, consequences |
| Runbook | Operational diagnosis and response steps |
| Inline comments | Non-obvious local intent, invariants, constraints |
| Changelog/release notes | User-visible changes, migrations, deprecations |

## ADR Template

```markdown
# ADR-NNN: [Decision Title]

## Status
Proposed | Accepted | Superseded | Deprecated

## Context
What problem are we solving? What constraints matter?

## Decision
What did we decide?

## Alternatives Considered
- Option A: pros/cons
- Option B: pros/cons

## Consequences
What becomes easier? What becomes harder? What risks remain?

## Verification
How will we know this decision is working?

## References
Links to specs, issues, docs, source, incidents, or discussions.
```

## Documentation Process

1. **Identify the audience.** User, developer, operator, reviewer, future maintainer, or agent.
2. **Document the why first.** Avoid duplicating obvious code behavior.
3. **Record commands exactly.** Use copy-pasteable commands from the actual project.
4. **List prerequisites and assumptions.** Versions, permissions, environment, external services.
5. **Explain failure modes.** Include common errors and recovery paths where useful.
6. **Link to source of truth.** Specs, ADRs, code, external docs, issues, or runbooks.
7. **Update docs with code.** Do not let docs describe behavior that no longer exists.

## Inline Comment Rules

Use comments for:

- Why a non-obvious choice was made
- Invariants the code depends on
- Security/compatibility/performance constraints
- External protocol or data quirks
- Links to decisions or upstream behavior

Avoid comments that merely restate the code.

```text
BAD:
  increment counter

GOOD:
  Retry once because the upstream service may accept the request but drop the response.
```

## Public Interface Documentation

For any public API, CLI, file format, plugin contract, event, or module boundary, document:

- Purpose and audience
- Inputs/arguments/options
- Outputs/return values/artifacts
- Error behavior
- Compatibility/versioning expectations
- Security considerations
- Examples using project-realistic values
- Migration notes if behavior changed

## Runbook Minimum

For operational behavior, include:

```markdown
# Runbook: [Symptom]

## What this means
[Plain-language explanation]

## First checks
[Queries, commands, dashboards, logs]

## Mitigation
[Safe actions]

## Escalation
[When and who]

## Rollback / Disable
[How to reduce impact]
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The code is self-documenting" | Code rarely explains context, alternatives, or trade-offs. |
| "We'll document it later" | Later documentation loses decision context. |
| "This is obvious" | It is obvious only to the person who just built it. |
| "Docs get stale" | Update docs in the same change that changes behavior. |
| "An ADR is too formal" | A short ADR is cheaper than rediscovering the decision later. |

## Verification

- [ ] Documentation matches current behavior.
- [ ] Commands/examples are project-realistic and copy-pasteable where applicable.
- [ ] Decisions capture context, alternatives, and consequences.
- [ ] Public interfaces document inputs, outputs, and errors.
- [ ] Operational docs include diagnosis and rollback/mitigation where relevant.
- [ ] Links point to stable source-of-truth artifacts.
