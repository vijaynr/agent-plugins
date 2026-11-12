---
name: generate-arch-md
disable-model-invocation: true
description: "Generate ARCHITECTURE.md from codebase analysis: layers, components, data flow, Mermaid diagrams, and agent-friendly context."
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Generate ARCHITECTURE.md

Analyse the codebase and write `ARCHITECTURE.md` — layered components, data flow, and agent-friendly context.

## Input

- **Source root** — path to analyse, leave blank for workspace root.
- **Extra context** — known patterns, monorepo scope, or anything to highlight (optional).

Resolve source root relative to workspace root; default to workspace root when blank.

---

## Codebase analysis — do in order

1. Scan: directory tree, `package.json` / `pyproject.toml` / build manifests, `tsconfig`/`jsconfig`, barrel files (`index.*`), and a sample of entry points.
3. Identify the dominant architectural pattern (layered, clean/hexagonal, feature-sliced, MVC, CQRS, etc.).
4. Cluster every significant module/folder into a named **layer** — do not list individual files, name logical components.
5. For each component note: what data it **receives**, how it **transforms** it, and what it **emits** downstream.
6. Trace the primary data-flow path end-to-end (e.g. HTTP request → … → persistence → … → response).

---

## Write `ARCHITECTURE.md`

Write at the source root with sections in this order:

| # | Section | Notes |
|---|---------|-------|
| 1 | Pattern & stack | One-paragraph statement of the architectural pattern and key tech |
| 2 | Layer map | Mermaid `flowchart TD` — layers as subgraphs, data-flow edges labelled with the payload type |
| 3 | Layers | One H3 per layer: purpose sentence, then a table of `Component \| Purpose \| Receives \| Emits` |
| 4 | End-to-end data flow | Mermaid `flowchart LR` — nodes are the named components from section 3, edges labelled with the payload/event crossing them; follow with a short numbered narrative |
| 5 | Cross-cutting concerns | Auth, logging, error handling, caching, config — which layer owns each |
| 6 | Key patterns & conventions | DI wiring, naming rules, state management strategy, API contract style |
| 7 | Entry points | CLI / server bootstrap / app shell — one line each with file path |
| 8 | Extending the codebase | ≤5 bullets: where to add a new feature, service, model, or route following existing conventions |

---

## Constraints

- Keep each `Receives / Emits` cell to ≤10 words — data shape, not implementation detail.
- Two Mermaid diagrams only: section 2 (layer structure, `flowchart TD`) and section 4 (data flow, `flowchart LR`); skip any others.
- Omit test, build, and config-only folders from the layer table unless they enforce a structural rule.
- Do not paraphrase file names — use the logical component name the team would use in conversation.

---

## Output

Confirm path written · one-line architecture summary for quick agent orientation.
