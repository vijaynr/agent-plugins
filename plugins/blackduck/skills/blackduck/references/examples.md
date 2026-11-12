# Black Duck Vulnerability CLI Examples

Resolve `SKILL_ROOT` before running these examples:

```bash
for d in "$HOME"/.copilot/installed-plugins/*/blackduck/skills/blackduck "$HOME/.copilot/skills/blackduck" "$HOME/.agents/skills/blackduck"; do
  if [ -f "$d/SKILL.md" ]; then SKILL_ROOT="$d"; break; fi
done
[ -n "$SKILL_ROOT" ] || { echo "Black Duck skill not found"; exit 1; }
```

All tools are implemented by:

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" <tool> [args]
```

## Discover projects, versions, and components

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-projects \
  --query "MyApp" --limit 20

uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-versions \
  --project "MyApp" --query "1.0" --limit 20

uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-licenses \
  --query "Apache" --limit 20

uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-components \
  --project "MyApp" --version "1.0" --query "openssl" --exact --limit 50

uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-components \
  --project "MyApp" --version "1.0" --filter "componentRisk:HIGH" --policy-status IN_VIOLATION

# Friendly component filters: Review Status, Name, License Risk,
# Operational Risk, and Security Risk. Use --all to return every match.
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-components \
  --project "MyApp" --version "1.0" --name "openssl" --exact \
  --review-status REVIEWED --license-risk HIGH \
  --operational-risk LOW --security-risk HIGH --all
```

## List vulnerabilities

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-vulnerabilities \
  --project "MyApp" --version "1.0" --limit 100

uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-vulnerabilities \
  --project "MyApp" --version "1.0" --severity CRITICAL

uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-vulnerabilities \
  --project "MyApp" --version "1.0" --status NEW

uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" list-vulnerabilities \
  --project "MyApp" --version "1.0" \
  --component 7460c937-f013-4c3a-bdf3-ace04cfd0304
```

## Get code-location evidence and matched file paths

For scan-level context:

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-code-location \
  --project "MyApp" --version "1.0" --component "openssl" --exact
```

For file-path evidence only (fully paginated, with origins traversal):

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-matched-files \
  --project "MyApp" --version "1.0" --component "openssl" --exact
```

When `totalMatchedFiles=0`, read the `note` field in the response:
- `FILE_DEPENDENCY_*` match types mean manifest-based detection; `matched-files` will always be empty.
  `totalFileMatchCount` counts manifest-file occurrences (pom.xml, package.json), not binary matches.
- Use `get-dependency-paths` instead to understand how the component enters the build.

For dependency-graph resolution (package-manager-detected components, requires BD 2021.2+):

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-dependency-paths \
  --project "MyApp" --version "1.0" --component "openssl" --exact
```

If `dependencyPaths` is empty, read the `note` field — the endpoint may not be supported,
or the scan did not capture dependency graph data.

Given a component id or URL:

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-matched-files \
  --project "MyApp" --version "1.0" \
  --component "7460c937-f013-4c3a-bdf3-ace04cfd0304" --component-id

uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-dependency-paths \
  --project "MyApp" --version "1.0" \
  --component "7460c937-f013-4c3a-bdf3-ace04cfd0304" --component-id
```

## Update BOM component review status, license, and usage

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" update-component \
  --project "MyApp" --version "1.0" \
  --component "openssl" --exact \
  --review-status REVIEWED \
  --license "Apache-2.0" \
  --usage DYNAMICALLY_LINKED
```

`--license` accepts a license name, license UUID, or full `/api/licenses/{id}` URL.
Use `list-licenses` first to choose an available license; do not guess by trying
licenses until one succeeds. Repeat `--usage` to set multiple usage values. Use
`--comment` when no matching license is available or when adding a review note.
Re-run `list-components` after the write to verify the component row.

## Update remediation status

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" update-vulnerability \
  --project "MyApp" --version "1.0" \
  --vuln-id "BDSA-2026-7659" --related-id "CVE-2026-5598" \
  --status AFFECTED --justification VENDOR_FIX \
  --comment "Planned to be fixed in next release"
```

## Get vulnerability details

For a standalone CVE:

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-vulnerability-details \
  --project "MyApp" --version "1.0" \
  --vuln-id "CVE-2026-5598"
```

For a BDSA related to a CVE:

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" get-vulnerability-details \
  --project "MyApp" --version "1.0" \
  --vuln-id "BDSA-2026-7659" --related-id "CVE-2026-5598"
```

## Typical triage workflow

1. `list-projects --query <name>` to identify the exact project.
2. `list-versions --project <name>` to identify the exact version.
3. `list-vulnerabilities --project <name> --version <version> --severity CRITICAL` to find urgent items.
4. `get-vulnerability-details` for selected CVE/BDSA details and affected components.
5. Inspect `matchTypes` on each affected component to choose the right code-path tool:
   - `FILE_DEPENDENCY_*` → `get-dependency-paths` (manifest-detected; `matched-files` will be empty)
   - `BINARY_SCAN`, `EXACT_MATCH`, `SNIPPET` → `get-matched-files` (returns actual file paths)
   - `MANUAL_BOM_COMPONENT` → no scan evidence; triage manually
6. `get-code-location` for scan-level context, or `get-matched-files` for file-path evidence.
7. Read the `note` field in `get-matched-files` / `get-dependency-paths` output when results are empty.
8. `update-vulnerability` only when the user explicitly asks to change remediation state.
9. Re-run `get-vulnerability-details` or `list-vulnerabilities` to verify writes.
