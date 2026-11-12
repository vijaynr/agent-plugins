---
name: dependency-risk-audit
disable-model-invocation: true
description: "Audit codebase dependencies from package managers and bundled binaries for Artifactory sourcing, EOL/out-of-support status, security risk, migration paths, migration effort, and a Markdown findings report."
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Dependency Risk Audit

Identify third-party dependencies consumed by a codebase, determine whether package managers source them from Artifactory, assess EOL/out-of-support and known security risk, define migration paths, estimate migration effort, and produce a defensible Markdown report.

## Default outputs

- Create or update `dependency-risk-report.md` at the repository root unless the user requests another path.
- Use `references/dependency-risk-report.template.md` as the report structure.
- If the resolved dependency graph is large, create a separate full inventory artifact such as `dependency-inventory.md` or `dependency-inventory.csv`.
- If bundled/direct binaries are found, include a bundled-binary appendix with file path, SHA-256, identity/version, and provenance.

## Main findings scope

The main findings table must include:

- All direct dependencies.
- All bundled/direct binaries.
- All transitive dependencies that are EOL/out-of-support or have known security risk.

Low-risk transitive dependencies may be moved to the separate full inventory artifact, but must not be silently omitted.

## Required findings table columns

| Component Name | Dependency Type | Current Version | From Artifactory? | EOL'd or Out of Support | Security Risk | Recommended Version / Replacement | Migration Plan | Effort for Migration | Confidence | Evidence / Source |
|---|---|---|---|---|---|---|---|---|---|---|

Column value rules:

- `Dependency Type`: `Direct`, `Transitive`, `Bundled binary`, `Container/OS package`, or `Unknown`.
- `From Artifactory?`: `Yes`, `No`, or `Unknown`; require evidence.
- `EOL'd or Out of Support`: `Yes`, `No`, or `Unknown`; require defensible vendor/project evidence for `Yes` or `No` when available.
- `Security Risk`: known vulnerability/advisory severity only: `Critical`, `High`, `Medium`, `Low`, `None known`, or `Unknown`.
- `Effort for Migration`: exactly one of `Low`, `Medium`, `High`, or `Complex`; include rationale inside `Migration Plan`.
- `Confidence`: `High`, `Medium`, or `Low`.

## Steps

1. Inventory dependency sources.
   - Detect package managers and manifests/lockfiles: npm/yarn/pnpm, Maven/Gradle, pip/Poetry/Pipenv/Conda, NuGet, Go modules, Cargo, Ruby/Bundler, Composer, Dockerfiles/container manifests, OS package manifests, build scripts, CI scripts, and vendored dependency directories.
   - Find direct binaries and embedded artifacts: `*.jar`, `*.war`, `*.ear`, `*.dll`, `*.so`, `*.dylib`, `*.exe`, `*.msi`, `*.deb`, `*.rpm`, `*.zip`, `*.tar*`, `vendor/`, `third_party/`, `lib/`, `libs/`, `external/`.
   - Look for existing SCA/security scan artifacts first: Black Duck, GitLab Dependency Scanning, Snyk, Dependabot, OWASP Dependency-Check, Trivy, CycloneDX/SPDX SBOMs, or vendor reports.
   - Completion criterion: every manifest, lockfile, package-manager config, CI install step, SCA artifact, and plausible bundled third-party binary has been listed with path evidence.

2. Resolve component identity.
   - Prefer existing SCA/SBOM output when present and current enough to be credible.
   - For package-manager dependencies, prefer lockfiles over manifests for exact name/version/transitive dependency resolution.
   - For direct binaries, infer name/version from filename, embedded metadata, manifest files, checksums, `strings`, archive contents, or adjacent documentation. Mark unresolved identity explicitly.
   - Completion criterion: each discovered component has a name, version when available, source path, and dependency type.

3. Determine Artifactory usage.
   - Inspect package-manager and build configuration for registry/repository/proxy settings, including `.npmrc`, `.yarnrc*`, `pnpm-workspace.yaml`, Maven `settings.xml`/`pom.xml`, Gradle `repositories`, `pip.conf`, `poetry.toml`, `Pipfile`, `NuGet.config`, `go env`/`GOPROXY`, `.cargo/config*`, Bundler config, Composer repositories, Docker registry config, CI variables, and build scripts.
   - Treat URLs/domains containing `artifactory`, `jfrog`, or known enterprise repository hosts as Artifactory-backed only when evidence shows the package manager uses them for resolution.
   - For bundled binaries, set `From Artifactory?` to `Yes` only if the repository, script, metadata, or documented fetch path proves the binary came from Artifactory; otherwise `No` or `Unknown` with evidence.
   - Completion criterion: every component has `Yes`, `No`, or `Unknown` for Artifactory sourcing with a short evidence note.

4. Assess support and known security risk.
   - Run read-only package-manager audit/outdated commands when available and safe, such as `npm audit`, `npm outdated`, `yarn npm audit`, `pnpm audit`, Maven/Gradle dependency update or vulnerability plugins, `pip-audit`, `safety`, `dotnet list package --vulnerable --outdated`, `govulncheck`, `cargo audit`, `bundle audit`, `composer audit`, `trivy`, or equivalent. Do not install, upgrade, or rewrite lockfiles unless the user explicitly asks.
   - Check whether each component/version is EOL, deprecated, archived, unmaintained, vendor out-of-support, or superseded by an announced replacement. Prefer official/vendor/project evidence: EOL policy, release notes, repository archived/deprecated status, package deprecation notice, or maintained-version matrix.
   - Check known security risk using SCA outputs, package-manager audit output, CVEs, GitHub/GitLab advisories, NVD/vendor advisories, and release notes.
   - Keep lifecycle and security separate: do not inflate `Security Risk` solely because a component is EOL/out-of-support.
   - If internet, registry, or advisory access is unavailable, continue best-effort using local evidence and mark unverifiable support/security fields as `Unknown`.
   - Completion criterion: every main-scope component has support/security classifications and cited evidence or a clear reason evidence could not be found.

5. Define migration paths.
   - For each EOL/out-of-support or risky component, provide a concrete migration plan: target supported version or replacement, code/config changes, compatibility concerns, test areas, rollout/rollback notes, and effort rationale.
   - If no migration is required, state `No migration required; continue monitoring`.
   - If identity or target is unknown, state the discovery action needed before migration.
   - Completion criterion: every finding has an actionable migration plan or a justified no-op/unknown-discovery plan.

6. Estimate migration effort.
   - `Low`: patch/minor upgrade or repository/config-only change; low API break risk; standard tests likely sufficient.
   - `Medium`: major upgrade with documented breaking changes, moderate code changes, or several dependent modules affected.
   - `High`: broad API/framework/runtime migration, data/config format changes, integration retesting, or coordinated release needed.
   - `Complex`: replacement/re-architecture, no drop-in supported path, multiple services/products affected, licensing/procurement blockers, or substantial manual remediation of bundled binaries.
   - Completion criterion: every row has exactly one effort value justified by the migration plan.

7. Write the Markdown report.
   - Copy the structure from `references/dependency-risk-report.template.md`.
   - Include scope, repository/package-manager summary, Artifactory configuration summary, methodology, assumptions/unknowns, recommended priority/next actions, the required findings table, optional full inventory reference, optional bundled-binary appendix, and audit evidence log.
   - Completion criterion: `dependency-risk-report.md` exists and includes the required table with one row per main-scope component or consolidated component/version finding.

## Out of scope by default

- License compliance/risk review. Add it only if the user asks.
- Remediation changes. Do not modify dependency versions, package-manager configuration, or binaries unless the user explicitly asks.
