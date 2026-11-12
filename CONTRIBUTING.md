# Contributing

This repository is a plugin workspace. Keep changes small, validated, and documented.

## Plugin workspace basics

- Add or change plugin assets under the owning `plugins/<plugin>/` directory.
- Keep plugin, skill, command, and agent names kebab-case unless a host format requires otherwise.
- Skill directory names must match each `SKILL.md` `name` field.
- Agent frontmatter `name` values must match their `.agent.md` file stems.
- Command filenames must match command frontmatter `name` values.
- Do not commit `.env`, credentials, generated Python cache files, or machine-local outputs.

## Skill scripts

Before adding or changing scripts under `plugins/<plugin>/skills/<skill>/scripts/`, read the [Agent Skills Guide](docs/agent-skills-guide.md).

In short:

- declare PEP 723 metadata for scripts with third-party dependencies,
- make `--help` work without credentials or network access,
- prefer explicit arguments and JSON output,
- keep write scripts gated, narrowly scoped, and verified by a read-after-write,
- update tests and the script guide when the CLI surface or dependencies change.

## Validation

Run the existing script suites before submitting changes. See the [Testing Guidelines](docs/testing-guidelines.md) for separate plugin commands. Keep tests only for active plugin or skill scripts. Do not add tests as part of the current cleanup.

```bash
python -m pytest tests -q
```

If marketplace metadata changes, update `.github/plugin/marketplace.json` to match `marketplace.json`, keeping the expected `../../` prefix on GitHub plugin `source` paths, then run:

```bash
./agents.sh validate
```

## Documentation updates

When adding, removing, renaming, or materially changing plugin assets, update:

- the owning plugin `README.md`,
- the owning plugin `AGENTS.md`,
- root documentation when workspace-wide conventions change,
- `docs/agent-skills-guide.md` when script conventions, dependencies, or external tools change,
- `docs/testing-guidelines.md` when validation or test conventions change.
