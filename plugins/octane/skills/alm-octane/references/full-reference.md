# ALM Octane Python Skill

Use this skill only for ALM Octane work. Keep context small: do not
read examples, references, or Python source unless needed for the current task
or for debugging inconsistent CLI behavior.

## Resolve the Skill Root

Resolve `SKILL_ROOT` before commands: prefer this repository's Octane skill,
then an installed Copilot plugin, then direct user skill roots. The local
candidates below support repository-root, plugin-root, and skill-root working
directories. Credentials are user-level profiles, not a required local `.env`.

```bash
SKILL_ROOT=""
for d in "plugins/octane/skills/alm-octane" "skills/alm-octane" "." "$HOME"/.copilot/installed-plugins/*/octane/skills/alm-octane "$HOME/.copilot/skills/alm-octane" "$HOME/.agents/skills/alm-octane"; do
  if [ -f "$d/SKILL.md" ] && [ -f "$d/scripts/octane_client.py" ]; then SKILL_ROOT="$(cd "$d" && pwd)"; break; fi
done
[ -n "$SKILL_ROOT" ] || { echo "ALM Octane skill not found"; exit 1; }
```

Invoke scripts by absolute path:

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" <subcommand> [args]
uv run "$SKILL_ROOT/scripts/octane_url.py" [args]
```

The scripts declare dependencies via PEP 723 inline metadata and must be run
with `uv run`. Every command prints a JSON envelope: `{"ok": true, "data": ...}`
or `{"ok": false, "error": "..."}`. Always parse JSON output.

## Credential Profiles and Configuration

Preferred authentication uses a named durable profile. The client secret is stored in OS keyring service `AgentDevelopmentToolkit:alm-octane`; `octane.json` stores only endpoint, keyring username, shared-space ID, workspace ID, and timeout.

| Platform | Default `octane.json` directory |
|---|---|
| Windows | `%APPDATA%\AgentDevelopmentToolkit` |
| macOS | `~/Library/Application Support/AgentDevelopmentToolkit` |
| Linux | `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit` |

`AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` overrides the directory on every platform. Runtime profile precedence is `octane_client.py --profile <name>`, then `OCTANE_PROFILE`, then `active_profile` in the stable document. `octane_url.py --profile <name> ...` forwards selection to its adjacent client.

Create and manage profiles from the skill root:

Inject `OCTANE_LOGIN_SECRET` through the launcher's masked environment without placing its value in command text, then run:

```bash
uv run scripts/octane_token.py login \
  --profile default --base-url "https://octane.example.com" \
  --user "<api-client-id>" --shared-space-id "<id>" --workspace-id "<id>" --timeout 30
uv run scripts/octane_token.py profiles
uv run scripts/octane_token.py use-profile --profile default
uv run scripts/octane_token.py delete-profile --profile default
```

Use `login --no-activate` to preserve the current active selection. Profile deletion removes metadata only and never deletes keyring entries. An activating login verifies the effective credentials unless `--skip-test` is explicitly provided. With `--no-activate`, verify the new inactive profile explicitly after selecting it. Login attempts to roll back prior metadata/keyring state after failed keyring writes, metadata writes, or verification and reports incomplete recovery.

### Legacy migration

When no stable document exists, client startup checks the executing skill root, `~/.copilot/skills/alm-octane`, and `~/.agents/skills/alm-octane` for keyring-backed `.env` metadata. One unambiguous, usable candidate is migrated to `default`; equivalent aliases are deduplicated. Sources are never changed. Conflicts, missing keyring entries, and backend failures stop before network access. Direct-secret files remain usable but are never migrated. Help commands and an existing stable document skip migration.

### Direct CI fallback

For CI/non-interactive execution, provide the complete coherent set `OCTANE_BASE_URL`, `OCTANE_CLIENT_ID`, and `OCTANE_CLIENT_SECRET`. Shared-space, workspace, and timeout values are optional and use client defaults when omitted. Complete direct credentials override a selected profile. When a stable profile is selected, partial endpoint, identity, keyring-user, or secret overrides are rejected before keyring/network access to prevent host/credential mismatch. Never commit direct secrets or pass them in normal chat.

| Variable | Description |
|---|---|
| `OCTANE_PROFILE` | Named stable profile when API `--profile` is absent |
| `OCTANE_BASE_URL` | Octane instance URL for a complete direct/keyring override |
| `OCTANE_CLIENT_SECRET_KEYRING_USER` | Keyring username for a complete explicit keyring-backed override |
| `OCTANE_CLIENT_ID` | API client ID for complete direct credentials |
| `OCTANE_CLIENT_SECRET` | Direct CI secret; never stored in profile metadata or migrated |
| `OCTANE_SHARED_SPACE_ID` | Shared space ID |
| `OCTANE_WORKSPACE_ID` | Workspace ID |
| `OCTANE_TIMEOUT` | Positive request timeout in seconds |

## Generic commands

From the skill root:

```bash
uv run scripts/octane_client.py --profile staging get-entity --entity-type defects --entity-id 1234 --fields id,name
```

`get-entity` returns the existing JSON envelope and exits nonzero on failure.
It accepts `--workspace-id` and `--shared-space-id`; otherwise the selected
profile supplies them. Known singular aliases are accepted. Target path segments
must be safe identifiers, not URLs, encoded paths, or traversal. Legacy entity
read commands retain their flags, default fields, and output.

```bash
uv run scripts/octane_client.py get-entity-types --workspace-id 1003 --shared-space-id 1001
```

`get-entity-types` returns actual workspace metadata. Unknown names in generic
reads resolve via metadata `rest.url`/`rest.methods`, including irregular plural
collections; they are never guessed. Metadata URLs must be safe collection names,
not full URLs or nested paths. Empty discovery is distinct from failed discovery.
Stable known read aliases avoid an unnecessary metadata round trip.

```bash
uv run scripts/octane_client.py get-entity-field-metadata --entity-type defects
```

Field discovery uses the exact metadata entity name and preserves reported types,
references, required/editable constraints, and filter/sort capabilities. Missing
attributes remain missing. No collection pagination/sort flags are sent to the
field-metadata endpoint. Wrong-entity responses and failed discovery stop; they
are never merged with another entity's fields or guessed conventions.

```bash
uv run scripts/octane_client.py get-filter-metadata --entity-type defects
```

Filter metadata combines **bundled documented grammar** (`source: documentation`,
Octane 26.1, cited URL) with **live field metadata** (`source: workspace`). It is
not a server operator-discovery endpoint. Operators vary by field type; missing
capabilities are unknown, and `filterable: false` is not support. Failed field
reads fail the command rather than producing fabricated workspace capabilities.

```bash
uv run scripts/octane_client.py get-entities --entity-type defects --query 'id EQ 1234' --fields id,name --order-by=-name,id --limit 20 --offset 0
uv run scripts/octane_client.py get-entities --entity-type work_items --search 'login fails' --fields id,name
```

`get-entities` retrieves exactly one page, with defaults limit 50, offset 0,
and sort `id`. It preserves server totals and adds requested `pagination` values.
`--query` takes native syntax **without outer double quotes** (the CLI adds them
once); it never guesses whether text is a filter. `--search` is mutually exclusive
and serializes the term in `text_search` JSON, only on `work_items`. This keyword
API is documented for ValueEdge latest; server support is required and no BK/name
fallback is attempted on rejection. Other collections reject search explicitly.

Flat `--fields` and comma-separated sort fields are supported; use a leading `-`
for descending order. Explicitly unsortable fields are rejected using metadata;
other schema/query restrictions remain server-validated. Limit must be positive,
offset nonnegative. The server's configured maximum page size is authoritative;
the CLI neither hardcodes the MCP maximum nor silently truncates results.

```bash
uv run scripts/octane_client.py create-entity --entity-type stories --data-file /path/to/story.json
```

`create-entity` accepts one nonempty UTF-8 JSON field object, not a `data` envelope
or array. Duplicate keys, nonstandard constants, top-level IDs, missing files,
and unsafe field/target segments are rejected before mutation. Nested relationship
objects are preserved; generic writes do not format Markdown/HTML, normalize phases,
or create tags. Consult actual field metadata for required fields/reference types.

Creation validates advertised REST methods, sends one POST, then reads the returned
ID in the same workspace. Results separate `mutation.outcome` from
`verification.read_ok`, `verification.matched`, and per-field comparison evidence.
A successful read alone is not verification. Missing IDs, unreadable/missing fields,
changed values, wrong read-back IDs, or failed reads return nonzero status and warn
against blind retries. No mutation is automatically replayed, even on timeout.
Relationship verification uses identity rather than expanded display fields;
complete multi-reference identities are compared without order. Read-back totals
must establish completeness and `exceeds_total_count` must not be true. Creation
requires documented HTTP 201; other successful-looking statuses remain uncertain.
Metadata-defined reference shapes/IDs/types are validated before the POST. Failed
verification includes its own read status/URL, separate from mutation status. Only documented
nullable-string empty-to-null normalization is accepted; no broad text conversion.

```bash
uv run scripts/octane_client.py update-entity --entity-type defects --entity-id 1234 --data-file /path/to/update.json
```

`update-entity` sends only supplied fields in a plain-object PUT, followed by a
read of that explicit ID. A matching redundant payload ID is removed; conflicting
IDs and ID/stamp-only payloads are rejected. Caller-supplied nonnegative integer
`client_lock_stamp` values are preserved exactly, never refreshed after conflict.
Otherwise the CLI fetches an advertised stamp first; missing/invalid stamps or a
failed/wrong-target prerequisite read block the update. If successful exact metadata
lacks stamp support, `concurrency` explicitly reports protection unavailable.
Supplying a stamp to such an entity is rejected rather than silently dropping the
caller's concurrency intent; remove it only if an unprotected update is intended.

PUT success requires HTTP 200 and a matching returned ID. Stale-stamp
errors may be HTTP 500 (`platform.version_conflict`), not only 409. Failed mutations
are never refreshed/replayed. Verification uses the same evidence contract as
creation, excluding transport identity/stamp fields from changed-field equality.

Generic errors omit raw server bodies, stack traces, and transport exception text
that could echo credentials. Safe HTTP status/URL and recognized version-conflict
or entity-not-found codes remain; HTTP 401/403 retain distinct classifications.
Malformed successful-looking mutation bodies are reported as unknown outcomes with
safe evidence only, not emitted as diagnostic `data`. Update responses must identify
the target record before verification. Legacy command error formats are unchanged.

The adjacent `octane_generic.py` module is an internal standard-library-only
helper, not an executable CLI; authentication stays in `octane_client.py`.

## Supported Commands

`scripts/octane_client.py` supports:

- `get-entity-types`
- `get-entity-field-metadata`
- `get-filter-metadata`
- `get-entities`
- `get-entity`
- `create-entity`
- `update-entity`
- `get-work-item`
- `get-defect`
- `get-feature`
- `get-story`
- `search-all`
- `create-feature`
- `update-feature`
- `create-defect`
- `update-defect`
- `create-story`
- `update-story`
- `create-story-under-feature`
- `get-story-parent-feature`
- `list-feature-items`
- `update-feature-security`
- `update-story-status`
- `delete-backlog-item`
- `create-comment`
- `read-comment`
- `add-attachment`
- `list-attachments`
- `delete-attachment`
- `download-attachment`
- `get-manual-test`
- `get-suite-runs`
- `get-run-history`
- `list-work-items`
- `list-tasks`
- `add-task`
- `list-tags`
- `add-tag`
- `list-phases`

`scripts/octane_url.py` supports:

- default action: fetch entity details from URL
- `--action get-favorite`
- `--action list-favorite-items`
- `--action get-work-item`
- `--action get-defect`
- `--action get-story`
- `--action get-feature`
- `--action get-manual-test`
- `--action create-story-under-feature`
- `--action update-feature`
- `--action update-story`
- `--action delete-backlog-item`
- `--action get-story-parent-feature`
- `--action list-feature-items`
- `--action update-feature-security`
- `--action update-defect`
- `--action create-comment`
- `--action read-comment`
- `--action add-attachment`
- `--action list-attachments`
- `--action delete-attachment`
- `--action list-tasks`
- `--action add-task`
- `--action add-tag`
- `--parse-only`

If needed, validate command availability with:

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" --help
```

Do not inspect Python source to discover hidden commands unless the user asks
for code-level debugging.

## Favorite links

From the plugin root (`plugins/octane`):

```bash
uv run skills/alm-octane/scripts/octane_url.py --parse-only 'https://octane.example.com/ui/favorites/42?p=1001/1003'
uv run skills/alm-octane/scripts/octane_url.py --profile default --action get-favorite 'https://octane.example.com/ui/favorites/42?p=1001/1003'
uv run skills/alm-octane/scripts/octane_url.py --profile default --fields id,name,subtype,phase --page-size 100 --max-items 10000 'https://octane.example.com/ui/favorites/42?p=1001/1003'
# Equivalent direct commands (no endpoint fallback; uses the selected profile):
uv run skills/alm-octane/scripts/octane_client.py --profile default get-favorite --entity-id 42 --shared-space-id 1001 --workspace-id 1003
uv run skills/alm-octane/scripts/octane_client.py --profile default list-favorite-items --entity-id 42 --shared-space-id 1001 --workspace-id 1003
```

**Contract and evidence.** `get-favorite` uses the captured internal UI request
`GET .../favorites?fields=id,name,params,state_name,module_root_state&query="(id='42')"`.
It does not require favorites to appear in entity metadata and does not guess a
single-resource endpoint. It returns one definition in `data`; this alone does
**not** list matching work items. This route and the UI JSON format were observed
in a user-provided UI 27.1.8.47 capture, not guaranteed by public API documentation.
Only synthetic fixtures are committed; never commit a HAR, browser cookies,
XSRF headers, tokens, or real item bodies. No new runtime dependencies.

**Supported adapter.** `list-favorite-items` currently accepts only state
`platform-tree-module-release-quality-details-feature-grid` with a `filter` AST
of `IN(PROPERTY release, LITERAL release-reference...)` and a `navFilter` of
`{"feature":{"product_entity_udf":{"<numeric-id>":"i",...}}}`. Both are applied:

```text
(product_entity_udf EQ {id IN 21,22};subtype EQ ^feature^);(release EQ {id IN 11})
```

Neutral search/content/shared/tree constraints must match the captured shape;
`includeChildren` must be the string `"true"` and
`ap_includeFeaturesNotDirectlyInContextFilter` must be false. Unknown scope keys,
other states, other operators/fields, exclusions, text search, and user-relative
IDs are rejected rather than silently broadening results. Presentation settings
are ignored. In this state `selectedEntities` selects a tree/detail item; the
captured grid request does not constrain membership to it. “All items” means the
matching feature grid, **not** every story/defect beneath those features. Other
favorite formats need their own verified adapter and tests.

The resolver validates filter fields against live workspace metadata and pages
`work_items` using public query syntax, stable `id` sorting, and `limit`/`offset`.
This reproduces membership, not display rank/order or grid layout. `--fields`
accepts flat comma-separated fields (defaults `id,name,subtype,phase,owner`); `id`
is always included. `--page-size` defaults to 100 and `--max-items` to 10000.
Output includes `favorite`, `resolution` (query, adapter, warnings), `data`,
`total_count`, `pages_read`, and `complete`. Success requires `ok: true` **and**
`complete: true`. Duplicate IDs, changing totals, capped totals, premature empty
pages, page errors, or the item safety cap yield nonzero exit and never complete
success; page-stage failures retain the partial `data`. Paging is not a
transactional snapshot: concurrent changes can still require a rerun even when
totals remain unchanged.

**Authorization limitation.** A favorite accessible in a human browser may be
private or unavailable to API clients. An empty collection means inaccessible or
not found, not zero matching items. Stop on 401/403; do not switch credentials,
impersonate the UI via `HPECLIENTTYPE`, reuse browser authentication, or replay the
UI `POST .../favorites/<id>/touch`. In the capture-backed pilot the configured API
identity returned 403 for the favorites collection; live end-to-end access is
**not verified**. Offline replay resolved all 37 captured IDs using four simulated
pages, which verifies parsing/paging, not live API permission or server acceptance
of the generated query. An administrator/authorized API identity is needed for
that remaining check.

Sources for the public collection/query mechanics and known favorite caveats:
- [Octane query syntax](https://admhelp.microfocus.com/octane/en/26.3/Online/Content/API/query_Clause.htm)
- [Collections](https://admhelp.microfocus.com/octane/en/26.3/Online/Content/API/Collections.htm)
- [OpenText Connect restrictions on named filters](https://admhelp.microfocus.com/documents/connect/readmes/24.4/mfcConnectorOctane_ReadMe.html)
  describes unsupported `navFilter` terms and identity-dependent ME/current_user.

## URL Handling

When the user provides an Octane UI URL, use `octane_url.py --parse-only` first.
Remember `base_url`, `shared_space_id`, `workspace_id`, `entity_type`, and
`entity_id`. Pass URL-derived `--shared-space-id` and `--workspace-id`
explicitly on later `octane_client.py` commands whenever supported.

Decision order:

1. UI URL given → start with `octane_url.py`.
2. URL `entityType=work_item` with no explicit action → fetch with `get-work-item`; do not assume defect/story subtype.
3. Plain entity ID given → call `octane_client.py` directly.
4. Any write action or comment post → require explicit user intent.

URL format:

```text
https://<host>/ui/entity-navigation?p=<shared_space_id>/<workspace_id>&entityType=<type>&id=<entity_id>
```

## Rules and Gotchas

All backlog updates (defect/story/feature/test) resolve every payload field from
live metadata for the target workspace and entity before attempting PUT. Exact
API names take precedence over normalized labels/logical names. An absent or
ambiguous mapping, an explicitly read-only field, or unavailable/incomplete metadata blocks
the entire update. Custom-field overrides still require metadata confirmation.
Unknown editability flags do not imply permission; Octane remains authoritative
for permissions and workflow restrictions. Updates read back the resolved API
fields and require `verification.matched: true`; failures are not replayed.

1. All entity-specific commands use the uniform `--entity-id <ID>` flag. Do not use command-specific ID flags.
2. Use `--text`, never `--comment`, for `create-comment`.
3. `--entity-type` for comments must match the Octane type string, e.g. `defect` or `story`.
4. Octane comment `text` is stored/rendered as HTML (`<html><body>...<p>...</p>...</body></html>`). The CLI formats plain `--text` into Octane-compatible HTML automatically; pass already wrapped HTML only when you intentionally need custom markup.
5. Use `read-comment --entity-id <ID>` to read comment content from a backlog/work item.
6. Use `add-attachment --entity-id <ID> --file <PATH> [--description <TEXT>] [--name <NAME>]` to upload a file attachment to a feature/backlog/work item. The default attachment owner is `owner_work_item` with owner type `work_item`, which covers features, stories, defects, and generic backlog items. Use `list-attachments --entity-id <ID>` to verify. Use `delete-attachment --entity-id <ID> --attachment-id <ATTACHMENT_ID>` to delete one attachment from a backlog/work item after explicit user confirmation; alternatively use `--attachment-name <EXACT_NAME>` when the name is unique. With a backlog UI URL, use `octane_url.py --action delete-attachment --attachment-id <ATTACHMENT_ID> <URL>` or `--attachment-name <EXACT_NAME>`. Use `download-attachment --attachment-id <ATTACHMENT_ID> --output-file <PATH>` to fetch attachment content for local analysis. For non-work-item entities, override `--owner-field` and `--owner-type` (for example `owner_test` / `test`).
7. Retry `list-work-items` once with `--retry-on-empty` if the first result is empty.
8. Use `get-work-item` for generic work-item URLs; switch to subtype-specific commands only when the subtype is known.
9. Use `create-feature --name <TEXT> --description <TEXT>` to create a feature. Optionally pass `--parent-id <WORK_ITEM_ID>` and `--owner-id <WORKSPACE_USER_ID>`. Verify with `get-feature --entity-id <FEATURE_ID>`.
10. Use `update-feature --entity-id <FEATURE_ID> --name <TEXT> --description <TEXT>` to update a feature's backlog-ready title/description. With a feature UI URL, use `octane_url.py --action update-feature --name ... --description ... <URL>`. Verify with `get-feature`.
11. Use `create-story-under-feature --entity-id <FEATURE_ID> --name <TEXT> --description <TEXT> --acceptance-criteria <TEXT>` to create a story under a feature. Repeat `--acceptance-criteria` for multiple criteria. The tool stores criteria in the description and, when available, in Octane's `acceptance_criteria` field.
12. Use `update-story --entity-id <STORY_ID> --description <TEXT> --acceptance-criteria <TEXT>` to update a story's description and acceptance criteria. Repeat `--acceptance-criteria` for multiple criteria. If only criteria are supplied, the tool preserves the current description and replaces the rendered Acceptance Criteria section. The separate criteria field must resolve in live metadata and match read-back; unlike the creation command's legacy fallback, updates never retry without the field.
13. Use `get-story-parent-feature --entity-id <STORY_ID>` to identify a story's parent feature.
14. Use `list-feature-items --entity-id <FEATURE_ID>` to list stories and issue/defect work items under a feature. With a feature UI URL, use `octane_url.py --action list-feature-items <URL>`.
15. Use `update-feature-security --entity-id <FEATURE_ID> --security-assessment <TEXT> --security-impact-level <VALUE_OR_LIST_NODE_ID>` to read a feature and update the threat-modelling fields `Security Assessment` and `Security Impact`. With a feature UI URL, use `octane_url.py --action update-feature-security --security-assessment ... --security-impact-level ... <URL>`. The Security Assessment field logical name is `security_assessment_udf`; the Security Impact field logical name is `security_impact_f_udf` (not `security_impact_level`). The command also resolves field logical names from Octane metadata. If your workspace uses nonstandard custom field names, set `OCTANE_SECURITY_ASSESSMENT_FIELD` and/or `OCTANE_SECURITY_IMPACT_LEVEL_FIELD` in `.env`. For `Security Impact`, prefer the exact `list_node...` ID when known.
16. Use `list-tasks --entity-id <ID>` to list tasks for a work item.
17. Use `add-task --entity-id <ID> --name <TEXT> --owner-id <USER_ID>` to add a task; override `--item-type` and `--phase` only when needed.
18. Use `list-tags --query <TEXT>` to search workspace user tags. Use `add-tag --entity-id <ID> --tag <TEXT>` to add a tag to a backlog/work item; the tool creates the workspace tag when missing unless `--no-create` is supplied, preserves existing tags, and verifies the update.
19. Use `delete-backlog-item --entity-id <ID> [--entity-type work_items]` to delete a backlog/work item, including a story under a feature. With a UI URL, use `octane_url.py --action delete-backlog-item <URL>`. This is destructive: require explicit user confirmation immediately before running it. The command must update the mandatory **Allow Delete?** field before deletion; metadata in this workspace resolves **Allow Delete?** / `Allow delete` to the boolean field logical name `allow_delete_udf`. The command resolves the field dynamically, always PUTs it to `true`, verifies it when possible, and only then sends `DELETE`.
20. Use `create-defect --parent-feature-id <FEATURE_ID>` when the defect must be created under a feature. Fetch the feature with `get-feature --fields id,name,owner,release`. Use the returned owner and release IDs when required. Pass description content with `--description`; the tool converts Markdown/plain text to Octane HTML. For security defects, use metadata to resolve the Security Source field and its allowed values. Supply CVSS data with `--cvss-score <SCORE> --cvss-vector <VECTOR>` when applicable. Use project-specific tags, for example `add-tag --entity-id <DEFECT_ID> --tag "SecurityReview"`. Do not reuse field or list-node IDs from another workspace. CVSS field names are resolved from metadata or environment overrides `OCTANE_CVSS_SCORE_FIELD` and `OCTANE_CVSS_VECTOR_FIELD`.
21. Verify entity IDs with `search-all`; do not assume sequential IDs.
22. Severity and priority values use list node IDs, for example `list_node.severity.high`. Resolve allowed names and IDs from the current workspace metadata. Security Source is also a list-node reference; pass an exact allowed name or an ID verified in that workspace.
23. Phase values should use phase IDs, e.g. `phase.defect.fixed`, `phase.story.inprogress`. The CLI also normalizes common shorthands (`fixed`, `opened`, `in progress`) to phase IDs. If a phase update fails, run `list-phases --entity defect` and check whether the workflow requires an intermediate transition.
24. `update-defect` fetches and sends `client_lock_stamp`, updates the entity, and returns a `verified` snapshot when verification succeeds.
25. If a relevant tool is unsupported, do not guess. Say: `No relevant Octane tool found for this request.` Then list supported commands.
26. After write operations, verify with the corresponding read command when possible.

## Common Errors

Credential errors are machine-readable and secret-safe. Stop API work rather than trying another host or credential.

| Symptom / code | Safe recovery |
|---|---|
| Missing or invalid profile metadata | Run `octane_token.py profiles`; select an existing profile or run login again. Do not hand-edit invalid JSON. |
| `OCTANE_KEYRING_ENTRY_MISSING` | Re-run login for the selected profile/keyring username. |
| `OCTANE_KEYRING_BACKEND_FAILURE` | Unlock or configure the OS credential backend, then retry; do not fall back to plaintext. |
| `OCTANE_REMOTE_AUTHENTICATION_FAILED` / HTTP 401 | Verify profile, client ID, and secret rotation; run login again. |
| `OCTANE_REMOTE_AUTHORIZATION_FAILED` / HTTP 403 | Request access to the selected shared space/workspace; changing the secret is not the normal fix. |
| Credential source mismatch | Remove partial environment overrides or provide one complete coherent direct/keyring-backed set. |
| Legacy migration conflict | Reconcile the reported non-secret candidate fields/paths and retry; source files were not modified. |
| Login rollback incomplete | Stop and inspect profile metadata and keyring selection separately; restore the affected side before retrying and never print the secret. |
| Workspace accessibility error | Verify the selected profile or propagate URL-derived shared-space/workspace IDs. |
| Entity not found | Search first with `search-all`. |
| Empty work-items response | Retry with `--retry-on-empty`. |
| Timeout | Increase the profile/direct `OCTANE_TIMEOUT` or check network connectivity. |
| Phase update rejected | Run `list-phases --entity defect`; use the returned phase ID and follow the configured workflow transition path. |

## References Loaded On Demand

- Examples and workflows: `"$SKILL_ROOT/references/examples.md"`
- Script help: `uv run "$SKILL_ROOT/scripts/octane_client.py" --help`
