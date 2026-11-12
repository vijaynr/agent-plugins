# Agent Development Toolkit

A plugin workspace maintained by **vnr**. Install each plugin independently in GitHub Copilot. The marketplace identifier is `vnr-agent-development-toolkit`.

## Plugins

- [`sdlc`](plugins/sdlc/) — AI SDLC workflows and project context artifacts.
- [`context-engineering`](plugins/context-engineering/) — Local context-tooling setup.
- [`okf`](plugins/okf/) — Knowledge catalog initialization, ingestion, validation, and export.
- [`product-owner`](plugins/product-owner/) — PRD drafting and backlog shaping.
- [`obs`](plugins/obs/) — RPM packaging, builds, and approved submissions to configured OBS instances.
- [`octane`](plugins/octane/) — ALM Octane backlog and work-item operations.
- [`blackduck`](plugins/blackduck/) — Vulnerability analysis and BOM component review.
- [`gitlab`](plugins/gitlab/) — Issue and merge-request workflows.
- [`web-tools`](plugins/web-tools/) — Bounded web capture and browser automation.

Each plugin uses a small router skill. Supporting instructions load only when needed. See [context loading](docs/context-loading.md) for host limits and verification steps.

## Install

From a local checkout of this repository, register the marketplace and install the plugins you need:

```bash
copilot plugin marketplace add .
copilot plugin install sdlc@vnr-agent-development-toolkit
copilot plugin install context-engineering@vnr-agent-development-toolkit
copilot plugin install okf@vnr-agent-development-toolkit
copilot plugin install product-owner@vnr-agent-development-toolkit
copilot plugin install obs@vnr-agent-development-toolkit
copilot plugin install octane@vnr-agent-development-toolkit
copilot plugin install blackduck@vnr-agent-development-toolkit
copilot plugin install gitlab@vnr-agent-development-toolkit
copilot plugin install web-tools@vnr-agent-development-toolkit
```

For a direct development install, use a plugin path:

```bash
copilot plugin install plugins/sdlc
```

The workspace helper can list, validate, and install plugins:

```bash
./agents.sh list
./agents.sh validate
./agents.sh install sdlc
```

Open your project in Copilot. Start with the example prompt in the plugin README. Each plugin documents its commands, required access, output, and write approval gates.

## First prompt

```text
/spec encrypted-share-links allow admins to require expiring public links
Ask the product-owner agent to turn this idea into a PRD: “Customers need expiring public links.”
```

## Service configuration

Supply your own service endpoints at login or through a selected profile. The toolkit does not select a service host for you. Do not put secrets in chat or committed files.

Credentials use OS keyring services named `AgentDevelopmentToolkit:<service>`. Non-secret profiles use the platform configuration directory:

- Windows: `%APPDATA%/AgentDevelopmentToolkit`
- macOS: `~/Library/Application Support/AgentDevelopmentToolkit`
- Linux: `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit`

Set `AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` to override this directory. This is a breaking storage rename: users of earlier storage names must log in again. Old profile files and keyring entries are not read, moved, or deleted.

## Scope

Office, JATO UI, and the full threat-model/Security Impact plugin are not bundled. Generic SDLC frontend and security review remain available. Removing source plugins does not uninstall existing host plugins or change user reports.

## Development

See [Contributing](CONTRIBUTING.md), the [documentation index](docs/README.md), and the [Agent Skills Guide](docs/agent-skills-guide.md). Python scripts declare third-party dependencies with PEP 723 metadata where needed and should run with `uv run`.

The root `marketplace.json` is the source of truth. Keep `.github/plugin/marketplace.json` synchronized, with `../../` prefixed to its plugin source paths. Run `./agents.sh validate` after changes. See [testing guidelines](docs/testing-guidelines.md) for the retained script suites.
