# Platform and Installation Guidance

Read only the selected platform section. Discovery is read-only. Any installation, elevation, credential-store change, PATH change, WSL/VM creation, or CA change needs approval for the exact command and environment.

## Linux

Use the organization's approved distribution repositories and supported `osc` version. The OBS manual recommends the distribution package manager. On SUSE/openSUSE with an approved repository already configured, a possible approved installation is:

```bash
sudo zypper install osc
```

Do not run it until the user approves. On Debian/Ubuntu or Fedora/RHEL-family systems, first check whether the approved repositories provide `osc`; then propose the matching package-manager installation. Do not assume the same package/version exists on every enterprise distribution. If unavailable, ask for the organization's approved source or environment.

Secure persistent storage also needs Python keyring support and an available backend in the `osc` runtime. The researched upstream README names `python3-keyring` and desktop/kernel-keyring backends. The correct package names and backend suitability depend on the distribution, desktop session, and internal policy. Ask before installing them. An installed Python library alone does not prove a usable or approved backend. On headless hosts, stop if there is no approved persistent store; use explicit transient/manual-only mode instead of plaintext storage.

Local RPM builds need additional target-compatible tooling and an approved isolated Linux environment. Installing `osc` does not prove local-build readiness. Do not install or run privileged build tooling during connection setup.

## Windows

Ask which approved WSL distribution, Linux VM, or remote Linux host the developer will use. Check existing WSL availability/status from PowerShell if the user permits. Do not select a distribution or use Windows administrator privileges silently.

Microsoft documents WSL installation with an elevated terminal and possible restart. Direct the user to the [official WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install) if provisioning is needed. WSL installation is an optional system change, not a prerequisite for every user who already has a remote build environment.

Run Linux `osc` setup and verification inside the chosen distribution/VM. Its home directory, keyring, network/VPN access, CA trust, and executable differ from Windows. Do not configure a Windows home file and claim that WSL is ready. If native Windows `osc` is already installed, treat it as a separate client-only environment and confirm supported behavior with its installed help; do not promise local RPM builds there.

## macOS

Prefer the team's approved Linux VM/remote environment for RPM work. If the user wants a macOS client, use an existing supported `osc` installation or request the organization's approved installation method. Do not invent a universal Homebrew formula or global pip installation recipe. Verify keyring support in that exact client environment. Local client access is separate from building RPMs in Linux.

## Containers and remote environments

An ephemeral container or SSH host may not share the user's desktop keyring or home directory. Do not mount host credentials or copy config/keyring files to solve this. Ask the owner for the approved authentication mechanism. Record where the setup was actually performed. Use that same environment for later checks.

## Network and certificates

Do not add public repositories, import signing keys, download unsigned executables, install an unstable upstream client, or use a curl-to-shell installer automatically. Internal package sources and trust roots come from the owner/administrator.

For an internal CA, use the organization's approved certificate distribution procedure. The OBS manual documents `cafile`/`capath`; any change belongs to the intended API host and environment and requires approval. Never use HTTP, disable TLS checks, accept a certificate by guesswork, or print proxy credential settings. If proxy/SSO behavior is uncertain, stop and involve the administrator.
