# Octane Agent Toolkit

## Context loading

Start with [using-octane](skills/using-octane/SKILL.md). Only the router allows automatic skill selection. Supporting skills set `disable-model-invocation: true`; direct user commands remain available. The router reads the selected skill file explicitly. Agents load their own instructions when invoked. Do not preload the whole plugin.

Copilot controls discovery metadata and system context. These rules do not guarantee a fixed token count or force the router to load at startup. Enable only the plugins needed for the task. Test loading in a fresh host session after updating.

This plugin provides ALM Octane workflow agents, commands, and CLI skills for work-item lookup, triage, analysis, planning, updates, and delivery evidence.

## Contents

- `skills/alm-octane/` — profile-aware Octane CLI and URL parser, including generic discovery, paged reads, and verified JSON writes; see [CLI reference](skills/alm-octane/references/full-reference.md#generic-commands).
- `agents/octane-agent.agent.md` — orchestrator for multi-step Octane workflows.
- `agents/oct-*.agent.md` — triage, research, planning, and implementation subagents.
- `commands/*.md` — login and workflow commands.

## Quick start

```text
/octane-login
/octane-triage <octane-url-or-id>
/octane-analyse <octane-url-or-id>
/octane-fix <octane-url-or-id>
```

The `/octane-fix` workflow researches and plans first, then implements only after its approval gates.

### Your first Octane task

1. Run `/octane-login` once to connect an Octane account.
2. Copy an Octane work-item URL (or its ID) from your browser.
3. Start with `/octane-triage <url-or-id>` to understand the item before requesting changes.

Use `/octane-analyse` when you need evidence and a recommendation. Use `/octane-fix` only when you are ready to review the plan and approve implementation. The plugin keeps reads safe by default and asks before workflow-driven updates.

## Generic entity CLI

The CLI provides **41 commands**: seven generic commands, two read-only favorite
commands, and the existing 32 workflow conveniences. It calls Octane REST directly; no MCP service or new
runtime dependency is required. Existing deletion/attachment operations remain
separate; there is no new generic deletion command.

| Purpose | Command |
|---|---|
| Discover entity types/REST collections | `get-entity-types` |
| Inspect exact field definitions | `get-entity-field-metadata` |
| Read cited grammar and live field capabilities | `get-filter-metadata` |
| Retrieve one filtered/sorted page | `get-entities` |
| Retrieve one entity | `get-entity` |
| Create one JSON record and verify it | `create-entity` |
| Partially update one record and verify it | `update-entity` |

From `plugins/octane`, after configuring a profile:

```bash
uv run skills/alm-octane/scripts/octane_client.py --help
uv run skills/alm-octane/scripts/octane_client.py --profile staging get-entity-types
uv run skills/alm-octane/scripts/octane_client.py --profile staging get-entity-field-metadata --entity-type defects
uv run skills/alm-octane/scripts/octane_client.py --profile staging get-filter-metadata --entity-type defects
uv run skills/alm-octane/scripts/octane_client.py --profile staging get-entities --entity-type defects --query 'id EQ 1234' --fields id,name --order-by=-id --limit 20 --offset 0
```

IDs/profile names above are examples, not valid deployment defaults. Pass optional
`--shared-space-id`/`--workspace-id` to target an explicitly identified workspace.
Native `--query` has no outer double quotes; `--search` is a separate,
mutually-exclusive keyword mode limited to `work_items` and requiring server
`text_search` support. Paging defaults to 50/0 and sort `id`; only one page is read.
Filter grammar is bundled, cited Octane 26.1 documentation—not server-discovered
operators—and is labeled separately from live workspace field metadata.

Generic writes require pre-authorized user intent and `--data-file` containing
one JSON field object. They preserve values/relationships without convenience
transformations. Inspect both `mutation` and `verification`: a write can succeed
but fail verification, producing a nonzero exit. Never replay an uncertain write
blindly. Update lock stamps preserve caller intent or are fetched when supported.
Every backlog update (defect/story/feature/test), including convenience commands,
resolves each requested field against live workspace/entity metadata before PUT.
Exact API names win; normalized labels/logical names must resolve uniquely.
Missing, ambiguous, or explicitly read-only fields block the whole update.
Metadata failure or a response advertised as incomplete also blocks writes
(field discovery requests up to 5,000 definitions). Unknown capability flags are not permission
checks, so Octane still enforces workflow/authorization rules. Required story
acceptance criteria are never dropped in a description-only retry.
Use convenience commands for HTML/Markdown formatting, phase shorthands, tags,
and acceptance criteria. See [payload and outcome examples](skills/alm-octane/references/examples.md#generic-discovery-to-verified-write)
and the [complete command reference](skills/alm-octane/references/full-reference.md#generic-commands).

Offline development verification (from `plugins/octane`):

```bash
uvx --from pytest --with requests --with python-dotenv --with keyring pytest skills/alm-octane/tests -q
```

Field-resolution regressions cover all four backlog types, alias ambiguity,
read-only/missing fields, metadata failures, convenience updates, and verification
mismatches. No new runtime dependencies were added.

Tests use fake HTTP/keyrings; do not run API examples as smoke tests without
explicit workspace permission. Exact MCP schema parity and live-server/version
compatibility are not claimed by offline verification.

## Read items from a favorite link

From `plugins/octane`:

```bash
uv run skills/alm-octane/scripts/octane_url.py --profile default --page-size 100 'https://octane.example.com/ui/favorites/42?p=1001/1003'
```

Favorite URLs now default to `list-favorite-items`. Use `--action get-favorite`
to inspect the saved definition, or call either command directly with
`--entity-id`, `--shared-space-id`, and `--workspace-id`. Reads never touch or
modify the favorite. The resolver combines saved release and product-navigation
filters and fetches all pages; require both `ok: true` and `complete: true`.

**Limited, capture-backed support:** only the release-quality feature-grid
favorite format is currently accepted. Other filters/states fail explicitly, not
as unfiltered reads. The favorite collection is an internal UI API, not a public
favorite-expansion contract. Browser access does not imply API-client access;
the configured API identity returned 403 in the pilot, so live end-to-end support
remains unverified. No browser credentials or UI client impersonation are used.
See [favorite commands, scope, and limitations](skills/alm-octane/references/full-reference.md#favorite-links).

## Durable credential profiles

Login stores the client secret in the operating-system keyring under `AgentDevelopmentToolkit:alm-octane`. It stores only non-secret metadata—endpoint, keyring username, shared space, workspace, and timeout—in `octane.json`:

| Platform | Default metadata path |
|---|---|
| Windows | `%APPDATA%\AgentDevelopmentToolkit\octane.json` |
| macOS | `~/Library/Application Support/AgentDevelopmentToolkit/octane.json` |
| Linux | `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit/octane.json` |

Set `AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` to override the directory on any platform. Profiles remain available after plugin upgrades or relocation because neither metadata nor secrets live in the plugin directory. The generic storage rename requires a fresh login for users of earlier names; old profiles and keyring entries are not read or removed. Supply your endpoint explicitly at login or through a generic profile.

From the skill root, inspect defaults and create the active `default` profile:

```bash
uv run scripts/octane_token.py defaults
# Inject OCTANE_LOGIN_SECRET through the launcher's masked environment; do not
# substitute the secret into this command text.
uv run scripts/octane_token.py login \
  --profile default \
  --base-url "https://octane.example.com" \
  --user "<api-client-id>" \
  --shared-space-id "<shared-space-id>" \
  --workspace-id "<workspace-id>" \
  --timeout 30
```

The script is non-interactive. Supply the secret through a launcher's protected environment facility rather than normal chat or command text. An activating login verifies the effective profile with a minimal API read unless `--skip-test` is explicitly supplied. `--no-activate` preserves the previous active profile, so its automatic read does not prove the newly saved inactive profile; select and test that profile explicitly before relying on it. Login attempts to restore prior metadata and keyring state after a failed write or verification and reports when rollback is incomplete.

### Named profiles

```bash
# Add and activate a profile (with OCTANE_LOGIN_SECRET injected securely)
uv run scripts/octane_token.py login \
  --profile staging --base-url "https://octane-staging.example.com" \
  --user "<api-client-id>" --shared-space-id "<id>" --workspace-id "<id>"

# Add/update without changing the active profile
uv run scripts/octane_token.py login \
  --profile staging --no-activate --base-url "https://octane-staging.example.com" \
  --user "<api-client-id>" --shared-space-id "<id>" --workspace-id "<id>"

uv run scripts/octane_token.py profiles
uv run scripts/octane_token.py use-profile --profile staging
uv run scripts/octane_token.py delete-profile --profile staging
uv run scripts/octane_client.py --profile default list-work-items --limit 1
```

Deleting a profile removes metadata only; it never deletes keyring credentials. Runtime selection is `--profile`, then `OCTANE_PROFILE`, then the active profile.

## Legacy `.env` and CI

On normal client startup, an unambiguous keyring-backed `.env` can be migrated from the executing skill root, `~/.copilot/skills/alm-octane`, or `~/.agents/skills/alm-octane`. Migration persists only non-secret metadata, confirms the selected keyring entry exists, writes one `default` profile, and never rewrites or deletes the source file. Equivalent path aliases are deduplicated. Conflicting candidates or unusable keyring entries fail without mutation.

Credential endpoints must use HTTPS and cannot contain userinfo, query strings, or fragments. Authentication redirects are refused. Direct secrets are never migrated. For CI, provide a complete coherent set of `OCTANE_BASE_URL`, `OCTANE_CLIENT_ID`, and `OCTANE_CLIENT_SECRET` together. Shared-space, workspace, and timeout values are optional and use client defaults when omitted. When a stable profile is selected, partial endpoint or credential overrides are rejected before keyring or network access so a credential cannot be paired with an unrelated host. Never commit `.env`.

## Troubleshooting

| Error class | Safe recovery |
|---|---|
| Missing/invalid profile metadata | Run `octane_token.py profiles`; log in again or select an existing profile. Do not hand-edit malformed JSON. |
| Selected keyring entry missing | Re-run `login` for that profile and keyring username. Metadata deletion does not remove keyring entries. |
| Keyring backend failure | Unlock/configure the platform credential store, then retry. Do not replace it with a plaintext secret. |
| HTTP 401 authentication failure | Verify the selected profile, client ID, and rotated secret; re-run login. |
| HTTP 403 authorization failure | Keep the credential unchanged and request access to the selected shared space/workspace. |
| Legacy migration conflict | Compare the reported non-secret endpoint/tenant/keyring-user fields, remove ambiguity, and retry. Source `.env` files are unchanged. |
| Incomplete rollback | Stop and inspect profile metadata and the selected keyring entry separately; restore or repeat login only after identifying which side changed. Never print the keyring value. |

Client/API errors are machine-readable JSON and do not include client secrets. Token-helper diagnostics are written to stderr.

Agent workflows obtain required write/delete confirmation in the orchestrator. The orchestrator/host conversation is the accepted approval boundary; direct CLI calls are treated as already authorized and intentionally have no model-forgeable confirmation flag. Constrain untrusted automation with scoped credentials, sandboxing, and host tool permissions.

## Install

```bash
copilot plugin marketplace add .
copilot plugin install octane@vnr-agent-development-toolkit
```

Copilot-installed workflows resolve the bundled skill from `~/.copilot/installed-plugins/*/octane/skills/alm-octane` automatically.

For a direct development install:

```bash
copilot plugin install plugins/octane
```

## Relationship to SDLC

Use Octane when work originates in an Octane item or delivery evidence must be linked back to it. The [SDLC plugin](../sdlc/README.md) owns requirements, research, design, implementation plans, logs, and verification reports; Octane owns its work-item state and links.
