# Implementation Plan: Generic ALM Octane CLI Foundation

## Status and scope

T1–T10 implemented and offline-validated. The user explicitly approved the spec,
G0 policies, autonomous execution, and committing the ignored plugin spec.
Routine verification gates completed without human pauses. Final G4 human review
remains before merge or separately authorized live validation. No live workspace
access or API writes were authorized or attempted.

Paths in this plan are relative to `plugins/octane` unless explicitly labeled
repository-root. Keep existing repository-root `tasks/plan.md`, `tasks/todo.md`,
and `SPEC.md` untouched. Detailed task acceptance and verification are in
`todo.md`.

Deliver seven additive generic REST CLI commands while preserving the existing
32 convenience commands, authentication, URL delegation, deletion, attachments,
and workflow-specific transformations. No MCP dependency, bulk writes, generic
delete, new runtime dependencies, or full wrapper migration.

## Read-only findings

Inspected the plugin spec/guidance, client request/session helpers, metadata
resolution, entity reads, update/concurrency behavior, parser/dispatch, profile
and URL test fixtures, repository smoke tests, and testing guidelines.

| Existing component | Reuse or constraint |
|---|---|
| `resolve_runtime_config`, `configure_runtime` | Reuse unchanged; profiles and credentials remain coherent. |
| `_api_root`, `entity_url`, `request_json` | Reuse for authenticated scoped requests; validate new-command inputs before constructing URLs. |
| `get_entity` | Prints today and is called by existing wrappers. Add a data-returning helper and keep the existing printing adapter/signature. |
| `normalize_entity_collection` | Guesses unknown plurals; do not treat it as authoritative discovery or modify its legacy behavior globally. |
| `get_entity_fields_metadata` | Tries several names/routes and adds limits. Preserve its existing callers unless a separately tested migration is justified. |
| `update_feature`, `update_defect` | Show stamp/read-back patterns, but new generic operations require stricter explicit verification outcomes. |
| `main` | Parses help before configuration. Maintain this for all new subcommands; keep old dispatch/output stable. |
| Plugin tests | Already provide fake keyrings, isolated configuration, relocated scripts, and fake sessions; reuse rather than touching the real credential store. |
| Repository smoke tests | Check help, Python 3.10 grammar, and PEP 723 declarations; extend coverage without making optional tools mandatory. |

Runtime metadata and existing skill requirements both specify Python 3.10+;
no version change is needed. `docs/testing-guidelines.md` provides a reproducible
`uvx` test command with requests, python-dotenv, and keyring.

### Authoritative source spot-check

Public documentation was read; no configured Octane instance was contacted.
These sources guide research, not a claim of compatibility with an unknown
server version:

- [Entity metadata, 26.1](https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/MetadataEntities.htm):
  workspace `/metadata/entities`; `rest` features expose collection URLs/methods.
- [Field metadata, 26.3](https://admhelp.microfocus.com/octane/en/26.3/Online/Content/API/MetadataFields.htm):
  `/metadata/fields`; only `query` filtering is supported, not ordinary
  `limit`, `offset`, `total_count`, or `order_by` parameters.
- [Optimistic locking, 26.1](https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/Lock.htm):
  send `client_lock_stamp` on PUT; documented stale-stamp errors can be HTTP 500
  with `platform.version_conflict`, not just HTTP 409.

T1 found official MCP documentation describing filter metadata as query-language
documentation, not necessarily live operator discovery. See `api-contracts.md`
for the proposed source-cited grammar/live-field composition and qualified search
contract. No operator-discovery endpoint was established or invented; G0 approval
of the composition and version limitations is required.

## Architecture decisions

1. **Additive vertical slices.** Each command lands with CLI parsing, a reusable
   operation, offline tests, and reference documentation; no horizontal transport
   rewrite before a usable command exists.
2. **Small data-returning functions.** Reuse request/session/configuration helpers.
   New CLI handlers serialize one envelope and return nonzero status on failure.
   Keep existing printing functions as compatibility adapters where necessary.
3. **Metadata-informed target resolution.** Use verified entity names and `rest`
   feature collection mappings, preserving explicit known aliases. Validate every
   path segment, including workspace/shared-space/entity IDs and metadata-supplied
   collection names. Never follow a full URL received in metadata. Keep any cache
   command-local and scoped to the selected endpoint/workspace.
4. **Explicit list semantics.** One page per invocation, defaults limit 50/offset
   0, native query distinct from text search, no silent full-workspace traversal.
   Preserve totals and the raw server data inside the established envelope.
5. **Single-record JSON writes.** One nonempty field object from `--data-file`;
   preserve nested relationships and caller values. Build the documented payload
   appropriate to collection POST versus single-record PUT; do not assume they
   use identical envelopes.
6. **Evidence-bearing verification.** Create and update ship with read-back in
   their own slices. Compare supplied fields using documented canonicalization;
   compare relationship identities rather than requiring expanded response
   objects to equal input literally. Unverifiable/mismatched writes are not
   reported as verified. Keep mutation evidence separate from read/match status.
7. **No automatic mutation replay.** A timeout, lost response, missing returned
   ID, failed read-back, or stale stamp must never trigger a second mutation.
8. **Minimal wrapper migration.** Prove `get_entity` adaptation in Task 2;
   postpone mass migration and do not alter specialized write behavior.
9. **Offline first.** Mock service and credential boundaries. Installing test
   dependencies may require package-index access, but tests must not contact
   Octane or real keyrings. No CI/runtime dependency changes.

## Dependency graph

```text
Existing profile/session/request helpers (unchanged)
                    |
          T1 Contract research + baseline
                    |
              G0: research approval
                    |
          T2 get-entity vertical slice
                    |
          T3 get-entity-types + REST mapping
                    |
              G1: read/target safety
                    |
          T4 get-entity-field-metadata
                    |
          T5 get-filter-metadata
                    |
          T6 get-entities query/search/page/sort
                    |
              G2: discovery/read review
                    |
          T7 create-entity + read-back
                    |
          T8 update-entity + lock/read-back
                    |
              G3: mutation safety review
                    |
          T9 compatibility + CLI smoke closure
                    |
          T10 user guidance + acceptance audit
                    |
              G4: completion review
```

T6 logically needs T2/T3 and the query/search contract from T1/T5. T7 needs T2,
T3, T4; T8 needs those plus verification/input helpers established by T7. The
execution order above intentionally serializes shared edits to `octane_client.py`.

## Phases and checkpoints

### Phase 0 — Resolve risky contracts

- [x] T1: Source-backed capability matrix, safe input/output contracts, test baseline.
  Evidence: `api-contracts.md`. Documentation-only TDD exemption; no new behavior.

**G0 — Blocking research review:** Verify filter discovery feasibility, text
search scope, sorting, metadata restrictions, REST collection mappings, POST/PUT
payloads, and generic concurrency/verification rules. Review baseline failures
without suppressing them. If sources cannot establish a required capability,
stop and request a spec amendment before implementing it. Explicitly approve the
spec and plan before production changes.

### Phase 1 — Read one record and discover available entities

- [x] T2: `get-entity`, including a behavior-preserving legacy read adapter.
  RED/GREEN recorded in todo; plugin 124 passed/1 skipped, workspace 328 passed/2 skipped.
- [x] T3: `get-entity-types`, including metadata-informed collection mapping.
  G1 passed: plugin 135 passed/1 skipped; workspace 328 passed/2 skipped;
  scope/method validation and irregular mapping tests pass.

**G1 — After T2–T3:** Focused tests and plugin regressions pass. Root/new command
help works without credentials/configuration/network. Validate path safety,
workspace/profile propagation, mapping of irregular collection names, and old
read output. Review before adding remaining discovery/list commands.

### Phase 2 — Discover fields/filters and retrieve a page

- [x] T4: `get-entity-field-metadata` with honest metadata/provenance.
  Plugin 141 passed/1 skipped; workspace 328 passed/2 skipped; compile checks pass.
  Unchanged profile test had one non-reproducing Windows replace failure; see todo.
- [x] T5: `get-filter-metadata` with source-backed syntax/operators.
  Plugin 144 passed/1 skipped; workspace 328 passed/2 skipped; compilation passed.
- [x] T6: `get-entities` with filtering, search, fields, sorting, and pagination.
  G2 passed: plugin 156 passed/1 skipped, workspace 328 passed/2 skipped;
  five discovery/read commands verified with fake HTTP, compile checks passed.

**G2 — After T4–T6:** All five generic read/discovery commands have CLI-to-fake-HTTP
coverage. Metadata restrictions, unsupported capabilities, encoding, totals,
empty results, and collection-specific search limits are documented/tested.
Approve the read-only foundation before adding generic writes.

### Phase 3 — Single-record mutations with verification

- [x] T7: `create-entity` from JSON with safe read-back outcomes.
  Plugin 185 passed/1 skipped, workspace 328 passed/2 skipped; compile passed.
  Review-driven regressions cover completeness, reference shapes and write evidence;
  three bounded review cycles reconciled against the approved contract (see todo).
- [x] T8: `update-entity` with partial fields and optimistic locking.
  G3 passed: plugin 205 passed/1 skipped; workspace 328 passed/2 skipped;
  compile/3.10 grammar passed; fresh-context mutation review resolved findings.

**G3 — After T7–T8:** Review invalid-input/no-write cases, nested relationships,
caller-supplied stamps, absent/unsupported stamps, failed prerequisite reads,
conflicts including HTTP 500, uncertain transport outcomes, normalization, and
mutation/read-back evidence. Confirm no automatic mutation replay, approval
flag, or credential/host behavior change. All plugin tests pass.

### Phase 4 — Compatibility and handoff

- [x] T9: Close compatibility, secret-safety, and workspace smoke coverage.
  Plugin 274 passed/1 skipped; workspace 328 passed/2 skipped; compile checks pass.
  Closure tests drove minimal generic-only boundary fixes; security review then
  found no remaining concrete issues in its scope.
- [x] T10: Publish agent/developer workflows and audit spec acceptance.
  Documentation-only TDD exemption; all 7 help contracts and 4 JSON examples
  validated locally. Final suites: plugin 274 passed/1 skipped, workspace
  328 passed/2 skipped. Compile/3.10 grammar checks passed.

**G4 — After T9–T10:** Run plugin and required workspace suites. Review diff,
commands/examples, all spec success criteria, test results, and remaining
limitations. No merge, deployment, or live access without human approval.

## Verification commands

Run plugin-local commands from `plugins/octane`:

```bash
# Reproducible development runner; packages may be resolved from the package index
uvx --from pytest --with requests --with python-dotenv --with keyring pytest skills/alm-octane/tests -q

# Equivalent once the development environment has these dependencies
python -m pytest skills/alm-octane/tests -q
python -m pytest ../../tests/test_skill_cli_smoke.py -q
python -m pytest ../../tests/test_credential_config_contract.py -q

# Help only; never run API examples as validation without permission
uv run skills/alm-octane/scripts/octane_client.py --help
```

Run the required workspace suite from repository root:

```bash
python -m pytest tests plugins/okf/tests -q
```

Each task lists focused tests in `todo.md`. Capture baseline failures, command,
Python version, and exit status before implementation. No tests were run in the
read-only planning phase; T1 subsequently ran the baselines documented below. There is no build step or newly required lint tool.
Use existing lint tooling if configured. Test CLI behavior through fake services,
not only through isolated helper assertions.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Filter syntax is documented grammar, not live operator discovery | High | G0 must approve explicitly labeled bundled grammar plus workspace field metadata; never misrepresent provenance. |
| Mixed documentation/server versions | High | Record source version per behavior and supported fallback; surface unknown capability honestly. |
| Singular names differ from REST collections | High | Use metadata `rest.url` and explicit aliases, not guessed plurals. Validate server-provided paths. |
| New generic targets allow URL/path injection | High | Validate all new-command path inputs and scope mappings before authenticated requests; adversarial tests. |
| Legacy helpers print or have broad fallbacks | Medium | Preserve adapters and caller contracts; isolate stricter new-command paths. |
| Incorrect generic write envelope | High | Pin collection POST and entity PUT separately with authoritative examples/fixtures. |
| Relationship/server normalization yields false verification | High | Define field-wise identity/canonicalization rules and explicit unverified results. |
| Stale stamps represented as HTTP 500 | High | Test documented error codes, preserve caller stamp, never retry mutation. |
| Successful write followed by verification failure | High | Return mutation evidence, failure status, and no-blind-retry warning. |
| Shared monolithic parser increases merge risk | Medium | Serialize production edits; small command-by-command increments. |
| Credentials/URL behavior accidentally changes | High | Run existing profile, migration, auth-error, URL, and cross-plugin contract tests. |
| Spec is ignored by git | Medium | User explicitly approved force-staging the plugin spec in `15b8812`; repository ignores and root spec remain unchanged. |

## Parallelization

Safe: source research across distinct API topics; independent review of already
landed slices; test-case design after command contracts are frozen.

Sequential: changes to `octane_client.py`, shared metadata resolution, new write
verification helpers, and `full-reference.md` edits. Do not launch concurrent
writers against these files. Test/document authors may work in isolated branches
with an agreed ownership boundary, but concurrency is unnecessary for this scope.

## T1 results and approval request

T1 delivered `api-contracts.md`: a source-backed capability matrix, proposed input,
concurrency and verification policies, exact payload distinctions, and honest
version/provenance limits. No production code or test cases changed.

Baseline evidence:
- Python 3.11.12; declared minimum Python 3.10 unchanged.
- Default Python lacked pytest; documented `uvx` runner resolved test dependencies.
- Octane: **106 passed, 1 skipped**, exit 0 (existing Windows/POSIX permission skip).
- Initial workspace: **4 failed, 324 passed, 2 skipped**, exit 1, because Windows
  helper subprocesses selected WSL Bash without Python.
- Existing `GIT_BASH` override selected the installed Git Bash: workspace
  **328 passed, 2 skipped**, exit 0 (existing unavailable-symlink skips).
- No tests were disabled or source changes made to fix environment failures.
- No dedicated build for docs-only work; workspace smoke suite checked compilation
  and minimum-version Python grammar. An explicit in-memory compile/Python 3.10
  grammar check also passed for all 4 Octane scripts; no bytecode was written.
  Staged whitespace validation passed. See `api-contracts.md` for commands.

**G0 approved.** The user accepted source-cited bundled filter grammar plus live
field metadata, version-qualified `work_items` keyword search, and safety policies
in `api-contracts.md`, and selected autonomous execution. Generic operations will
live in an adjacent standard-library-only helper module to avoid growing the
2,400-line legacy client; no new dependency or credential behavior is introduced.
The approved spec is explicitly staged despite the existing ignore rule.

## Final offline acceptance audit

| Spec success criterion | Evidence |
|---|---|
| 1. Seven generic commands and coherent profile/help behavior | All 39 commands plus root help tested without runtime; generic CLI tests, root smoke contract, existing profile/credential/URL suites |
| 2. Real entity/field metadata and explicit failures | Metadata fixtures cover irregular REST collections/methods, exact field identity, empty discovery, permissions, malformed metadata; documented/live provenance stays separate |
| 3. Native filters, sorting, paging, supported keyword mode | Entity tests check quoted params, one-page bounds/totals, sort capability, exclusive query/search, work_items-only JSON text_search, no undocumented fallback |
| 4. Generic get with target/field propagation | Entity tests cover safe aliases/metadata mapping, scope IDs, field selection, malformed/wrong-record responses, retained legacy output |
| 5. Safe single-record writes and read-back evidence | Entity tests cover raw JSON/references, one POST/PUT, method restrictions, lock stamps/conflicts, typed/null/reference comparisons, incomplete collections, uncertain outcomes/redaction, no mutation retries |
| 6. Existing workflows/auth remain compatible | 274 plugin tests (1 existing skip), 328 workspace tests (2 existing skips); legacy tags/delete/attachments dispatch and specialized updates explicitly covered; auth/profile implementation unchanged |
| 7. Agent/developer docs and success/failure interpretation | README, skill entry point, full reference, examples cover discovery/read/pre-authorized writes; 7 help contracts and 4 JSON blocks validated locally |

**Final commands/results:**
- From `plugins/octane`: `uvx --from pytest --with requests --with python-dotenv --with keyring pytest skills/alm-octane/tests -q --tb=short` — **274 passed, 1 skipped**.
- From repository root: `GIT_BASH='C:\\Users\\vnr\\AppData\\Local\\Programs\\Git\\bin\\bash.exe' uvx --from pytest pytest tests plugins/okf/tests -q --tb=short` — **328 passed, 2 skipped**; includes smoke/cross-plugin credential contracts.
- Compile every skill script in memory and parse with `ast.parse(feature_version=(3, 10))` — passed; no new dependency/build system.
- Run seven `uv run ... <command> --help` checks and parse fenced JSON examples locally — passed, no API requests.
- Task-scoped whitespace checks passed. T9 adversarial security review resolved findings in two cycles; T10 documentation review corrected verification-certainty wording. Cross-model review was skipped.

**Limitations/review boundary:** All verification uses fake HTTP/keyrings, not a
live deployment. Actual server version/search support and tenant-specific schemas
remain unverified. Python 3.10 grammar was checked, not a separate 3.10 runtime
matrix. Existing Windows permission/symlink skips remain. Exact MCP schemas/parity,
new dependencies, credential changes, generic deletion, URL-wrapper expansion,
and broad convenience-wrapper migration remain out of scope. Automated G4
acceptance is complete; final human review and separately authorized live
validation are not claimed.
