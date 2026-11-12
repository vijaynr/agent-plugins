# OBS Setup Research and Decisions

## Sources checked

1. [OBS User Guide: osc installation and configuration](https://openbuildservice.org/help/manuals/obs-user-guide/cha-obs-osc). Documents package-manager installation, explicit API selection, keyrings, CA configuration, and first-use setup. Some sections describe the legacy `~/.oscrc` path and plain text defaults.
2. [osc 1.27.3 README](https://github.com/openSUSE/osc/blob/1.27.3/README.md). Documents `~/.config/osc/oscrc`, Python keyring support, and backend prerequisites. Its public repository examples are not approved internal installation sources.
3. [osc 1.27.3 conf.py](https://github.com/openSUSE/osc/blob/1.27.3/osc/conf.py). `identify_conf` selects existing config locations. `interactive_config_setup` requests username/password and calls `select_credentials_manager_descr` before saving a host. The available storage list is dynamic. It can include insecure stores, so never prescribe a choice number or accept a default blindly.
4. [osc 1.27.3 credentials.py](https://github.com/openSUSE/osc/blob/1.27.3/osc/credentials.py). Distinguishes plaintext, obfuscated, transient, and supported keyring stores. Transient mode prompts again per process; keyring availability depends on the runtime and backend.
5. [osc 1.27.3 commandline.py](https://github.com/openSUSE/osc/blob/1.27.3/osc/commandline.py). `whois` without a username uses the configured account. `config --select-password-store` and `config --change-password` operate on the named API configuration. These are local credential operations, not an OBS server password reset. Agent tooling must not execute their secret prompts.
6. OBS source at revision `567f58ec65d4a9ffa6a7c1b249b6463d8428ba1f`: [API routes](https://github.com/openSUSE/open-build-service/blob/567f58ec65d4a9ffa6a7c1b249b6463d8428ba1f/src/api/config/routes/api.rb) and [PersonController](https://github.com/openSUSE/open-build-service/blob/567f58ec65d4a9ffa6a7c1b249b6463d8428ba1f/src/api/app/controllers/person_controller.rb). The GET `/person/:login/watchlist` uses a user authorization check. User-info lookup alone is not equivalent to this check. Discard the private watchlist body; record only the result. Endpoint support and policy on older or customized internal servers remain unverified.
7. [Microsoft WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install). WSL provisioning is an explicit system change, distinct from configuring an already available Linux environment.

## Decisions

- Provide `obs-setup` as a guided command plus a lazily loaded `setup-obs` skill. No new CLI script, credential store, or runtime dependency is required.
- Use one explicit internal API URL on every `osc` invocation. Do not change global default host selection or infer the API from a UI URL.
- Hand interactive configuration to the user's private terminal. Never route password entry through chat, agent stdin, a recorded shell, or a model-supplied environment value.
- Preserve existing client configuration. Prefer the client's targeted password-store operation over deleting host sections as older documentation suggests. Get approval for any migration or credential replacement.
- Require an approved persistent keyring backend for unattended use. Transient mode is acceptable only as an explicit manual-session choice. Never silently fall back to plain text or obfuscation.
- Separate connection/account lookup, protected-resource authentication checks, workspace configuration, and local-build prerequisites. A public read cannot prove authentication. A protected read cannot prove write permission.
- Treat SSO, internal CA, proxy authentication, headless keyring support, and client/server version differences as explicit operator decisions. Do not invent platform-specific authentication workarounds.

## Verification limits

Repository tests check command registration, references, explicit-host examples, and documented safety contracts. They do not install tools, log in, inspect credential files, or contact any OBS instance. This research is not a live compatibility certification. Validate the installed client's help and the internal administrator's authentication policy before setup. A pilot needs a user-provided API URL and permission for the named reads.
