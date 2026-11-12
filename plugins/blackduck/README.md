# Black Duck Agent Toolkit

## Context loading

Start with [using-blackduck](skills/using-blackduck/SKILL.md). Only the router allows automatic skill selection. Supporting skills set `disable-model-invocation: true`; direct user commands remain available. The router reads the selected skill file explicitly. Agents load their own instructions when invoked. Do not preload the whole plugin.

Copilot controls discovery metadata and system context. These rules do not guarantee a fixed token count or force the router to load at startup. Enable only the plugins needed for the task. Test loading in a fresh host session after updating.

This plugin provides Black Duck vulnerability, component-review, code-evidence, and explicitly confirmed remediation workflows.

## Commands

- `/blackduck-login`
- `/blackduck:vulnerability-review`
- `/blackduck:vulnerability-analysis`
- `/blackduck:component-review`

```text
/blackduck-login
/blackduck:vulnerability-analysis "My Project" "1.0" --severity HIGH
/blackduck:vulnerability-review "My Project" "1.0" --severity CRITICAL
```

The orchestrator presents proposed Black Duck updates and applies them only after explicit confirmation. The orchestrator/host conversation is the accepted approval boundary; direct CLI calls are treated as already authorized and intentionally have no model-forgeable confirmation flag. For untrusted automation, use read-only/scoped service credentials and host tool restrictions.

### Your first Black Duck review

1. Run `/blackduck-login` once to connect Black Duck.
2. Start with `/blackduck:vulnerability-analysis` for a project version and severity.
3. Use `/blackduck:vulnerability-review` when you want guided triage and a proposed remediation path.

The plugin reads findings first. It shows any proposed Black Duck update and waits for your explicit confirmation before applying it.

## Durable credential profiles

Login stores the API token in OS keyring service `AgentDevelopmentToolkit:blackduck`. Stable `blackduck.json` contains only the Black Duck URL, keyring username, and SSL-verification setting:

| Platform | Default metadata path |
|---|---|
| Windows | `%APPDATA%\AgentDevelopmentToolkit\blackduck.json` |
| macOS | `~/Library/Application Support/AgentDevelopmentToolkit/blackduck.json` |
| Linux | `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit/blackduck.json` |

Set `AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` to override the directory. Profiles survive plugin upgrades and relocation because configuration is outside the plugin. The generic storage rename requires a fresh login for users of earlier names; old profiles and keyring entries are not read or removed. Supply the endpoint explicitly with `--url`, `BLACKDUCK_URL`, or an existing generic profile. There is no default host.

From the skill root, inspect new-profile defaults. When updating an existing profile, explicitly confirm its URL and SSL setting rather than assuming `defaults` represents that profile. Inject `BLACKDUCK_LOGIN_TOKEN` through the launcher's masked environment without putting its value in command text or chat.

```bash
uv run scripts/blackduck_token.py defaults
uv run scripts/blackduck_token.py login \
  --profile default \
  --url "https://blackduck.example.com" \
  --user "https://blackduck.example.com" \
  --verify-ssl true
```

Login verifies the named profile with `list-projects --limit 1` unless `--skip-test` is supplied. Rollback is best-effort rather than guaranteed; after any login failure, verify both profile metadata and keyring selection before retrying.

### Profile lifecycle and selection

```bash
# Save without changing the active profile
uv run scripts/blackduck_token.py login --profile staging --no-activate \
  --url "https://staging-blackduck.example.com" \
  --user "https://staging-blackduck.example.com" \
  --verify-ssl false

uv run scripts/blackduck_token.py profiles
uv run scripts/blackduck_token.py use-profile --profile staging
uv run scripts/blackduck_token.py delete-profile --profile staging
uv run scripts/blackduck_vulnerabilities.py --profile default list-projects --limit 1
```

Runtime selection is API `--profile`, then `BLACKDUCK_PROFILE`, then the active stable profile. Deleting profile metadata never deletes the keyring token.

## SSL verification

`verify_ssl` belongs to each profile and remains effective after plugin replacement. Keep it `true` for normally trusted certificates. Set `--verify-ssl false` only when the user has explicitly accepted the risk for a known self-signed/private CA environment; do not disable verification merely to bypass an unexplained TLS failure.

A selected profile's URL, keyring locator, and SSL policy form one source. Process-level partial `BLACKDUCK_URL`, `BLACKDUCK_TOKEN`, or `BLACKDUCK_TOKEN_KEYRING_USER` overrides are rejected rather than mixed. Legacy `.env` credentials do not override a selected stable profile. This prevents a self-hosted token from being paired with a default or unrelated host.

For CI, supply complete `BLACKDUCK_URL` plus `BLACKDUCK_TOKEN`; `BLACKDUCK_VERIFY_SSL` is optional and defaults to verification enabled. It accepts `true`/`false`, `1`/`0`, or `yes`/`no`; malformed values fail before credential or network access. Never persist the direct token in stable metadata or logs.

## Legacy `.env` migration

When no stable document exists, startup checks the executing skill root, `~/.copilot/skills/blackduck`, and `~/.agents/skills/blackduck`. One unambiguous usable keyring-backed candidate is migrated to `default`. Migration persists only URL, keyring locator, and SSL setting, deduplicates equivalent aliases, and leaves every source byte-for-byte unchanged. Conflicts and unusable keyring entries fail without stable-state or network mutation.

Credential endpoints must use HTTPS and cannot contain userinfo, query strings, or fragments. Authentication redirects are refused. A direct-token `.env` in the executing skill root remains a fallback when no profile is selected and is never migrated. Direct-token files found only in the other migration-discovery roots are not loaded. Help commands skip migration.

## Troubleshooting

| Error class | Safe recovery |
|---|---|
| `BLACKDUCK_PROFILE_METADATA_MISSING` | Run `blackduck_token.py profiles` when using profiles. If using direct environment credentials, either complete matching URL/token values or remove the incomplete override. |
| Invalid profile metadata | Profile commands cannot load malformed JSON. Back up the reported `blackduck.json` securely, move it aside, then recreate profiles with login. Do not copy unknown fields or possible secret material into the replacement. |
| `BLACKDUCK_KEYRING_ENTRY_MISSING` | Re-run login for the selected profile/keyring username. |
| `BLACKDUCK_KEYRING_BACKEND_FAILURE` | Unlock/configure the OS credential backend; do not switch to plaintext. |
| `BLACKDUCK_CREDENTIAL_SOURCE_MISMATCH` | Remove partial overrides or provide a complete matching URL/token or URL/keyring-user source. |
| `BLACKDUCK_REMOTE_AUTHENTICATION_FAILED` / HTTP 401 | Verify selected URL and token rotation, then log in again. |
| `BLACKDUCK_REMOTE_AUTHORIZATION_FAILED` / HTTP 403 | Request authorization on the selected instance; do not silently change hosts. |
| `BLACKDUCK_REMOTE_AUTHENTICATION_REQUEST_FAILED` | Inspect the non-401/403 authentication status and network/proxy behavior without changing credential source. |
| TLS verification failure | Confirm URL and CA trust. Change `verify_ssl` only with explicit acceptance of the security impact. |
| Legacy migration conflict | Reconcile reported non-secret paths/fields and retry; sources were not modified. |
| Login failure after a mutation | Rollback is best-effort. Stop and inspect profile metadata and keyring selection separately before retrying; never print the token. |

Coded credential failures use JSON. Authentication response filtering removes only a small set of exact credential-key names; secrets embedded elsewhere may remain. Treat output and all server-provided response bodies as sensitive and do not share them blindly. Token-helper diagnostics use stderr.

## Install

```bash
copilot plugin marketplace add .
copilot plugin install blackduck@vnr-agent-development-toolkit
```

For a direct development install:

```bash
copilot plugin install plugins/blackduck
```

## Relationship to SDLC

Use Black Duck for dependency, component, CVE/BDSA, and remediation evidence. The [SDLC plugin](../sdlc/README.md) owns lifecycle artifacts; reference Black Duck findings from research, design, implementation, and verification records.
