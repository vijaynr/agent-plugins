---
name: mermaid-diagrams
disable-model-invocation: true
description: "Mermaid diagram creation and syntax for flowcharts, sequence, class, ERD, C4, state, gantt, git graphs, and architecture diagrams."
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Mermaid Diagrams

Create valid Mermaid diagrams for software and architecture documentation.

## Steps

1. Select the diagram type.
   - Use flowchart for processes, sequence for interactions, class for domain structure, ERD for data, C4/architecture for systems, state for lifecycle.
   - Load `references/full-reference.md` for syntax examples, theming, or export details.
   - Completion criterion: diagram type matches the user's intent and available evidence.

2. Draft valid Mermaid.
   - Use stable IDs and readable labels.
   - Avoid unsupported syntax for the target diagram type.
   - Completion criterion: diagram text is syntactically plausible and source-backed.

3. Validate or explain limits.
   - Run a renderer/linter when available.
   - Completion criterion: diagram renders or the failing line/syntax is identified.
