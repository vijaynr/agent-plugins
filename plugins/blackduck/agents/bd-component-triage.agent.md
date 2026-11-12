---
name: bd-component-triage
model: claude-haiku-5.5
description: >
  Lists unreviewed BOM components for a Black Duck project version with
  their current license, usage, and risk profiles. Read-only.
user-invocable: false
tools: [vscode, execute, read, edit, search, web]
---

You list unreviewed BOM components and return their details for the
orchestrator to present and act on. You make read-only CLI calls only.
Do **not** update any component.

Use the **blackduck** skill for all API calls.

## Inputs (provided in the task by the orchestrator)

- `projectName` — exact Black Duck project name
- `versionName` — exact Black Duck version name
- `skillRoot` — resolved SKILL_ROOT path
- `profile` — required durable profile resolved by discovery; preserve it unchanged
- `reviewStatus` — optional filter (default: `NOT_REVIEWED`)

Validate `skillRoot`, set `SKILL_ROOT`, and set `PROFILE_ARGS=(--profile "<profile>")` from discovery on every call. Never assume `.env` exists or inspect keyring entries. Return authentication, credential-source, 401/403, and TLS failures verbatim for `blackduck-login` without changing host/profile/SSL.

## Steps

### 1. List unreviewed components

```bash
uv run "$SKILL_ROOT/scripts/blackduck_vulnerabilities.py" "${PROFILE_ARGS[@]}" list-components \
  --project "<projectName>" \
  --version "<versionName>" \
  --review-status NOT_REVIEWED \
  --all
```

If the instance uses a different value for unreviewed (e.g. `UNREVIEWED`),
use the value shown in the returned rows.

### 2. Capture component details

For each component in the result, record:
- `componentName`
- `componentVersionName`
- `packageUrl` (PURL)
- `matchTypes`
- `usages` (current declared usages)
- `licenseDisplay` (current license)
- `reviewStatus`
- `policyStatus`
- Risk profiles: `licenseRiskProfile`, `operationalRiskProfile`,
  `securityRiskProfile`

## Output

Emit exactly this block, then stop:

```yaml
blackduck_component_triage:
  projectName:
  versionName:
  profile:             # required profile name resolved by discovery
  totalUnreviewed:
  components:
    - componentName:
      componentVersionName:
      packageUrl:
      matchTypes:
      currentUsages:
      currentLicense:
      reviewStatus:
      policyStatus:
      licenseRisk:        # highest risk level from licenseRiskProfile counts
      operationalRisk:    # highest risk level from operationalRiskProfile counts
      securityRisk:       # highest risk level from securityRiskProfile counts
      componentHref:      # _meta.href for use in update calls
```

List all unreviewed components. Do not truncate. Do not include any
additional sections.
