---
name: gitlab-login
description: >
  Configure durable GitLab credential profiles in the OS keyring and stable
  per-user metadata, including project safety settings, then verify access.
argument-hint: "[profile]"
---

# GitLab Login

Resolve the installed GitLab skill root, then read non-secret defaults:

```bash
uv run scripts/gitlab_token.py defaults
```

Collect profile name, API URL, keyring username, default project, allowed project IDs, read-only mode, and timeout with `#tool:vscode/askQuestions`. The `defaults` output is a fallback for a new profile, not a view of an existing named profile. When updating, ask the user to explicitly confirm every project/safety value so omitted arguments do not weaken or reset restrictions. Collect the personal access token with a masked/secret field; never ask for it in normal chat.

Inject `GITLAB_LOGIN_TOKEN` through the tool launcher's masked environment without placing its value in command text, then run:

```bash
uv run scripts/gitlab_token.py login \
  --profile "<profile-name>" \
  --api-url "<gitlab-api-url>" \
  --user "<keyring-username>" \
  --project-id "<default-project-id>" \
  --allowed-project-ids "<comma-separated-project-ids>" \
  --read-only-mode "<true-or-false>" \
  --timeout "<seconds>"
```

Add `--no-activate` only when saving without changing the active profile. The script is non-interactive and reports missing values instead of prompting. It stores the token in OS keyring service `AgentDevelopmentToolkit:gitlab`, stores only non-secret endpoint and safety metadata in stable `gitlab.json`, and attempts transactional rollback on failure. Login performs a minimal verification read against the named profile, including with `--no-activate`. Do not use `--skip-test` in the interactive login workflow.

```bash
uv run scripts/gitlab_token.py profiles
uv run scripts/gitlab_token.py use-profile --profile "<profile-name>"
uv run scripts/gitlab_token.py delete-profile --profile "<profile-name>"
```

Deleting metadata never deletes a keyring token. Missing-entry errors require login for that profile; backend errors require repairing/unlocking the OS credential store. HTTP 401 means the selected host rejected the token; HTTP 403 means the identity lacks authorization. If rollback is incomplete, stop and inspect metadata and keyring selection separately. Never use `--show` or print a token while troubleshooting.
