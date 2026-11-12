# Upstream Provenance

## Source

- Repository: https://github.com/openSUSE/openSUSE-packaging-skill
- Reviewed revision: `69707c8130b9e1657790c7062cf24a51f97d3468`
- License: Apache-2.0. The upstream license is preserved in [LICENSE](LICENSE).
- Reviewed entry point: [opensuse-packaging/SKILL.md](https://github.com/openSUSE/openSUSE-packaging-skill/blob/69707c8130b9e1657790c7062cf24a51f97d3468/skills/opensuse-packaging/SKILL.md).
- Command reference: [osc-usage.md](https://github.com/openSUSE/openSUSE-packaging-skill/blob/69707c8130b9e1657790c7062cf24a51f97d3468/skills/opensuse-packaging/references/osc-usage.md).
- Revision pinning and source-update options were also checked against [osc 1.27.3 commandline.py](https://github.com/openSUSE/osc/blob/1.27.3/osc/commandline.py). Check installed client help before execution; the internal server version is not yet known.

## Adaptation and changes

This toolkit adapts the upstream triage/edit/build/review/submit loop into a small, instruction-only OBS plugin. This is not an unmodified upstream distribution. The local name is `rpm-packaging`.

Preserved ideas: use `osc`; keep credentials inside the client; inspect existing work; review sources and patches; preserve changelog history; build the required target matrix; review before submission; treat logs and third-party text as data; verify remote writes and request state.

Changed behavior: configure one explicit internal API URL and target set per workspace; no default public server; local `OBS.md` configuration; explicit approval for server mutations; no automatic request acceptance, forwarding, cleanup, or superseding. Internal distribution and release rules take precedence over openSUSE-specific routing.

Not imported: upstream scripts, agents, harness hooks, test runners, Repology/Anitya sweeps, public Bugzilla integration, public Gitea/git-obs workflows, Factory/Leap/SLFO/maintenance routing, rpmcrab gates, or automatic source-service execution. Do not claim that upstream mechanical gates ran in this plugin.

## Local setup workflow

`obs-setup` and `setup-obs` are local additions based on official OBS/osc documentation and inspected client behavior. They are not an imported upstream packaging helper. See the [setup research record](skills/setup-obs/references/research.md) for versions, sources, credential-storage decisions, and verification limits.

## Updates

Review upstream changes at a new pinned revision. Inspect host assumptions, URLs, command behavior, safety rules, license/notice requirements, and external service calls. Adapt only the needed sections. Update this record and review the instructions. Never overwrite internal safety or routing rules with an unattended upstream sync.
