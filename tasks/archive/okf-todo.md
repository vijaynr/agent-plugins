# OKF Plugin Implementation Tasks

Implementation is blocked until `tasks/plan.md` is reviewed and approved.

## Phase 1: Foundation

- [x] **Task 1 — Scaffold and register the `okf` plugin**
  - Acceptance: Valid plugin manifest, marketplace registration, README/AGENTS guidance, and discoverable skill/command names.
  - Verify: Parse manifests; run discovery checks; `git diff --check`.
  - Depends on: None

- [x] **Task 2 — Implement shared OKF core and validation CLI**
  - Acceptance: Parse/validate frontmatter, reserved files, links, paths, JSON results, and exit codes without writes.
  - Verify: Parser/validator fixtures; CLI `--help`; valid and invalid bundle runs.
  - Depends on: Task 1

### Checkpoint: Foundation

- [x] Review shared OKF model, validation contract, and plugin discovery.
- [x] Confirm validation is read-only and tests pass.

## Phase 2: Authoring core paths

- [x] **Task 3 — Add staging and unified-diff boundary**
  - Acceptance: Proposal staging, new/modified/collision diffs, safe paths, explicit apply, and read-back verification.
  - Verify: Staging tests; target hashes unchanged in proposal mode; approved apply test.
  - Depends on: Task 2

- [x] **Task 4 — Implement `/okf-init` repository bootstrap**
  - Acceptance: Proposes architecture, decisions, gotchas, indexes, log, provenance, and evidence while preserving existing docs.
  - Verify: Empty/partial/non-OKF fixtures; validate staged output; assert no target mutation.
  - Depends on: Tasks 2–3

- [x] **Task 5 — Implement `/okf-ingest` for conversation/text/Markdown**
  - Acceptance: Classifies and renders concepts, detects duplicates, updates indexes/logs, and stages a diff.
  - Verify: Conversation, Markdown, plain-text, duplicate, and empty-input fixtures; validation and immutability checks.
  - Depends on: Tasks 3–4

### Checkpoint: Core authoring

- [x] Init and text ingest produce validated, reviewable staged bundles.
- [x] Confirm taxonomy, templates, duplicate handling, and write gates.

## Phase 3: Input and consumer paths

- [x] **Task 6 — Add safe DOCX/PDF adapters**
  - Acceptance: Shared ingest pipeline, bounded safe extraction, optional dependency errors, and provenance.
  - Verify: Mocked/fixture extraction; malformed/oversized/unsupported inputs; no embedded code execution.
  - Depends on: Task 5

- [x] **Task 7 — Add safe URL ingestion**
  - Acceptance: Explicit HTTP(S) fetches with timeout, size, redirect, content-type, provenance, and structured failures.
  - Verify: Mocked success, redirect, timeout, oversized, unsupported, and prompt-injection cases.
  - Depends on: Task 5

- [x] **Task 8 — Implement `/okf-export`**
  - Acceptance: Deterministic external JSON with concept IDs, metadata, provenance, relationships, and broken-link warnings.
  - Verify: Repeated-run comparison; schema parsing; valid and partially broken fixtures.
  - Depends on: Task 2

### Checkpoint: Input and export coverage

- [x] All required input paths share one renderer.
- [x] Safety tests pass without live network calls.
- [x] Export format and optional adapter decisions are resolved as deterministic JSON for v0.1.

## Phase 4: Integration and release

- [x] **Task 9 — Add commands and canonical consumer guidance**
  - Acceptance: Four user commands, progressive OKF reading guidance, and non-conflicting agent routing.
  - Verify: Frontmatter/command inspection; plugin discovery; simulated review flows.
  - Depends on: Tasks 4–8

- [x] **Task 10 — Complete end-to-end tests and documentation**
  - Acceptance: Full CLI coverage, usage documentation, safety scan, and mapped success criteria.
  - Verify: `python -m pytest tests -q`; `python -m pytest tests/test_skill_cli_smoke.py -q`; `git diff --check`.
  - Depends on: Tasks 6–9

### Checkpoint: Release readiness

- [x] `SPEC.md` success criteria are covered by tests or manual checks.
- [x] Plugin metadata, skills, commands, and marketplace registration agree.
- [ ] Human approves final implementation and generated-document behavior.

## Open Decisions

- [x] `using-okf-knowledge` moved to `plugins/okf`.
- [x] JSON is the v0.1 export format; additional formats remain future scope.
- [x] DOCX/PDF adapters use bounded standard-library extraction for v0.1.
- [x] Non-OKF `docs/` is preserved and conflicts are reported.
- [x] Provenance/status metadata is producer-defined and preserved; a stricter vocabulary remains future scope.
