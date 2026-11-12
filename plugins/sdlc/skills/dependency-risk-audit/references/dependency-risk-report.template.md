# Dependency Risk Audit Report

**Repository:** `<repo-name-or-path>`  
**Audit date:** `<YYYY-MM-DD>`  
**Auditor:** `<agent/user>`  
**Report version:** `1.0`

## 1. Executive Summary

Summarize the dependency posture in 3-6 bullets:

- Package managers detected: `<ecosystems>`
- Artifactory usage: `<Yes/No/Partial/Unknown>`
- Direct dependencies reviewed: `<count>`
- Bundled/direct binaries reviewed: `<count>`
- Risky or EOL/out-of-support findings: `<count>`
- Highest known security risk: `<Critical/High/Medium/Low/None known/Unknown>`

## 2. Scope

### Included

- Direct dependencies from package-manager manifests and lockfiles.
- Bundled/direct binaries committed to the repository or fetched by scripts.
- Transitive dependencies that are EOL/out-of-support or have known security risk.
- Existing SCA/SBOM/security scan outputs found in the repository.

### Excluded / Deferred

- Low-risk transitive dependencies are listed in `<dependency-inventory.md/csv>` when the dependency graph is large.
- License compliance is out of scope unless explicitly requested.
- Remediation changes are out of scope unless explicitly requested.

## 3. Repository and Package Manager Summary

| Ecosystem | Files / Evidence | Lockfile Present? | Notes |
|---|---|---|---|
| `<npm/maven/pip/etc.>` | `<path>` | `<Yes/No>` | `<notes>` |

## 4. Artifactory Configuration Summary

| Ecosystem / Tool | Artifactory Configured? | Evidence | Notes |
|---|---|---|---|
| `<ecosystem>` | `<Yes/No/Unknown>` | `<file path, URL, config key>` | `<notes>` |

## 5. Recommended Priority / Next Actions

Rank the most important remediation items. Consider known vulnerability severity, EOL/out-of-support status, dependency type, exposure, confidence, and migration effort.

| Priority | Component | Reason | Recommended Action | Target Date / Owner |
|---|---|---|---|---|
| `1` | `<component>` | `<why it matters>` | `<next step>` | `<optional>` |

## 6. Findings

| Component Name | Dependency Type | Current Version | From Artifactory? | EOL'd or Out of Support | Security Risk | Recommended Version / Replacement | Migration Plan | Effort for Migration | Confidence | Evidence / Source |
|---|---|---|---|---|---|---|---|---|---|---|
| `<name>` | `<Direct/Transitive/Bundled binary/Container/OS package/Unknown>` | `<version/range/unknown>` | `<Yes/No/Unknown>` | `<Yes/No/Unknown>` | `<Critical/High/Medium/Low/None known/Unknown>` | `<target version or replacement>` | `<plan, compatibility notes, validation areas, rollback, effort rationale>` | `<Low/Medium/High/Complex>` | `<High/Medium/Low>` | `<file paths, commands, advisory links, SCA IDs>` |

## 7. Full Inventory Reference

If the dependency graph is large, place full low-risk transitive inventory in a separate artifact and link it here.

- Full inventory artifact: `<dependency-inventory.md/csv or N/A>`
- Inventory generation method: `<lockfile parser/SCA report/package-manager command/manual review>`

## 8. Bundled Binary Appendix

Include this section only when bundled/direct binaries are found.

| File Path | SHA-256 | Inferred Component | Inferred Version | Provenance | From Artifactory? | Evidence / Notes |
|---|---|---|---|---|---|---|
| `<path/to/binary>` | `<sha256>` | `<name/unknown>` | `<version/unknown>` | `<Artifactory/Repository committed/Downloaded by script/Unknown>` | `<Yes/No/Unknown>` | `<metadata, script path, manifest, strings output>` |

## 9. Assumptions and Unknowns

List gaps that affect confidence, such as missing lockfiles, private registry access, unavailable advisory databases, unresolved binary identity, or stale SCA reports.

- `<assumption or unknown>`

## 10. Methodology

Describe how the audit was performed:

1. Discovered package-manager manifests, lockfiles, build scripts, CI scripts, and vendored/binary artifacts.
2. Reused existing SCA/SBOM/security scan artifacts where present.
3. Resolved component names and versions, preferring lockfiles/SCA outputs over manifests.
4. Inspected package-manager configuration for Artifactory/JFrog repository usage.
5. Checked lifecycle support and known vulnerability advisories.
6. Defined migration paths and effort ratings for EOL/out-of-support or risky components.

## 11. Audit Evidence Log

Record commands, files, tools, and dates so the report is reproducible.

| Type | Evidence | Result / Notes |
|---|---|---|
| `File inspected` | `<path>` | `<summary>` |
| `Command run` | ``<command>`` | `<summary; no dependency changes made>` |
| `Tool/report used` | `<SCA/SBOM/tool>` | `<version/date/result>` |
| `External source` | `<URL/advisory/vendor policy>` | `<summary>` |
