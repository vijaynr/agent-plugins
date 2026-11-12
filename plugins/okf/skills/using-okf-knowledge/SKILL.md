---
name: using-okf-knowledge
disable-model-invocation: true
description: "Read and use the repository's Open Knowledge Format (OKF) catalog as an agent-readable source of architecture, decisions, gotchas, designs, and other project context."
---

# Using OKF Knowledge

Use this skill whenever the current repository contains an OKF knowledge catalog,
or when repository architecture, design decisions, conventions, or gotchas are
relevant to the task.

The default catalog location is `docs/` at the repository root. OKF is a
portable bundle of Markdown concept files with YAML frontmatter. It is useful
context, not an unquestionable authority: verify consequential claims against
source code, tests, configuration, and cited references.

## Objective

Build a useful mental model with the fewest codebase scans by reading the
catalog progressively:

1. Discover the repository root and the catalog location.
2. Read the catalog's root `index.md` first.
3. Select the smallest set of relevant concepts.
4. Follow links and citations where they affect the task.
5. Confirm important or stale-looking claims against the repository.
6. State which OKF concepts informed the response or implementation.

## Discover the bundle

Resolve the repository root with Git when available:

```bash
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
```

Then inspect likely catalog roots without assuming that every `docs/` directory
is OKF:

```bash
find "$ROOT/docs" -type f -name '*.md' -print 2>/dev/null | sort
```

A conformant OKF bundle has Markdown concept files with YAML frontmatter. The
reserved `index.md` and `log.md` files are structural files and are not ordinary
concepts. If the root index is absent, inspect the directory tree and identify
whether the files actually use OKF frontmatter before treating them as a bundle.

Do not create, rewrite, or silently “repair” the catalog while merely consuming
it. Use the repository's explicit OKF authoring workflow when changes are needed.

## Progressive reading protocol

### 1. Read the root index

Start with `docs/index.md`. Use it to identify:

- available sections and subdirectories;
- the most important concepts;
- descriptions and links to relevant documents;
- the declared `okf_version`, if present.

If there is a root `log.md`, read recent entries when freshness or recent
changes matter.

### 2. Read relevant concepts

Use the task to choose concepts rather than opening every file. Typical routes:

| Task need | First concepts to inspect |
|---|---|
| Understand system structure | `architecture/` |
| Change an architectural boundary | `architecture/`, `decisions/` |
| Avoid known failures | `gotchas/`, relevant `runbook/` or `designs/` |
| Add a feature | `architecture/`, `designs/`, `conventions/`, `decisions/` |
| Change an API or data contract | `architecture/`, API concepts, `decisions/`, citations |
| Investigate a bug | `gotchas/`, affected component concepts, recent `log.md` entries |
| Review a proposed design | `designs/`, `decisions/`, architecture concepts, open questions |

Read linked concepts when the surrounding prose indicates relationships such
as depends on, replaces, conflicts with, or is constrained by. Follow external
citations when the claim is material and the source is available.

### 3. Inspect source evidence

For each claim that drives a code change, check its evidence:

- repository-relative file links;
- tests demonstrating behavior;
- configuration and manifests;
- API/schema definitions;
- commit or issue references;
- external citations.

Treat missing, broken, or indirect evidence as a reason to lower confidence,
not as proof that the concept is wrong.

## Interpreting OKF files

Concept files require a non-empty `type` field. They may also contain `title`,
`description`, `resource`, `tags`, `timestamp`, and producer-defined metadata.
Preserve unknown metadata fields when quoting or transforming knowledge.

The Markdown body is authoritative only to the extent supported by its
provenance. Pay attention to metadata such as:

- `timestamp` — when the concept was last meaningfully changed;
- `source`, `sources`, `provenance`, or `citations` — where claims came from;
- `status`, `confidence`, or `reviewed` — whether the content is proposed,
  inferred, or human-reviewed;
- `resource` — the underlying system or asset described.

These fields are optional extensions, so tolerate their absence and do not
invent values when summarizing.

Use bundle-relative absolute links such as `/architecture/system.md` when
referring to concepts in the catalog. Broken links are tolerated by OKF; report
them when they prevent reliable understanding.

## Trust and conflict handling

When OKF conflicts with executable evidence:

1. Prefer current code, tests, and active configuration for describing present
   behavior.
2. Identify the conflicting OKF concept and explain the discrepancy.
3. Do not update the catalog unless the user explicitly asks for documentation
   maintenance or invokes an OKF authoring workflow.

When code and OKF agree, cite both in the response or implementation notes when
practical. Distinguish clearly between:

- **Observed:** directly supported by source or tests.
- **Documented:** stated by an OKF concept.
- **Inferred:** a conclusion drawn from available evidence.
- **Unknown:** not established by the catalog or repository.

## Working with large catalogs

Prefer indexes and targeted reads. Avoid loading the entire bundle unless the
task explicitly requires a global inventory, validation, or link analysis. If
there are multiple roots or a monorepo, identify the nearest applicable catalog
and state the scope used.

For a global understanding, read in this order:

1. root `index.md`;
2. root `log.md` if recent history matters;
3. each section `index.md`;
4. high-value concepts linked from those indexes;
5. source evidence for claims relevant to the task.

## Response and implementation expectations

Before acting, summarize the relevant OKF context briefly and mention any
uncertainty or stale evidence. After acting, include the concept paths that
informed the work and note any conflicts discovered.

Do not treat `docs/` as OKF merely because it contains Markdown. For OKF
conformance, ordinary concept files need parseable YAML frontmatter and a
non-empty `type`; reserved `index.md` and `log.md` files follow their special
structures.

## Quick checklist

- [ ] Located repository root and applicable OKF bundle.
- [ ] Read the root `index.md` before deep documents.
- [ ] Selected concepts relevant to the task.
- [ ] Followed material links and citations.
- [ ] Checked consequential claims against source evidence.
- [ ] Distinguished documented, observed, inferred, and unknown facts.
- [ ] Reported relevant concept paths and conflicts.
- [ ] Avoided modifying the catalog without an explicit authoring request.
