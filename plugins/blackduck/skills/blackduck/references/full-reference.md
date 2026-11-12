# Black Duck Vulnerability Management Skill

Use this skill only for Black Duck security finding and vulnerability triage
work. Keep context small: do not read references or Python source unless needed
for debugging inconsistent CLI behavior.

## Resolve the Skill Root

This is a user-level skill. Do not look for its scripts, references, or `.env`
in the current project. Resolve `SKILL_ROOT` before every command, preferring
the installed Black Duck plugin root over direct user skill directories:

```bash
for d in "$HOME"/.copilot/installed-plugins/*/blackduck/skills/blackduck "$HOME/.copilot/skills/blackduck" "$HOME/.agents/skills/blackduck"; do
  if [ -f "$d/SKILL.md" ]; then SKILL_ROOT="$d"; break; fi
done
[ -n "$SKILL_ROOT" ] || { echo "Black Duck skill not found in installed plugin or user skill directories"; exit 1; }
```

Invoke the CLI by absolute path:

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" <tool> [args]
```

JSON is written to stdout. Diagnostics are written to stderr.

## Credential Profiles and Configuration

Preferred authentication uses a named profile. The token is stored in OS keyring service `AgentDevelopmentToolkit:blackduck`; stable `blackduck.json` stores only URL, keyring username, and `verify_ssl`.

| Platform | Default `blackduck.json` directory |
|---|---|
| Windows | `%APPDATA%\AgentDevelopmentToolkit` |
| macOS | `~/Library/Application Support/AgentDevelopmentToolkit` |
| Linux | `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit` |

`AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` overrides the directory. Runtime precedence is `blackduck_vulnerabilities.py --profile <name>`, then `BLACKDUCK_PROFILE`, then the active profile.

Inject `BLACKDUCK_LOGIN_TOKEN` with a masked launcher environment without putting its value in command text:

```bash
uv run "$SKILL_ROOT/scripts/blackduck_token.py" login \
  --profile default --url "https://blackduck.example.com" \
  --user "https://blackduck.example.com" --verify-ssl true
uv run "$SKILL_ROOT/scripts/blackduck_token.py" profiles
uv run "$SKILL_ROOT/scripts/blackduck_token.py" use-profile --profile default
uv run "$SKILL_ROOT/scripts/blackduck_token.py" delete-profile --profile default
```

`defaults` provides new-profile fallback values, not a view of an existing profile. Explicitly pass URL and SSL behavior when updating. `--no-activate` saves without changing the active profile. Deletion removes metadata only, never keyring tokens. Login verifies the named profile unless `--skip-test` is supplied. Rollback after failure is best-effort; verify metadata and keyring selection separately before retrying.

### SSL safety and provenance

`verify_ssl` persists per profile after relocation. Keep it `true` for trusted certificates. Set it `false` only after explicit acceptance for a known private/self-signed certificate environment. Process-level partial URL/token/keyring-user overrides are rejected when a profile is selected, and legacy `.env` credentials do not override that profile.

For CI, provide complete `BLACKDUCK_URL` and `BLACKDUCK_TOKEN`; `BLACKDUCK_VERIFY_SSL` is optional and defaults to `true`. A direct token is never stored in profile metadata or migrated.

| Variable | Purpose |
|---|---|
| `BLACKDUCK_PROFILE` | Named profile when API `--profile` is absent |
| `BLACKDUCK_URL` | URL for a complete direct/keyring-backed override |
| `BLACKDUCK_TOKEN_KEYRING_USER` | Keyring username paired with explicit URL |
| `BLACKDUCK_TOKEN` | Direct CI token paired with explicit URL |
| `BLACKDUCK_VERIFY_SSL` | `true`/`false` (also `1`/`0` or `yes`/`no`); defaults to `true`; any other value fails before keyring or network access |

### Legacy migration

With no stable document, startup checks the executing skill root, `~/.copilot/skills/blackduck`, and `~/.agents/skills/blackduck`. One unambiguous usable keyring-backed candidate migrates to `default`; aliases are deduplicated. Only non-secret metadata is persisted and sources stay byte-for-byte unchanged. Conflicts and unusable keyring entries fail before HTTP. A direct-token `.env` in the executing root remains a fallback and is never migrated; direct-token files found only in other discovery roots are not loaded. Help skips migration.

## Supported Tools Only

| Tool | Purpose |
|---|---|
| `list-remediation-values` | List documented remediation status, status justification, and remediation option values. |
| `list-projects` | List/search projects. |
| `list-versions` | List/search versions for a project. |
| `list-licenses` | List/search available Black Duck licenses by name before choosing a license for component updates. |
| `list-components` | List BOM components for a project version with `--query`/`--name`, `--exact`, `--filter`, `--review-status`, `--license-risk`, `--operational-risk`, `--security-risk`, `--policy-status`, and `--all` support. |
| `list-vulnerabilities` | List vulnerabilities with `--severity`, `--status`, `--component`, `--query`, `--filter`, and `--limit` support. |
| `get-vulnerability-details` | Get details for a vulnerability and affected components. |
| `get-code-location` | Given a component name/id, get code-location evidence for a project version (fully paginated, with detection notes). |
| `get-matched-files` | Given a component name/id, get matched file paths/URIs. Fully paginated via all origin-level endpoints; returns a `note` field explaining why results are empty for manifest-detected components. |
| `get-dependency-paths` | Given a component name/id, get the dependency-graph resolution path (DIRECT vs TRANSITIVE) for package-manager-detected components. Requires Black Duck 2021.2+ and a Detect scan with dependency resolution. Returns empty list with an explanatory `note` on older instances or non-manifest-detected components. |
| `update-component` | Update a BOM component's review status, component license, and/or component usage. |
| `update-vulnerability` | Update vulnerability remediation status with optional justification. Does not update comments. |
| `comment-vulnerability` | Update vulnerability remediation comment only. |

`list-vulnerablities` is accepted as a backward-compatible alias for the common
misspelling of `list-vulnerabilities`.

## Common Usage

```bash
# Add --profile <name> before the tool when explicit selection is required.
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-remediation-values
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-projects --query "MyApp" --limit 25
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-versions --project "MyApp" --query "1.0"
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-licenses --query "Apache" --limit 25
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-components --project "MyApp" --version "1.0" --query "openssl" --limit 25
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-components --project "MyApp" --version "1.0" --name "openssl" --review-status REVIEWED --license-risk HIGH --operational-risk LOW --security-risk HIGH --all
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-vulnerabilities --project "MyApp" --version "1.0" --severity HIGH --status NEW
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-vulnerability-details --project "MyApp" --version "1.0" --vuln-id "BDSA-2024-0001" --related-id "CVE-2024-0001"
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-code-location --project "MyApp" --version "1.0" --component "openssl" --exact
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-matched-files --project "MyApp" --version "1.0" --component "openssl" --exact
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-dependency-paths --project "MyApp" --version "1.0" --component "openssl" --exact
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" update-component --project "MyApp" --version "1.0" --component "openssl" --exact --review-status REVIEWED --license "Apache-2.0" --usage DYNAMICALLY_LINKED
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" update-component --project "MyApp" --version "1.0" --component "openssl" --exact --comment "No matching license found; leave license unchanged."
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" update-vulnerability --project "MyApp" --version "1.0" --vuln-id "CVE-2023-44487" --status PATCHED
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" update-vulnerability --project "MyApp" --version "1.0" --vuln-id "CVE-2023-44487" --status NOT_AFFECTED --justification VULNERABLE_CODE_NOT_PRESENT
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" update-vulnerability --project "MyApp" --version "1.0" --vuln-id "CVE-2023-44487" --status AFFECTED --remediation VENDOR_FIX
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" comment-vulnerability --project "MyApp" --version "1.0" --vuln-id "CVE-2023-44487" --comment "Upgraded dependency"
```

## Rules and Gotchas

1. Discover the exact project and version before listing or updating vulnerabilities.
2. Use `get-vulnerability-details` before `update-vulnerability` unless exact CVE/BDSA and component context are already provided.
3. Do not update remediation status or comments unless the user explicitly asks for a write action.
4. Keep status/justification updates separate from comment updates: use `update-vulnerability` for status/justification and `comment-vulnerability` for comments.
5. After `update-component`, verify with `list-components`; after `update-vulnerability` or `comment-vulnerability`, verify with `get-vulnerability-details` or `list-vulnerabilities`.
6. Parse stdout as JSON; use stderr only for diagnostics.
7. Use `get-code-location` for scan/code-location context and `get-matched-files` for component file-path evidence when available.
8. When `get-matched-files` returns `totalMatchedFiles=0`, read the `note` field before concluding there are no code paths. For `FILE_DEPENDENCY_*` match types (manifest-based detection), `totalFileMatchCount > 0` counts manifest-file occurrences, not binary/source matches — use `get-dependency-paths` instead to see the dependency-graph resolution chain.
9. `get-dependency-paths` returns empty `dependencyPaths` (not an error) when the endpoint is unsupported (pre-2021.2 instances, binary/signature scans, or Detect ran without dependency resolution). Read the `note` field for the reason.
10. Both `get-matched-files` and `get-dependency-paths` expose `matchTypes` and `totalFileMatchCount` on each component result to help understand how the component was detected.

## Credential Troubleshooting

Stop rather than trying another host, disabling TLS casually, or exposing a token.

| Symptom / code | Safe recovery |
|---|---|
| `BLACKDUCK_PROFILE_METADATA_MISSING` | For profiles, run `blackduck_token.py profiles` and log in/select as needed. For direct credentials, complete matching URL/token values or remove the incomplete override. |
| Invalid durable profile | Profile commands cannot read malformed JSON. Back up reported `blackduck.json` securely, move it aside, and recreate profiles through login without copying unknown/secret fields. |
| `BLACKDUCK_KEYRING_ENTRY_MISSING` | Re-run login for the selected profile/keyring username. |
| `BLACKDUCK_KEYRING_BACKEND_FAILURE` | Unlock/configure the OS credential backend; do not switch to plaintext. |
| `BLACKDUCK_CREDENTIAL_SOURCE_MISMATCH` | Remove partial overrides or provide complete matching URL/token or URL/keyring-user values. |
| `BLACKDUCK_REMOTE_AUTHENTICATION_FAILED` / HTTP 401 | Verify selected URL and token rotation, then log in again. |
| `BLACKDUCK_REMOTE_AUTHORIZATION_FAILED` / HTTP 403 | Request access on the selected instance; do not silently change hosts. |
| `BLACKDUCK_REMOTE_AUTHENTICATION_REQUEST_FAILED` | Inspect the non-401/403 authentication status and network/proxy behavior without changing credential source. |
| TLS verification error | Confirm endpoint and CA trust. Disable verification only with explicit risk acceptance. |
| Legacy migration conflict | Reconcile reported non-secret candidate paths/fields; source files were not changed. |
| Login failure after a mutation | Rollback is best-effort. Inspect profile metadata and keyring selection separately before retrying; never print the token. |

Coded credential errors are JSON. Authentication response filtering omits only a small set of exact credential-key names; embedded or differently named secrets may remain. Treat all output and server-provided content as sensitive. Token-helper diagnostics use stderr.

## References Loaded On Demand

- Examples and workflows: `"$SKILL_ROOT/references/examples.md"`
- API endpoint details: `"$SKILL_ROOT/references/api_notes.md"`
- Script help: `uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" --help`
