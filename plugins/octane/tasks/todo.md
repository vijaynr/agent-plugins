# Tasks: Generic ALM Octane CLI Foundation

## Execution rules

- [x] User explicitly approved the spec, G0 policies, autonomous T2–T10 execution,
  and committing the plugin spec despite its ignore rule.
- [x] Resolve G0 before feature changes; stop for approval if any public contract changes.
- [x] Keep production and test changes scoped to each vertical slice; write failing
  tests first, implement, then verify through CLI dispatch against fake services.
  Documentation-only T1/T10 used the TDD exemption.
- [x] Complete acceptance criteria and per-task verification before marking a task done.
- [x] No live Octane calls, real keyring access, or runtime dependency changes were
  authorized or performed. Autonomous execution used descriptive task-scoped commits.

All file paths and commands below are relative to `plugins/octane`, except paths
explicitly prefixed `../../` or commands labeled repository-root. Estimated
scopes exclude routine checkbox/result updates to these planning documents.
Task test files/contracts below were implemented; final results are in `plan.md`.
Use the dependency-equipped development environment or the `uvx` runner in
`plan.md`. Record test results; do not treat dependency resolution failure as a
passing or skipped validation.

## Phase 0 — Contract research

### T1: Establish source-backed generic command contracts

**Status:** Complete (research deliverable); G0 policies approved below.
See `api-contracts.md` for sources, policies, limitations, and baseline evidence.
No RED/GREEN test was added: this task changes documentation only.

**Description:** Resolve the high-risk API unknowns before building commands.
Record cited/versioned REST contracts and reproducible baseline test results.
This is a bounded research prerequisite; following tasks are end-to-end slices.

**Acceptance criteria:**
- [x] A capability matrix covers each command's endpoints, entity/collection
  mapping, supported methods, query/search/sort parameters, payload/response
  shapes, and metadata restrictions, citing authoritative versioned sources.
- [x] Define filter discovery provenance, supported text-search collections,
  path/ID validation rules, create-supplied-ID handling, lock support/prerequisite
  reads, relationship normalization, and mutation/verification output and exit
  states. An unavailable required capability triggers a proposed spec amendment,
  not an invented implementation.
- [x] Record Python 3.10+ compatibility, development test setup, and untouched
  plugin/workspace test baselines; no live service or credential-store access.

**Verification:**
- Manually follow source citations and compare examples with current helpers.
- `python -m pytest skills/alm-octane/tests -q`
- From repository root: `python -m pytest tests plugins/okf/tests -q`
- Record pre-existing failures and environment/tool limitations accurately.

**Dependencies:** Human spec/plan approval.

**Files likely touched (3):**
- `tasks/api-contracts.md` (new research artifact)
- `tasks/plan.md` (research outcomes/baseline results)
- `SPEC.md` (only if an amendment is needed, with approval)

**Estimated scope:** Medium; documentation/research only.

### G0: Research checkpoint — STOP for review

- [x] Required API contracts established and G0 composition/version limits approved.
- [x] User approved the documented policies; routine checkpoints run without pauses
  in autonomous mode, with exception stops for blockers/high-risk changes.
- [x] Baseline results and test setup are recorded without suppressing failures.

T1 verification: Octane suite **106 passed, 1 skipped**; workspace suite
**328 passed, 2 skipped** with the existing `GIT_BASH` override. The initial
missing-pytest and WSL-Bash environment failures are preserved in `api-contracts.md`.
No production code, test cases, dependencies, or ignored spec were changed.

## Phase 1 — First reads and entity discovery

### T2: Fetch one generic entity without breaking existing reads

**Status:** Complete. RED: 17 missing-command/help failures. GREEN: 124 plugin
passes/1 existing skip; workspace 328 passes/2 existing skips. Compile/3.10 grammar
and whitespace checks passed. Adjacent helper isolates generic command logic.

**Description:** Deliver `get-entity` from flags through request/JSON output and
introduce the small reusable fetch helper needed by later verification.

**Acceptance criteria:**
- [x] `get-entity` accepts entity type, ID, fields, profile, and workspace/shared-space
  arguments; returns one JSON envelope; root/subcommand help bypasses runtime
  configuration and network. New helpers return data; errors exit nonzero.
- [x] Validate collection, entity ID, and scope path segments; support explicit
  known aliases without unsafe arbitrary paths. Unknown names are not guessed
  into collections; T3 adds metadata-based resolution for discoverable names.
- [x] Existing `get_entity` printing adapter and subtype/work-item wrappers keep
  their signatures, flags, selected fields, request target, and output behavior.

**Verification:**
- `python -m pytest skills/alm-octane/tests/test_octane_generic_entities.py -q -k get_entity`
- `python -m pytest skills/alm-octane/tests/test_octane_generic_cli.py -q`
- `python -m pytest skills/alm-octane/tests -q`
- Tests exercise actual parsing/dispatch and assert rejected paths issue no HTTP calls.

**Dependencies:** T1, G0.

**Files likely touched (4):**
- `skills/alm-octane/scripts/octane_client.py`
- `skills/alm-octane/tests/test_octane_generic_entities.py` (new)
- `skills/alm-octane/tests/test_octane_generic_cli.py` (new)
- `skills/alm-octane/references/full-reference.md`

**Estimated scope:** Medium.

### T3: Discover available entities and their REST collections

**Status:** Complete. RED: 11 missing discovery/mapping failures after fixing test
fixture imports. GREEN: 135 plugin passes/1 existing skip; workspace 328 passes/2
existing skips; compilation/3.10 grammar passed.

**Description:** Deliver `get-entity-types` and extend generic target resolution
using the server's declared entity names, REST collection names, and methods.

**Acceptance criteria:**
- [x] CLI discovery returns server metadata, including available REST feature
  mappings, from the selected workspace without synthetic entity invention.
- [x] New generic reads resolve discovered names/collections including irregular
  plurals; metadata-derived paths are validated and never followed as full URLs.
  Any caching is invocation-local and scope-aware.
- [x] Unsupported collections/methods and failed discovery produce actionable
  errors, not arbitrary authenticated requests or silent fallback across hosts.

**Verification:**
- `python -m pytest skills/alm-octane/tests/test_octane_generic_metadata.py -q -k entity_types`
- `python -m pytest skills/alm-octane/tests/test_octane_generic_entities.py -q -k get_entity`
- Test singular/collection mappings, irregular plurals, malicious metadata URLs,
  empty discovery, HTTP failures, profile/scope propagation, and CLI help.

**Dependencies:** T2.

**Files likely touched (5):**
- `skills/alm-octane/scripts/octane_client.py`
- `skills/alm-octane/tests/test_octane_generic_metadata.py` (new)
- `skills/alm-octane/tests/test_octane_generic_entities.py`
- `skills/alm-octane/tests/test_octane_generic_cli.py`
- `skills/alm-octane/references/full-reference.md`

**Estimated scope:** Medium.

### G1: After T2–T3

- [x] Plugin tests pass; new help is independent of credentials/config/network.
- [x] Reviewed scope validation, metadata mappings, and unchanged legacy read output.
- [x] G1 verification complete; autonomous approval permits Phase 2 without a pause.

## Phase 2 — Field/filter discovery and paged queries

### T4: Expose generic entity field metadata

**Status:** Complete. RED: 5 missing-command cases. GREEN: 141 plugin passes/1
existing skip; workspace 328 passes/2 existing skips; compile/3.10 checks pass.
One initial legacy profile atomic replace failed with Windows Access Denied;
that unchanged test passed in isolation and the full suite passed on rerun.
No credential code/test changes or suppressions were made; transient cause unproven.

**Description:** Deliver `get-entity-field-metadata` with complete available field
attributes, honestly sourced to the chosen entity/workspace.

**Acceptance criteria:**
- [x] CLI returns logical names, types, references, and available required/editable
  constraints without manufacturing missing values or merging unrelated entity fields.
- [x] Requests honor verified metadata query restrictions and distinguish an empty
  result from unsupported metadata, auth failure, or transport failure.
- [x] Existing specialized metadata resolver behavior remains isolated and covered;
  any shared refactor preserves its return shape and fallback behavior.

**Verification:**
- `python -m pytest skills/alm-octane/tests/test_octane_generic_metadata.py -q -k field_metadata`
- `python -m pytest skills/alm-octane/tests -q`
- Inspect fake request logs to ensure forbidden metadata pagination/sorting is absent.

**Dependencies:** T3.

**Files likely touched (4):** Client script, `test_octane_generic_metadata.py`,
`test_octane_generic_cli.py`, and `references/full-reference.md`, all under
`skills/alm-octane/` in their respective directories.

**Estimated scope:** Medium.

### T5: Expose verified filter capabilities

**Status:** Complete. RED: 2 missing-command cases. GREEN: 144 plugin passes/1
existing skip; workspace 328 passes/2 skips; compilation/3.10 grammar passed.
Help-test assertion generalized to check the requested subcommand name.

**Description:** Deliver `get-filter-metadata` using the mechanism established at
G0, including explicit provenance and version/collection limitations.

**Acceptance criteria:**
- [x] CLI exposes verified syntax/operators and available entity/field capability
  constraints, clearly separating server metadata from documented language rules.
- [x] Unsupported server/version/capability paths return an honest actionable error;
  no invented endpoint or static operator list represented as workspace discovery.
- [x] Help, selected profile/scope behavior, output envelope, and failures are
  exercised end-to-end; supported limitations are documented.

**Verification:**
- `python -m pytest skills/alm-octane/tests/test_octane_generic_metadata.py -q -k filter_metadata`
- `python -m pytest skills/alm-octane/tests/test_octane_generic_cli.py -q`
- Manually compare fixtures/provenance against approved `tasks/api-contracts.md`.

**Dependencies:** T1/G0's explicit feasible contract, T4.

**Files likely touched (4):** Client script, `test_octane_generic_metadata.py`,
`test_octane_generic_cli.py`, and `references/full-reference.md` under the skill.

**Estimated scope:** Medium. Blocked if G0 cannot substantiate this capability.

### T6: Retrieve a filtered, searched, sorted page of entities

**Status:** Complete. RED: 10 list-command cases; GREEN: plugin 156 passed/1
existing skip, workspace 328 passed/2 existing skips; compile/3.10 grammar passes.

**Description:** Deliver `get-entities`, including native queries and supported
text search as distinct modes, field selection, sorting, and explicit pagination.

**Acceptance criteria:**
- [x] CLI supports mutually exclusive `--query`/`--search`, `--fields`,
  `--order-by`, positive limit/default 50, and nonnegative offset/default 0.
  Fetch one page, preserve server totals, and report requested page parameters.
- [x] Native filters are encoded exactly once without heuristic reinterpretation;
  search escaping and supported collections follow the approved source contract.
  Unsupported search/sort behavior is rejected rather than ignored.
- [x] Empty results, special characters, invalid bounds, target validation,
  read-only/auth failures, and optional parameters have CLI-to-HTTP tests.

**Verification:**
- `python -m pytest skills/alm-octane/tests/test_octane_generic_entities.py -q -k get_entities`
- `python -m pytest skills/alm-octane/tests/test_octane_generic_cli.py -q`
- `python -m pytest skills/alm-octane/tests -q`

**Dependencies:** T2, T3, approved query/search contract from T1/T5.

**Files likely touched (4):** Client script, `test_octane_generic_entities.py`,
`test_octane_generic_cli.py`, and `references/full-reference.md` under the skill.

**Estimated scope:** Medium.

### G2: After T4–T6

- [x] All five discovery/read commands pass focused and plugin regression tests.
- [x] Reviewed metadata provenance, search limitations, encoding, and pagination.
- [x] G2 verification passed; autonomous approval covers generic mutation code
  with fake HTTP only. No live writes are authorized.

## Phase 3 — Verified mutations

### T7: Create one generic entity from a JSON file

**Status:** Complete. RED: 16 create cases; review-driven RED cases additionally
covered reference validation, completeness flags/totals, read evidence and
unexpected create statuses. GREEN: plugin 185 passed/1 existing skip; workspace
328 passed/2 skips; compile/3.10 grammar passed. Fresh-context review ran 3 bounded
cycles. Actionable findings fixed with tests; last-cycle concerns about nullable
empty-string normalization and excluding transport stamps were contract misreads:
these are explicitly approved in api-contracts.md. Cross-model review skipped in
autonomous mode. RuntimeError transport fake is valid: isolated_runtime explicitly
sets requests.RequestException=RuntimeError; no shared transport change needed.

**Description:** Deliver `create-entity`, including payload validation, a single
POST, read-back verification, and an unambiguous result for uncertain outcomes.

**Acceptance criteria:**
- [x] Accept one nonempty UTF-8 field object; preserve relationships and raw
  caller values. Reject malformed/missing files, arrays, envelopes, empty objects,
  invalid targets, and create IDs prohibited by the approved contract before mutation.
- [x] Perform one correctly shaped POST and read the returned ID in the same
  workspace. Compare supplied fields using approved normalization rules; emit
  separate mutation and verification evidence through one JSON result.
- [x] Missing IDs, lost responses/timeouts, failed read-back, unreadable fields,
  or mismatches return nonzero status with evidence and safe no-blind-retry guidance.
  No automatic mutation retry, content formatting, or hidden remediation.

**Verification:**
- `python -m pytest skills/alm-octane/tests/test_octane_generic_entities.py -q -k create_entity`
- `python -m pytest skills/alm-octane/tests/test_octane_generic_cli.py -q`
- Assert fake HTTP logs contain exactly one POST and correctly scoped verification
  GET; invalid input causes zero mutations; compare nested relationships and nulls.

**Dependencies:** T2, T3, T4, G2.

**Files likely touched (4):** Client script, `test_octane_generic_entities.py`,
`test_octane_generic_cli.py`, and `references/full-reference.md` under the skill.

**Estimated scope:** Medium. Shared JSON/verification helpers are introduced only
as needed for this complete path, not as a separate infrastructure task.

### T8: Update selected entity fields with concurrency protection

**Status:** Complete. RED: 13 update cases plus 4 invalid stamps and 1 unsupported
caller-stamp case; GREEN: 205 plugin passes/1 existing skip, workspace 328 passes/2
skips; compilation/3.10 grammar passed. Fresh-context review fixed unsupported
caller-stamp handling with a regression, then found no substantive defects.

**Description:** Deliver `update-entity` with explicit ID, partial updates,
lock-stamp handling, and read-back using T7's evidence model.

**Acceptance criteria:**
- [x] Validate the same JSON contract plus target/embedded-ID consistency; preserve
  omitted fields and nested relationship payloads. No phase/HTML/tag normalization
  is inherited from convenience commands.
- [x] Preserve caller-provided stamps; otherwise fetch a current stamp where
  supported. Failed required reads block mutation; unsupported stamp fields follow
  the approved contract rather than silently bypassing available protection.
- [x] Send one correctly shaped PUT; verify supplied fields afterward. Surface
  stale stamps (including documented HTTP 500/version-conflict responses), rejected
  workflow transitions, uncertain writes, and verification failure without replay.

**Verification:**
- `python -m pytest skills/alm-octane/tests/test_octane_generic_entities.py -q -k update_entity`
- `python -m pytest skills/alm-octane/tests -q`
- Assert GET/PUT/GET ordering where required, untouched caller stamps, zero PUT on
  invalid input/prerequisite failure, and no automatic second PUT on any error.

**Dependencies:** T7 (input/verification helpers), T2/T3/T4, G2.

**Files likely touched (4):** Client script, `test_octane_generic_entities.py`,
`test_octane_generic_cli.py`, and `references/full-reference.md` under the skill.

**Estimated scope:** Medium.

### G3: After T7–T8

- [x] Reviewed payloads, field comparisons, stamp semantics, uncertain outcomes, and
  secret-safe errors; all plugin tests pass.
- [x] Confirmed single mutation/no retry, unchanged authentication, and existing
  host/conversation approval boundary; no invented confirmation flags.
- [x] G3 verification passed; autonomous approval permits compatibility/doc closure.

## Phase 4 — Compatibility and handoff

### T9: Close CLI compatibility and security regression coverage

**Status:** Complete. RED: 8 boundary/error cases plus a malformed error-code case
and 11 security-review cases; GREEN: plugin 274 passed/1 existing skip, workspace
328 passed/2 skips (including smoke/cross-plugin credential contracts); compile/3.10
checks passed. All 39 command helps tested without runtime. Minimal generic-only
boundary fixes were made with closure tests: safe failure bodies, record identity,
empty search, uncertain mutation redaction, and reusable update path validation.
No legacy auth/error changes. Security review resolved findings in 2 cycles.

**Description:** Add cross-cutting contract coverage for the finished surface,
including retained convenience commands and repository smoke expectations.

**Acceptance criteria:**
- [x] All seven commands and retained legacy command signatures appear in CLI
  tests; no-credential root/subcommand help never reads keyring/config or performs
  migration/network. Profile and workspace propagation remain coherent.
- [x] Cover old read adapters and representative specialized writes, tags,
  deletion, and attachment payload behavior to ensure generic refactors did not
  change them; existing URL/auth/profile suites remain green.
- [x] Negative target/file inputs and service error fixtures stay secret-safe;
  smoke tests verify the new surface without requiring new tools or dependencies.

**Verification:**
- `python -m pytest skills/alm-octane/tests -q`
- `python -m pytest ../../tests/test_skill_cli_smoke.py ../../tests/test_credential_config_contract.py -q`
- From repository root: `python -m pytest tests plugins/okf/tests -q`
- Review the diff for unrelated changes; record failures rather than disabling tests.

**Dependencies:** T2–T8, G3.

**Files likely touched (up to 4):**
- `skills/alm-octane/tests/test_octane_generic_cli.py`
- `skills/alm-octane/tests/test_octane_generic_entities.py`
- `skills/alm-octane/tests/test_octane_generic_metadata.py`
- `../../tests/test_skill_cli_smoke.py`

**Estimated scope:** Medium; closure tests exposed generic-only boundary defects
fixed here as part of safety acceptance (helper module/reference and repository
test guidance included). No additional feature, dependency, or auth scope added.

### T10: Publish agent/developer workflows and acceptance evidence

**Status:** Complete (documentation-only TDD exemption; CLI description text only,
no behavioral change). All 7 help contracts and 4 JSON blocks validated locally;
plugin 274 passed/1 skipped, workspace 328 passed/2 skipped, compile/3.10 checks
passed. Documentation review corrected overconfident failed-verification wording.
Reference/root-resolution consistency and stale MCP description were corrected.

**Description:** Finish concise entry-point guidance and examples for discovery,
querying, and pre-authorized verified writes; audit the entire spec.

**Acceptance criteria:**
- [x] Skill instructions select the smallest generic or convenience command;
  README/examples cover discovery-to-read and JSON-create/update with relationship
  samples, exact flags, pagination/search limits, and verification-failure outcomes.
- [x] Existing approval/authentication guidance remains accurate; no dependency,
  CI, credential, generic-delete, or attachment-transfer scope expansion is implied.
- [x] Review each spec success criterion against tests and docs; record commands,
  results, limitations, and completion checkpoint evidence in `tasks/plan.md`.

**Verification:**
- Cross-check all documented command names/flags with CLI help; do not execute API
  examples against a real workspace. Check sample JSON locally for valid syntax.
- `python -m pytest skills/alm-octane/tests -q`
- From repository root: `python -m pytest tests plugins/okf/tests -q`

**Dependencies:** T9.

**Files likely touched (4):**
- `skills/alm-octane/SKILL.md`
- `README.md`
- `skills/alm-octane/references/examples.md`
- `tasks/plan.md`

**Estimated scope:** Medium; full command reference was updated with each slice.

### G4: Completion checkpoint — human review

- [x] All task acceptance criteria and spec success criteria are met offline.
- [x] Plugin, cross-plugin credential, and required workspace validations pass.
- [x] Diff and security review confirm no unrelated changes or exposed secrets.
- [x] Spec/plan/task artifacts are included intentionally when committing;
  user explicitly approved force-staging the plugin spec (recorded in `15b8812`).
- [ ] Human reviews the complete change before merge or further live validation.
