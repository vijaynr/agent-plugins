---
name: blackduck-login
description: >
  Configure durable Black Duck credential profiles in OS keyring and stable
  per-user URL/SSL metadata, then verify the named profile.
argument-hint: "[profile]"
---

# Black Duck Login

Resolve the installed Black Duck skill root, then read new-profile fallback defaults:

```bash
uv run scripts/blackduck_token.py defaults
```

Collect profile name, URL, keyring username, and SSL-verification setting with `#tool:vscode/askQuestions`. For an existing profile, explicitly confirm URL and SSL behavior rather than assuming `defaults` shows its current values. Collect the API token with a masked/secret field; never ask the user to paste it into normal chat.

Inject `BLACKDUCK_LOGIN_TOKEN` through the tool launcher's masked environment without putting its value in command text, then run:

```bash
uv run scripts/blackduck_token.py login \
  --profile "<profile-name>" \
  --url "<blackduck-url>" \
  --user "<keyring-username>" \
  --verify-ssl "<true-or-false>"
```

Add `--no-activate` only when saving without changing the active profile. The script is non-interactive and reports missing values instead of prompting. It stores the token in OS keyring service `AgentDevelopmentToolkit:blackduck`, stores only non-secret URL and SSL metadata in stable `blackduck.json`, verifies the named profile with a minimal read, and attempts best-effort rollback on failure. After a failed mutation, verify metadata and keyring selection separately before retrying. Do not use `--skip-test` in this interactive workflow.

```bash
uv run scripts/blackduck_token.py profiles
uv run scripts/blackduck_token.py use-profile --profile "<profile-name>"
uv run scripts/blackduck_token.py delete-profile --profile "<profile-name>"
```

Deleting metadata never deletes keyring tokens. A missing entry requires login for that profile; a backend error requires repairing/unlocking the OS credential store. HTTP 401 means the selected instance rejected the token; HTTP 403 means the identity lacks access. For TLS errors, verify URL/CA trust and disable SSL verification only with explicit risk acceptance. Because rollback is not guaranteed or separately classified, inspect metadata and keyring selection separately after any failed login mutation. Never use `--show` or print a token while troubleshooting.
