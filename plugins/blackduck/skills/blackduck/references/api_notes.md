# Black Duck REST API – Vulnerability Endpoints Reference

## Authentication & Token Rotation

Black Duck uses a two-tier token model:

1. **API access token** (long-lived) – generated manually in the Black Duck UI
   under *Profile → Access Tokens*.
2. **Bearer token** (short-lived, ~2 hours) – obtained programmatically by
   exchanging the access token.

### Obtain a bearer token

```
POST /api/tokens/authenticate
Authorization: token <API_ACCESS_TOKEN>
Accept: application/vnd.blackducksoftware.user-4+json
```

**Response** (`200 OK`):
```json
{
  "bearerToken": "eyJhbGci…",
  "expiresInMilliseconds": 7200000
}
```

The script caches the bearer token and automatically re-authenticates when
`expiresInMilliseconds` is about to elapse (with a 2-minute safety margin).

### Using the bearer token

All subsequent API calls include:
```
Authorization: Bearer <BEARER_TOKEN>
```

## Key Endpoints

### 1. List Projects
```
GET /api/projects?q=name:{name}
Accept: application/vnd.blackducksoftware.project-detail-4+json
```

### 2. List Project Versions
```
GET /api/projects/{projectId}/versions
Accept: application/vnd.blackducksoftware.project-detail-5+json
```

### 3. List Licenses

```
GET /api/licenses?q=name:{name}
Accept: application/vnd.blackducksoftware.component-detail-5+json
```

Used by `list-licenses` to enumerate license records that can be selected for
component license updates.

### 4. List Vulnerable BOM Components
```
GET /api/projects/{projectId}/versions/{versionId}/vulnerable-bom-components
Accept: application/vnd.blackducksoftware.bill-of-materials-6+json
```
Returns paginated list of BOM components with known vulnerabilities.
Each item contains a `vulnerabilityWithRemediation` object with:
- `vulnerabilityName` – CVE or BDSA identifier
- `severity` – CRITICAL, HIGH, MEDIUM, LOW, OK, UNKNOWN
- `baseScore` / `overallScore` – CVSS scores
- `remediationStatus` – current triage status
- `description`, `cweId`, `cvss2Vector`, `cvss3Vector`, etc.

### 5. Get Vulnerability Details
```
GET /api/vulnerabilities/{CVE-or-BDSA-id}
Accept: application/json
```
Returns server-side details for a CVE/BDSA when exposed by the Black Duck instance.
The CLI combines this with affected components discovered from vulnerable BOM rows.

### 6. List Project Version Code Locations
```
GET /api/projects/{projectId}/versions/{versionId}/codelocations
Accept: application/vnd.blackducksoftware.scan-4+json
```
Returns code locations/scans mapped to a project version. Useful fields include:
- `name` – code location / scan name, often encodes project, branch, module, detector, or package manager
- `url` – scan UUID URN
- `mappedProjectVersion` – project version URL
- `createdAt`, `updatedAt`, `status`, `scanSize`

### 7. Matched Files for a BOM Component

Three endpoint tiers exist, from most to least granular:

```
# Origin-level (most granular — use this first)
GET /api/projects/{projectId}/versions/{versionId}/components/{componentId}/versions/{componentVersionId}/origins/{originId}/matched-files

# Component-version level
GET /api/projects/{projectId}/versions/{versionId}/components/{componentId}/versions/{componentVersionId}/matched-files

# Component level (broadest fallback)
GET /api/projects/{projectId}/versions/{versionId}/components/{componentId}/matched-files
```

The `rel: "matched-files"` link in the BOM component's `_meta.links` already points to the
**origin-level URL** (i.e. it already includes `/origins/{originId}/`). Additional origins are
embedded in `item.origins[]`, each with their own `_meta.links[rel="matched-files"]` link.

All three endpoints support `offset`/`limit` pagination. Since 2023.10, responses include a
`uri` field alongside `path` and `archiveContext`. Files inside archives are reported with
both `archiveContext` (the archive path) and `path` (the path within the archive).

**Critical: always paginate.** A single GET with `limit=250` silently truncates results if
more than 250 files match. Use the paging loop (`offset` increments until `totalCount` is
reached).

**When `matched-files` returns `totalCount=0` despite `totalFileMatchCount > 0`:**
The component was detected via **package-manager manifest scanning** (matchTypes:
`FILE_DEPENDENCY_DIRECT` / `FILE_DEPENDENCY_TRANSITIVE`). `totalFileMatchCount` counts how
many manifest files (e.g. `pom.xml`, `package.json`) declare this dependency — not binary or
source content matches. The `matched-files` API only returns content/signature-level matches,
which are empty for manifest-based detection. Use `get-dependency-paths` instead to understand
how the component is pulled into the build.

### 7a. Dependency-Graph Resolution Paths (BD 2021.2+)

```
GET /api/projects/{projectId}/versions/{versionId}/components/{componentId}/versions/{componentVersionId}/origins/{originId}/dependency-paths
```

Returns the dependency-graph resolution path for package-manager-detected components:
- `type`: `DIRECT` or `TRANSITIVE`
- `pathNodes`: ordered list of packages in the resolution chain

This endpoint was added in Black Duck 2021.2. On older instances it returns **404** (not an
error — the data simply was not captured). Dependency graph data also requires a Detect scan
with dependency resolution enabled (not a binary/signature-only scan).

The URL is derived from the origin's `matched-files` link by replacing the `/matched-files`
suffix with `/dependency-paths`. Origins are embedded in the BOM component body under the
`origins[]` field when fetched with the `bill-of-materials-6+json` Accept header.

**Detection method → recommended tool:**

| matchType | Tool to use |
|-----------|-------------|
| `BINARY_SCAN`, `EXACT_MATCH`, `SNIPPET` | `get-matched-files` |
| `FILE_DEPENDENCY_DIRECT` / `TRANSITIVE` (manifest-based) | `get-dependency-paths` |
| `MANUAL_BOM_COMPONENT` | Neither — no scan evidence exists |

### 8. Update BOM Component Review Status, License, Usage, and Comment

Preferred compatibility path: list BOM components with the BOM v6 media type,
then update each matching component via that item's `_meta.href`.

```
PUT /api/projects/{projectId}/versions/{versionId}/components/{componentId}/versions/{componentVersionId}
Accept: application/vnd.blackducksoftware.bill-of-materials-6+json
Content-Type: application/vnd.blackducksoftware.bill-of-materials-6+json
```

Body used by `update-component` varies by Black Duck version; the CLI tries
partial and full-item payloads, with JSON and BOM v6 media types. Typical fields:

```json
{
  "reviewStatus": "REVIEWED",
  "licenses": [{"license": "https://blackduck.example/api/licenses/licenseId"}],
  "usages": ["DYNAMICALLY_LINKED"],
  "comment": "No matching license found; leave license unchanged."
}
```

`--license` resolves a license name through `GET /api/licenses?q=name:{name}` or
accepts a license UUID/full license URL directly. `--comment` sends a free-text
component note/comment when supported by the instance.

### 9. Update Vulnerability Remediation Status

Preferred compatibility path: list vulnerable BOM components with the BOM v6 media
type, then update each matching component vulnerability via that item's `_meta.href`.

```
PUT {vulnerable-bom-component-item._meta.href}
Accept: application/vnd.blackducksoftware.bill-of-materials-6+json
Content-Type: application/vnd.blackducksoftware.bill-of-materials-6+json
```

Status/justification/remediation body used by `update-vulnerability`:
```json
{
  "remediationStatus": "AFFECTED",
  "remediation": "VENDOR_FIX"
}
```

For Known Not Affected:
```json
{
  "remediationStatus": "NOT_AFFECTED",
  "remediationJustification": "VULNERABLE_CODE_NOT_PRESENT"
}
```

Comment-only body used by `comment-vulnerability`:
```json
{
  "comment": "planned to be fixed"
}
```

Keep status/justification and comment updates separate. Some Black Duck versions
return `406 Not Acceptable` when fields are combined or when strict PUT media
types are used.

Key fields cross-checked against Black Duck docs:
- `remediationStatus` – documented values:
  `NEW`, `NEEDS_REVIEW`, `AFFECTED`, `NOT_AFFECTED`, `UNDER_INVESTIGATION`,
  `REMEDIATION_REQUIRED`, `REMEDIATION_COMPLETE`, `MITIGATED`, `PATCHED`,
  `IGNORED`, `DUPLICATE`.
  The skill accepts legacy alias `NOT_VULNERABLE` and sends `NOT_AFFECTED`.
- `remediationJustification` – status justification for `NOT_AFFECTED`:
  `COMPONENT_NOT_PRESENT`, `VULNERABLE_CODE_NOT_PRESENT`,
  `VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY`,
  `VULNERABLE_CODE_NOT_IN_EXECUTE_PATH`, `INLINE_MITIGATIONS_ALREADY_EXIST`.
- `remediation` – remediation option for `AFFECTED`:
  `MITIGATION`, `NO_FIX_PLANNED`, `NONE_AVAILABLE`, `VENDOR_FIX`, `WORKAROUND`.
  The skill accepts legacy aliases `WILL_NOT_FIX` -> `NO_FIX_PLANNED` and
  `NONE` -> `NONE_AVAILABLE`.
- `comment` – free-text explanation, sent separately by `comment-vulnerability`.

Returns `200 OK` or `202 Accepted` on success.

## Pagination

All list endpoints support `offset` and `limit` query parameters.  The script
pages automatically (default page size 250) and yields items via a generator to
keep memory usage low.

### 7b. Component Origins

Each BOM component returned with `Accept: application/vnd.blackducksoftware.bill-of-materials-6+json`
contains an embedded `origins[]` array. Each origin has:

```json
{
  "name": "1.17.2",
  "origin": "https://.../api/components/{compId}/versions/{compVerId}/origins/{originId}",
  "externalNamespace": "maven",
  "externalId": "commons-codec:commons-codec:1.17.2",
  "packageUrl": "pkg:maven/commons-codec/commons-codec@1.17.2",
  "_meta": {
    "links": [
      {"rel": "origin",                      "href": "...global origin URL..."},
      {"rel": "matched-files",               "href": "...project-scoped origin-level matched-files..."},
      {"rel": "upgrade-guidance",            "href": "..."},
      {"rel": "transitive-upgrade-guidance", "href": "..."},
      {"rel": "component-origin-copyrights", "href": "..."}
    ]
  }
}
```

The `rel: "matched-files"` link on each origin is project-version-scoped and is the
**authoritative URL** for that origin's file matches. The top-level BOM component's
`rel: "matched-files"` link is equivalent to the primary origin's link.

## Official Resources

- Python SDK: https://github.com/blackducksoftware/hub-rest-api-python
- Client User Guide: https://github.com/blackducksoftware/hub-rest-api-python/wiki/Client-User-Guide
- API docs (per-instance): `https://<your-bd-url>/api-doc/public.html`
