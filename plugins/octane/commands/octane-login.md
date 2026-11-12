---
name: octane-login
description: >
  Configure durable ALM Octane credential profiles in the OS keyring and
  stable per-user metadata, then verify access with the Octane CLI.
argument-hint: "[profile]"
---

# Octane Login

Resolve the installed `alm-octane` skill root, then read non-secret defaults:

```bash
uv run scripts/octane_token.py defaults
```

Collect base URL, shared-space ID, workspace ID, timeout, profile name, and API client ID with `#tool:vscode/askQuestions`. Collect the client secret with a masked/secret field; never ask the user to paste it into normal chat. Client ID and secret are mandatory. Use displayed defaults when optional values are left blank.

Run the non-interactive login command from the skill root:

Inject `OCTANE_LOGIN_SECRET` through the tool launcher's masked environment without placing its value in command text, then run:

```bash
uv run scripts/octane_token.py login \
  --profile "<profile-name>" \
  --base-url "<octane-base-url>" \
  --user "<api-client-id>" \
  --shared-space-id "<shared-space-id>" \
  --workspace-id "<workspace-id>" \
  --timeout "<seconds>"
```

Add `--no-activate` only when the profile should be saved without becoming active. The script fails with a list of missing values instead of prompting. It stores the secret in OS keyring service `AgentDevelopmentToolkit:alm-octane`, stores only non-secret profile metadata in stable per-user `octane.json`, and attempts to roll both back on failure. An activating login performs a minimal verification read. With `--no-activate`, the read uses the previously active profile; select and test the new profile explicitly. Do not use `--skip-test` in the interactive login workflow.

Useful lifecycle commands:

```bash
uv run scripts/octane_token.py profiles
uv run scripts/octane_token.py use-profile --profile "<profile-name>"
uv run scripts/octane_token.py delete-profile --profile "<profile-name>"
```

Deleting profile metadata does not delete its keyring secret. If login reports a missing keyring entry, retry login for that profile. For a keyring backend error, unlock or configure the OS credential store. A remote 401 means the identity/secret was rejected; a remote 403 means the identity lacks access to the selected tenant. If rollback is reported incomplete, stop and inspect metadata and keyring selection separately before retrying. Never print, retrieve with `--show`, or copy a secret into chat while troubleshooting.
