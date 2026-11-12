# Spec: Generic ALM Octane CLI Foundation

## Status

T1–T10 implemented and offline-validated; final human G4 review pending.
The user approved autonomous implementation and G0 policies in
`tasks/api-contracts.md`, covering code, offline tests, and task-scoped commits,
not live Octane access. See `tasks/plan.md` for final acceptance evidence.
The Octane plugin is the project root for this feature. The repository-root
`SPEC.md` (durable credential configuration) remains unchanged.

## Objective

Extend the existing `alm-octane` Python CLI with seven generic discovery and
entity-operation commands. Agents and developers should be able to discover
workspace capabilities and operate on supported entities without needing a new
specialized command for each entity type.

Use a two-layer design:

1. A reusable generic REST foundation for metadata, reads, creates, and updates.
2. Existing convenience commands for workflow-specific behavior.

This is a direct REST CLI, not an MCP client. The seven supplied MCP tool
descriptions inform the capability model; exact MCP schema parity is not claimed.

### Scope

- Add `get-entity-types`, `get-entity-field-metadata`, `get-filter-metadata`,
  `get-entities`, `get-entity`, `create-entity`, and `update-entity`.
- Support explicit workspace/shared-space targeting and existing named profiles.
- Preserve existing command names, arguments, output contracts, URL dispatch,
  authentication precedence, and specialized workflow behavior.
- Expose reusable functions returning data rather than printing internally;
  keep JSON rendering at the new command boundary.
- Migrate existing wrappers incrementally, only where behavior remains identical.
  Migrating all wrappers is not a first-release requirement.
- Retain existing deletion and attachment-transfer capabilities separately.

### Out of scope

- An MCP server/client dependency or deployment.
- A new generic deletion command, bulk writes, or arbitrary HTTP requests.
- New credential storage, login behavior, or approval mechanisms.
- Automatic repair of workflow transitions, required fields, or permissions.
- Rewriting all existing commands or expanding URL dispatch to generic operations.
- Modifying other plugins.

## Tech Stack

- Python 3.10+, matching existing script metadata and skill documentation; no
  minimum-version change.
- `uv run` with existing PEP 723 dependency declarations.
- Existing `requests`, `python-dotenv`, and `keyring` dependencies.
- Standard-library `argparse`, `json`, and `pathlib` for command parsing and inputs.
- `pytest` and mocks for deterministic verification; no new runtime dependencies.

## Commands

All commands below run from `plugins/octane`.
API examples are proposed interface contracts, not permission to execute them.
`--profile` remains a top-level option. Each new command accepts optional
`--shared-space-id` and `--workspace-id` using existing resolution behavior.

### Discovery

```bash
uv run skills/alm-octane/scripts/octane_client.py --help
uv run skills/alm-octane/scripts/octane_client.py --profile staging get-entity-types --shared-space-id 1001 --workspace-id 1002
uv run skills/alm-octane/scripts/octane_client.py --profile staging get-entity-field-metadata --entity-type defects --shared-space-id 1001 --workspace-id 1002
uv run skills/alm-octane/scripts/octane_client.py --profile staging get-filter-metadata --entity-type defects --shared-space-id 1001 --workspace-id 1002
```

- Entity-type discovery returns server-supported entity names and available metadata.
- Field discovery returns logical names, types, references, and available
  required/read-only constraints without inventing absent metadata.
- Filter discovery returns documented/server-supported syntax and operators.
  Do not guess an endpoint or silently present a static list as workspace metadata.

### Reads

```bash
uv run skills/alm-octane/scripts/octane_client.py --profile staging get-entities --entity-type defects --query 'id=1234' --fields id,name,phase --order-by id --limit 20 --offset 0 --shared-space-id 1001 --workspace-id 1002
uv run skills/alm-octane/scripts/octane_client.py --profile staging get-entities --entity-type work_items --search 'authentication' --fields id,name,subtype --limit 20 --offset 0
uv run skills/alm-octane/scripts/octane_client.py --profile staging get-entity --entity-type defects --entity-id 1234 --fields id,name,phase,client_lock_stamp
```

- `--entity-type` names a supported collection; support existing documented
  aliases without allowing arbitrary paths, URLs, query strings, or traversal.
- `--query` accepts a native Octane filter expression. Encode it once through
  request parameters; do not reinterpret its contents as plain search text.
- `--search` is an explicit text-search mode, mutually exclusive with `--query`.
  Verify supported Octane semantics before implementation. If only specific
  entities/fields support it, document that limitation and reject unsupported use.
- `--fields` selects a comma-separated field list.
- `--order-by` uses verified Octane sorting syntax; document direction examples.
- `--limit` is positive; `--offset` is nonnegative. Defaults: 50 and 0.
- Fetch one page per invocation. Preserve server totals when supplied and make
  the requested pagination evident; do not silently fetch the entire workspace.

### Writes

```bash
uv run skills/alm-octane/scripts/octane_client.py --profile staging create-entity --entity-type stories --data-file /path/to/story.json --shared-space-id 1001 --workspace-id 1002
uv run skills/alm-octane/scripts/octane_client.py --profile staging update-entity --entity-type defects --entity-id 1234 --data-file /path/to/update.json --shared-space-id 1001 --workspace-id 1002
```

- Require a UTF-8 JSON file containing one nonempty field object, not an Octane
  `data` envelope or a batch array. The CLI constructs the server envelope.
- Accept arbitrary supported field names and nested relationship objects; do not
  limit writes to the fields of existing convenience commands.
- Reject malformed JSON, missing files, arrays, empty objects, and embedded target
  IDs that conflict with explicit targeting before any mutation.
- Preserve caller values: generic writes do not convert Markdown, normalize
  phases, create tags, or perform workflow remediation. Document the convenience
  commands as the preferred route when those behaviors are needed.
- Update only supplied fields. Fetch and send `client_lock_stamp` where supported.
  If a caller supplies a stamp, preserve its concurrency intent; never replace a
  stale caller stamp silently. Surface conflicts without retrying the write.
- Perform one mutation, followed by a read of the same returned/explicit ID and
  workspace. Never retry creates or updates automatically.
- Return mutation evidence and verification evidence separately. A successful
  mutation followed by failed verification must explicitly say the write may
  have succeeded, return a nonzero exit status, and discourage blind retries.
- Verification must distinguish a successful read from confirmation that requested
  fields were applied, accounting for documented server normalization.

### Validation commands

```bash
# From plugins/octane; dependency-equipped development Python environment
python -m pytest skills/alm-octane/tests -q
python -m pytest ../../tests/test_skill_cli_smoke.py -q

# From repository root; required workspace validation before merge
python -m pytest tests plugins/okf/tests -q
```

There is no new build step. Use existing lint/type-check tooling if configured;
do not introduce tooling solely for this feature. First implementation work must
confirm the development test dependencies and document reproducible setup.

## Project Structure

```text
plugins/octane/
  SPEC.md                                  This specification
  README.md                                User-facing generic CLI examples
  skills/alm-octane/
    SKILL.md                               Discovery, command selection, safety
    scripts/
      octane_client.py                     CLI parsing, shared REST functions
      octane_url.py                        Existing URL handling, preserved
      credential_config.py                 Existing configuration, preserved
      octane_token.py                      Existing login/lifecycle, preserved
    references/
      full-reference.md                    Complete command and payload contracts
      examples.md                          Discovery/read/write examples
    tests/
      test_octane_generic_metadata.py       Discovery contracts and failures
      test_octane_generic_entities.py       Reads, writes, pagination, verification
      test_octane_generic_cli.py            Parsing, help, output, compatibility
```

Prefer a small additive implementation in the existing script. Extract a
plugin-local helper module only if needed for a clear reusable boundary, not a
large framework refactor. Update repository smoke coverage where appropriate.
Follow `docs/agent-skills-guide.md` and dependency/test documentation rules.

## Code Style

Match surrounding Python conventions: snake_case functions, explicit types,
small helpers, existing JSON envelopes, no hidden global reconfiguration.
Generic transport functions return envelopes; CLI handlers print once.
Illustrative style, not a prescribed helper implementation:

```python
def fetch_entity_record(
    collection: str,
    entity_id: str,
    fields: Optional[str] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> Dict[str, Any]:
    url = entity_url(collection, entity_id, workspace_id, shared_space_id)
    params: Dict[str, Any] = {}
    if fields:
        params["fields"] = fields
    return request_json("GET", url, params=params)
```

- Reuse authenticated request/session helpers and profile resolution.
- Preserve `{"ok": true, "data": ...}` success and `{"ok": false, "error": ...}`
  failure conventions; additive evidence fields are allowed for new commands.
- Emit one JSON result to stdout for operations; diagnostics go to stderr.
  Standard argparse help/usage remains conventional.
- New command errors return nonzero exit status and safe actionable messages.
- Avoid unrelated formatting, renaming, authentication changes, and speculative
  abstractions. Do not change existing command output to suit the new layer.

## Testing Strategy

Use pytest with mocked HTTP/session responses, isolated configuration directories,
and fake keyrings. No real network or real credential-store access.

Required coverage:

1. All seven commands appear in help; root and subcommand help need no credentials,
   profile migration, keyring access, or network calls.
2. Metadata routes, parameters, available field attributes, and unsupported metadata
   behavior match documented contracts and representative fixtures.
3. Query, search, fields, sorting, pagination, and workspace targeting reach the
   transport correctly. Cover quoting/encoding, empty pages, totals, invalid bounds,
   and mutually exclusive search/query inputs.
4. Collection/path validation rejects attempts to escape the API scope.
5. JSON object and relationship payloads survive without unwanted transformation;
   malformed input never triggers a mutation.
6. Create/update envelopes, partial updates, concurrency stamps, conflict handling,
   returned IDs, and subsequent verification reads are correct.
7. Write-success/verification-failure and field-mismatch outcomes are unambiguous;
   network errors and 401/403 responses remain secret-safe.
8. Existing authentication, URL parsing, and convenience command regression tests
   pass. Add targeted compatibility cases for any wrappers actually migrated.
9. CLI smoke tests and required workspace validation pass.

No arbitrary coverage percentage is introduced. Every new branch of validation,
mutation, verification, and error behavior needs an explicit automated case.
Live smoke testing is optional and requires separate user permission; it is not
part of the default acceptance gate.

## Boundaries

### Always

- Preserve existing CLI and durable credential behavior.
- Validate targets and payloads, use the selected profile, and keep requests within
  its configured host and explicit/resolved workspace.
- Require user intent in the orchestrating conversation before writes; direct CLI
  invocation remains an already-authorized operation.
- Verify writes and report uncertain outcomes without automatic replay.
- Test offline and update skill/reference/README documentation with the feature.
- Verify Octane API behavior against authoritative documentation before choosing
  endpoints, filter/search semantics, or concurrency rules.

### Ask first

- New dependencies, raised Python minimums, authentication changes, or CI changes.
- Breaking existing flags, outputs, workflow behavior, or removing commands.
- Bulk operations, generic deletion, additional generic commands, or an MCP bridge.
- Live workspace access; request explicit confirmation for each proposed live write.
- An unavailable API capability requiring a reduced or changed public contract.

### Never

- Expose secrets, commit credentials, or contact a fallback host with profile secrets.
- Bypass host/conversation approval with an invented `--confirmed` flag.
- Invent metadata endpoints/operators, silently ignore unsupported arguments, or
  claim MCP parity without checking schemas.
- Remove deletion/attachment commands or silently strip their safety behavior.
- Remove failing tests, overwrite unrelated specs, or modify unrelated plugins.

## Success Criteria

- Seven documented generic commands have working help and deterministic tests.
- Users can discover entities/fields/filter capabilities, retrieve a page or one
  entity, and create/update a supported record with relationship fields.
- Read operations support documented filtering, search, sorting, and pagination.
- Generic writes preserve partial-update semantics, concurrency protection where
  supported, and explicit verification evidence.
- Existing commands, profile selection, URL handling, and safety behavior remain
  compatible; tests provide evidence for touched paths.
- No new runtime dependency or MCP service is required.
- Required test suites pass and documentation provides executable examples.

## Resolved Research and Remaining Limitations

User decisions and G0 policies are approved; source/version details are recorded
in `tasks/api-contracts.md` and implementation evidence in `tasks/plan.md`.

- Filter metadata composes cited, bundled Octane 26.1 grammar with separately
  labeled live workspace field metadata; no operator-discovery endpoint is claimed.
- Keyword search is restricted to `work_items` through ValueEdge-documented
  `text_search`; deployed-server support is unverified and failures never trigger
  an alternative search or host fallback.
- Generic logic is isolated in adjacent, standard-library-only `octane_generic.py`.
  Legacy commands retain their interface/behavior; no bulk wrapper migration.
- Mutations require documented create/update statuses and matching safe returned
  IDs before read-back can be considered verified. Uncertain response bodies and
  raw failure diagnostics are omitted; server-version conflicts retain safe codes.
- Validation is offline only. No live-server compatibility or exact MCP schema
  parity is claimed. Python 3.10 syntax is checked; baseline/runtime versions and
  existing platform skips are documented in the task records.

Future changes to these contracts require spec updates and user approval.
