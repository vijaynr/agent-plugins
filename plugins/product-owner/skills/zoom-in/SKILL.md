---
name: zoom-in
disable-model-invocation: true
description: "Use when asked to zoom in, elaborate, decompose, operationalize, make concrete, expand an abstract idea, turn a one-liner into requirements/design detail, or derive implementation-facing detail from a concept using the ladder of abstraction."
---

# Zoom In

Turn an abstract idea, one-liner, concept, requirement, or design statement into
concrete product/design detail. Use this to deepen a design or requirements
document, derive behavior from intent, or make an idea implementation-ready
without jumping straight to code.

## Inputs

Accept any of these as source context:

- A design or requirements document path, folder, URL, or pasted text.
- A one-line idea, concept, product outcome, capability, policy, or architectural
  principle.
- A specific section in an existing document that needs more detail.

If the user points to a design or requirements document, treat that document as
the root. Follow its local references to related requirements, designs, research,
plans, diagrams, source files, and linked artifacts when they are needed to make
concrete decisions.

## Ladder of abstraction

Move downward one rung at a time:

1. **Intent** — why the idea matters: outcome, risk reduction, compliance,
   usability, reliability, performance, or maintainability.
2. **Concepts** — the domain idea, invariant, policy, lifecycle, or business rule.
3. **Capabilities** — what a user, operator, service, or product area must be able
   to do.
4. **Mechanisms** — product/design mechanisms, interactions, data flows,
   validation rules, states, APIs, permissions, and operational behavior.
5. **Concrete facts** — acceptance criteria, examples, edge cases, diagrams,
   affected components, tests, observability, migration/rollout notes, and
   implementation constraints.

Do not skip rungs. If a lower rung depends on an unresolved product or design
decision, ask before continuing.

## Required clarification behavior

Use the `grilling` skill for clarification before committing to concrete detail.
Ask exactly one question at a time, include a recommended answer and rationale,
and wait for the user's response. Do not ask questions that can be answered by
reading the referenced document or exploring the codebase.

Prioritize questions about:

- Target user/persona or system actor.
- Desired outcome and success signal.
- Scope boundary and explicit non-goals.
- Critical constraints, dependencies, permissions, security, privacy, or data
  retention.
- Risky assumptions that would change the concrete design or acceptance criteria.

Stop grilling when remaining unknowns can be safely marked as assumptions or open
questions.

## Steps

1. Resolve the source and target.
   - Read the referenced design/requirements document or pasted context first.
   - Identify the exact idea, section, requirement, or abstraction to zoom in on.
   - Determine whether the user wants chat output or an update/new file.
   - Completion criterion: source context, target abstraction, and output mode are
     known.

2. Ground the abstraction.
   - Extract stated intent and concepts from the source.
   - Follow relevant pointers from the document before asking questions.
   - Mark missing intent or concepts as candidate grilling topics.
   - Completion criterion: existing facts are separated from assumptions.

3. Grill only decision-changing gaps.
   - Use `grilling` one question at a time for unresolved choices that affect the
     downward ladder.
   - Record the user's answers as decisions.
   - Keep recommended answers pragmatic and explain the tradeoff briefly.
   - Completion criterion: enough decisions exist to produce concrete detail, or
     remaining gaps are explicitly open questions.

4. Descend the ladder.
   - Convert intent into concepts and invariants.
   - Convert concepts into capabilities.
   - Convert capabilities into mechanisms and interactions.
   - Convert mechanisms into externally observable acceptance criteria, examples,
     edge cases, affected areas, and validation/test ideas.
   - Completion criterion: every concrete detail traces back to an intent,
     concept, source fact, or user-confirmed decision.

5. Produce or update the artifact.
   - Default to Markdown in chat unless the user requested a file edit.
   - For new files, write near the source document using a clear name such as
     `zoom-in.md` or `<topic>.zoom-in.md`.
   - For edits to an existing document, preserve its structure and add only the
     requested detail.
   - Completion criterion: the result is concrete enough for design review,
     backlog refinement, or implementation planning.

## Output format

```markdown
# Zoom In: <topic>

## Source
- <document/path/link> — <why it mattered>

## Starting abstraction
<The idea, one-liner, requirement, concept, or design statement being expanded.>

## Decisions from clarification
- <Decision> — <source: user/source document/assumption>

## Ladder
| Rung | Detail | Traceability |
|---|---|---|
| Intent | <why this matters> | <source/user decision> |
| Concepts | <domain idea/policy/invariant> | <source/user decision> |
| Capabilities | <what actors can do> | <source/user decision> |
| Mechanisms | <flows/rules/interactions/components> | <source/user decision> |
| Concrete facts | <criteria/examples/tests/edge cases> | <source/user decision> |

## Proposed concrete detail
<Expanded requirements/design text suitable for the target document.>

## Acceptance criteria / verification
- [ ] Given <context>, when <action>, then <observable result>.

## Edge cases and constraints
- <Edge case or constraint.>

## Open questions / assumptions
- <Only if needed.>
```

## Rules

- Do not invent hard requirements. Use assumptions and open questions for unknowns.
- Keep implementation detail proportional to the source document type: product
  requirements should stay externally observable; technical designs may include
  interfaces, data flows, and component responsibilities.
- Prefer concrete examples and acceptance criteria over vague elaboration.
- Preserve traceability from concrete details back to intent, source facts, or
  user-confirmed decisions.
- Do not edit product code.
