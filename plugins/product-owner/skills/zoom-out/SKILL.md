---
name: zoom-out
disable-model-invocation: true
description: "Use when asked to zoom out, abstract, summarize, conceptualize, explain architecture, derive concepts from implementation, understand complex code, or turn concrete design/requirements/code details into higher-level intent using the ladder of abstraction."
---

# Zoom Out

Abstract concrete implementation, design, or requirements detail into the
higher-level concepts it serves. Use this to understand an existing complex
codebase or to turn dense design/requirements material into a clearer conceptual
model.

## Inputs

Accept any of these as source context:

- A design or requirements document path, folder, URL, or pasted text.
- A code path, component name, feature name, stack trace, class/function, or module.
- A one-off question about how an implementation works.

If the user points to a design or requirements document, treat that document as
the root. Follow its local references to related requirements, designs, research,
plans, diagrams, source files, and linked artifacts when they are needed to
explain the concept accurately.

## Ladder of abstraction

Move upward one rung at a time:

1. **Concrete facts** — files, functions, APIs, fields, workflows, states,
   validations, data stores, dependencies, tests, and observable behavior.
2. **Mechanisms** — the implementation patterns and collaborations that make the
   facts work together.
3. **Capabilities** — what the mechanism lets a user, operator, service, or
   product area do.
4. **Concepts** — the domain idea, invariant, policy, lifecycle, or business rule
   represented by the capability.
5. **Intent** — why the concept matters: outcome, risk reduction, compliance,
   usability, reliability, performance, or maintainability.

Do not skip rungs. If evidence only supports a lower rung, stop there and mark
higher rungs as assumptions or open questions.

## Steps

1. Resolve the source.
   - Read the referenced design/requirements document or pasted context first.
   - Follow only relevant pointers from that document: sibling spec files,
     diagrams, code paths, issue links, referenced components, and tests.
   - If no source is provided, ask for the document/path/component to zoom out
     from.
   - Completion criterion: the concrete source facts and their provenance are
     known.

2. Extract concrete evidence.
   - Identify the smallest set of concrete facts that explain the behavior.
   - Preserve names that carry domain meaning, but avoid dumping implementation
     detail.
   - Distinguish confirmed facts from inferred intent.
   - Completion criterion: every important claim has a source fact or is marked
     as an inference.

3. Climb the ladder.
   - Group related facts into mechanisms.
   - Name the capability each mechanism provides.
   - Name the broader concept or policy behind the capability.
   - State the product or engineering intent that the concept serves.
   - Completion criterion: the abstraction chain from concrete detail to concept
     is explicit and no rung relies on hidden leaps.

4. Produce the zoom-out artifact.
   - Default to a concise Markdown explanation in chat unless the user requests a
     file.
   - For file output, write near the source document using a clear name such as
     `zoom-out.md` or `<topic>.zoom-out.md`.
   - Completion criterion: the result helps a reader understand the system
     without needing to inspect every low-level detail.

## Output format

```markdown
# Zoom Out: <topic>

## Source
- <document/path/link> — <why it mattered>

## One-line concept
<The highest accurate abstraction in one sentence.>

## Ladder
| Rung | Summary | Evidence |
|---|---|---|
| Concrete facts | <files/functions/flows/requirements> | <source refs> |
| Mechanisms | <how pieces collaborate> | <source refs> |
| Capabilities | <user/system capability> | <source refs> |
| Concepts | <domain concept/policy/invariant> | <source refs or inference> |
| Intent | <why this exists> | <source refs or assumption> |

## Conceptual model
<Short explanation of the concept and how the concrete implementation embodies it.>

## Boundaries and non-goals
- <What this abstraction does not cover.>

## Open questions / assumptions
- <Only if needed.>
```

## Rules

- Keep source traceability. Conceptual clarity must not become invention.
- Prefer domain language over framework language at higher rungs.
- Preserve important constraints, invariants, and failure modes while abstracting.
- If multiple concepts are mixed together, split them and show how they relate.
- Do not rewrite requirements or design decisions unless the user explicitly asks.
