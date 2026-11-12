---
name: "alm-octane"
disable-model-invocation: true
description: "ALM Octane CLI for generic entity/field discovery, filters, paged reads, verified JSON writes, work-item workflows, tests, comments, attachments, tags, and URL parsing."
compatibility: >
  Requires uv (https://docs.astral.sh/uv/) installed and on PATH.
  Requires Python 3.10+. Requires network access to the Octane instance.
---

# ALM Octane CLI

Use this skill to read or write ALM Octane through the bundled Python CLI.

## Steps

0. Resolve the skill root and environment.
   - Resolve the Octane skill root in this order: `plugins/octane/skills/alm-octane` in this repository, an installed plugin at `~/.copilot/installed-plugins/*/octane/skills/alm-octane`, then direct user skill roots.
   - Do not perform login, credential setup, keyring reads, or credential preflight in this skill. A plugin-local `.env` is not required: normal authentication uses an OS-keyring secret selected by stable per-user profile metadata. Metadata is `%APPDATA%\AgentDevelopmentToolkit\octane.json` on Windows, `~/Library/Application Support/AgentDevelopmentToolkit/octane.json` on macOS, and `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit/octane.json` on Linux; `AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` overrides the directory.
   - Select a named profile with API `--profile <name>` when the user identifies one. Otherwise selection is `OCTANE_PROFILE`, then the active profile. Never invent an endpoint fallback or combine a partial endpoint/credential override with profile credentials.
   - If the CLI reports missing/invalid authentication, stop tool work and direct the user/agent to `octane-login`. Login should read defaults with `uv run scripts/octane_token.py defaults`, show those defaults while asking questions, require client ID and secret every time, inject `OCTANE_LOGIN_SECRET` through the tool launcher's masked environment without putting its value in command text, and run:
     ```bash
     uv run scripts/octane_token.py login --profile "<name>" --base-url "<url>" --user "<client-id>" --shared-space-id "<id>" --workspace-id "<id>"
     ```
   - Load `references/full-reference.md` only when you need profile lifecycle, configuration locations, command syntax, field names, URL parsing, or troubleshooting.
   - Load `references/threat-model-defect-description-format.md` when constructing or validating threat-model defect descriptions.
   - Completion criterion: script paths and command syntax are known.

1. Choose the smallest CLI command.
   - Prefer read commands before writes.
   - Use `get-entity-types` to discover workspace entity types and REST collections; use `get-entity-field-metadata --entity-type <type>` for actual field definitions.
   - Use `get-filter-metadata --entity-type <type>` before constructing native filters; distinguish documented grammar from live workspace field capabilities.
   - Use `get-entities --entity-type <type>` for one page; pass native `--query` without outer quotes, or `--search` on `work_items` only. Specify fields/limit/offset to keep reads small; search requires server support.
   - For a known collection without a convenience command, use `get-entity --entity-type <collection> --entity-id <id> [--fields id,name]`; see the full reference for generic command contracts.
   - Before every backlog update (defect, story, feature, or test), resolve all requested fields against live metadata for the target workspace/entity. Exact API names take precedence; otherwise normalized labels/logical names must match uniquely. Missing, ambiguous, or explicitly read-only fields block the entire update. Overrides and naming conventions are not proof that a field exists. The CLI enforces this for generic and convenience updates, including status, security, tag, and Allow Delete field changes; metadata/auth failures must not be bypassed.
   - Generic writes use `create-entity --entity-type <type> --data-file <path>` or `update-entity --entity-type <type> --entity-id <id> --data-file <path>` after explicit user intent. Supply a field object using discovered metadata; prefer convenience commands for Markdown/phase/tag transformations. Inspect mutation and verification evidence before reporting success or retrying.
   - Parse Octane URLs with `scripts/octane_url.py` before calling entity commands. Favorite URLs (`/ui/favorites/<id>?p=<space>/<workspace>`) default to read-only `list-favorite-items`; use `--action get-favorite` to inspect their definitions. Direct commands take `--entity-id <favorite-id>` and explicit tenant IDs. `list-favorite-items` supports `--fields`, `--page-size` (default 100), and `--max-items` (default 10000); it returns `data`, `total_count`, `resolution`, and `complete`. Require `ok: true` and `complete: true` before claiming all items were read.
   - Favorites use an internal UI collection API, not a documented public favorite-expansion endpoint. Only the captured release-quality feature-grid format is supported (release-IN references plus product navigation inclusions). Read [favorite limitations and examples](references/full-reference.md#favorite-links) before using it. Unknown states/filters/search/tree constraints fail closed. Never ignore `navFilter`, infer item membership from `selectedEntities`, replay the UI `touch` POST, or copy browser cookies/headers to work around authorization. A browser-visible favorite may be inaccessible to the API identity; stop on 401/403.
   - Completion criterion: command, entity ID/type, fields, and workspace/shared-space IDs are explicit.

2. Execute and verify.
   - Run `uv run scripts/octane_client.py [--profile <name>] ...`.
   - Generic writes perform read-back internally. Require `ok: true` and `verification.matched: true` before reporting success. `mutation.outcome: succeeded` with failed verification means the write may have succeeded, not that requested state is confirmed; an `unknown` outcome requires inspection, never blind replay.
   - Backlog updates also compare all resolved field values through internal read-back. Required acceptance criteria must update the actual mapped field; `update-story` never drops it and retries with description-only content. After convenience writes, verify with the matching read command. Generic writes never automatically retry mutations or remediate workflow restrictions.
   - Completion criterion: JSON output is parsed and the requested Octane state is confirmed or an error is reported; on credential/authorization failures stop tool work rather than switching hosts/profiles.
