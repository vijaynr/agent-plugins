# ALM Octane CLI Examples

Resolve `SKILL_ROOT` before running these examples:

```bash
SKILL_ROOT=""
for d in "plugins/octane/skills/alm-octane" "skills/alm-octane" "." "$HOME"/.copilot/installed-plugins/*/octane/skills/alm-octane "$HOME/.copilot/skills/alm-octane" "$HOME/.agents/skills/alm-octane"; do
  if [ -f "$d/SKILL.md" ] && [ -f "$d/scripts/octane_client.py" ]; then SKILL_ROOT="$(cd "$d" && pwd)"; break; fi
done
[ -n "$SKILL_ROOT" ] || { echo "ALM Octane skill not found"; exit 1; }
```

## Generic discovery to verified write

These examples are templates, not permission to access a workspace. Profile names,
entity IDs, and reference IDs are fictitious. Use existing configured profiles;
never put secrets in command text or payload examples. Generic commands accept
`--shared-space-id`/`--workspace-id` when an explicit target is needed.

### Discover, then read one page

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" --profile staging get-entity-types
uv run "$SKILL_ROOT/scripts/octane_client.py" --profile staging get-entity-field-metadata --entity-type stories
uv run "$SKILL_ROOT/scripts/octane_client.py" --profile staging get-filter-metadata --entity-type stories
uv run "$SKILL_ROOT/scripts/octane_client.py" --profile staging get-entities --entity-type stories --query 'parent EQ {id EQ 3011}' --fields id,name,parent --order-by=-id --limit 20 --offset 0
uv run "$SKILL_ROOT/scripts/octane_client.py" --profile staging get-entity --entity-type stories --entity-id 912 --fields id,name,parent,client_lock_stamp
```

Native `--query` takes an expression **without outer double quotes**. One page is
returned; increase `--offset` explicitly for the next page. Defaults are limit 50,
offset 0, sort `id`. Server totals stay in `data`; requested bounds appear in
`pagination`. The server's configured maximum page size remains authoritative.

Filter grammar is bundled/cited documentation (Octane 26.1); field capabilities
are live workspace metadata with separate provenance. Missing capabilities are
unknown. The CLI does not fabricate an operator-discovery endpoint.

Keyword search is a separate mode, mutually exclusive with `--query`:

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" --profile staging get-entities --entity-type work_items --search 'login timeout' --fields id,name,subtype --limit 20 --offset 0
```

Only `work_items` supports this CLI search mode. The `text_search` parameter is
documented in ValueEdge latest; verify deployment support. Rejection does not
trigger a BK/name-filter fallback. Other entity collections reject `--search`.

### Create from a field object

After inspecting required fields and reference types, save this example as
`story.json` outside the plugin's source directories. Replace reference IDs with
read-verified workspace IDs; your workspace may require additional fields.

```json
{
  "name": "Investigate sign-in latency",
  "description": "<html><body><p>Investigate sign-in latency.</p></body></html>",
  "parent": {"type": "feature", "id": "3011"}
}
```

**Only after explicit user intent authorizes creation:**

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" --profile staging create-entity --entity-type stories --data-file /path/to/story.json
```

The file is one field object, not `{"data":[...]}`. Generic writes preserve raw
values and relationship objects; no Markdown conversion, phase shorthand mapping,
acceptance-criteria rendering, tag creation, or workflow remediation is performed.
Use convenience commands when those transformations are desired.

### Update only selected fields

Save as `update.json`, using a workspace-user ID confirmed by a read:

```json
{
  "name": "Investigate and document sign-in latency",
  "owner": {"type": "workspace_user", "id": "1001"}
}
```

**Only after explicit user intent authorizes this target update:**

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" --profile staging update-entity --entity-type stories --entity-id 912 --data-file /path/to/update.json
```

Omitted fields stay omitted. An advertised current lock stamp is fetched if the
file omits it. To preserve a reviewed version, include its nonnegative integer
`client_lock_stamp`; it is sent unchanged, never refreshed after a conflict.
An explicit stamp is rejected if metadata lacks support. An update without stamp
support is labeled unprotected. Failed stamp prerequisite reads block mutation.

### Interpret mutation and verification separately

Successful verified write, abbreviated output:

```json
{
  "ok": true,
  "mutation": {"outcome": "succeeded", "entity_id": "912"},
  "verification": {"read_ok": true, "matched": true}
}
```

If the write succeeded but its read-back was denied, output instead includes:

```json
{
  "ok": false,
  "mutation": {"outcome": "succeeded", "entity_id": "912"},
  "verification": {"read_ok": false, "matched": false, "status": 403},
  "error": "Write may have succeeded but could not be verified; do not retry blindly"
}
```

The second result exits nonzero **without undoing the write**. Inspect the target
with an authorized read; do not issue a second create/update blindly. A lost
response or malformed mutation body reports `mutation.outcome: unknown`. Raw
failure diagnostics are not emitted. Neither HTTP success nor a successful GET
alone proves that fields were applied: identity, readable fields, value matching,
and complete reference collections must also verify.

## Fetch entities

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" get-work-item --entity-id 1013024
uv run "$SKILL_ROOT/scripts/octane_client.py" get-defect --entity-id 2045
uv run "$SKILL_ROOT/scripts/octane_client.py" get-story --entity-id 912
uv run "$SKILL_ROOT/scripts/octane_client.py" get-feature --entity-id 3011
uv run "$SKILL_ROOT/scripts/octane_client.py" get-defect --entity-id 2045 --fields "id,name,severity"
```

## Search

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" search-all --query "login timeout"
uv run "$SKILL_ROOT/scripts/octane_client.py" search-all --query "severity={id='list_node.severity.critical'}" --limit 20
```

## Create and update

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" create-defect \
  --name "Login page 500 error" \
  --description "Steps to reproduce: ..." \
  --severity "list_node.severity.high" \
  --priority "list_node.priority.urgent"

uv run "$SKILL_ROOT/scripts/octane_client.py" create-defect \
  --name "[TM] Missing authorization allows cross-tenant file access" \
  --description "<html><body><h2>Threat Summary</h2><p>...</p><h2>Risk Rating</h2><p>CVSS Vector: CVSS:3.1/...</p><p>Base Score: 8.1</p></body></html>" \
  --severity "High" \
  --security-source "Threat Model" \
  --parent-feature-id "12345" \
  --owner-id "1001" \
  --target-release-id "2002" \
  --cvss-score "8.1" \
  --cvss-vector "CVSS:3.1/AV:N/AC:L/..."

uv run "$SKILL_ROOT/scripts/octane_client.py" create-story \
  --name "As a user I want SSO" \
  --description "Acceptance criteria: ..."

uv run "$SKILL_ROOT/scripts/octane_client.py" create-story-under-feature \
  --entity-id 3011 \
  --name "As a user I want SSO" \
  --description "Users need to sign in with the corporate identity provider." \
  --acceptance-criteria "Given a valid corporate account, when I sign in, then I am authenticated" \
  --acceptance-criteria "Given an invalid account, when I sign in, then I see a clear error"

uv run "$SKILL_ROOT/scripts/octane_client.py" update-story \
  --entity-id 912 \
  --description "Users need to sign in with the corporate identity provider." \
  --acceptance-criteria "Given a valid corporate account, when I sign in, then I am authenticated" \
  --acceptance-criteria "Given an invalid account, when I sign in, then I see a clear error"

uv run "$SKILL_ROOT/scripts/octane_client.py" list-phases --entity defect
uv run "$SKILL_ROOT/scripts/octane_client.py" update-defect --entity-id 2045 --phase "phase.defect.fixed"
uv run "$SKILL_ROOT/scripts/octane_client.py" update-defect --entity-id 2045 --phase fixed
uv run "$SKILL_ROOT/scripts/octane_client.py" update-defect --entity-id 2045 --severity "list_node.severity.critical"
uv run "$SKILL_ROOT/scripts/octane_client.py" update-story-status --entity-id 912 --phase "phase.story.inprogress"

uv run "$SKILL_ROOT/scripts/octane_client.py" update-feature-security \
  --entity-id 3011 \
  --security-assessment "Threat modelling required; use standard STRIDE review." \
  --security-impact-level "list_node.security_impact.high"
```

`update-feature-security` reads the feature first, sends `client_lock_stamp`, updates
`Security Assessment` (`security_assessment_udf`) and/or `Security Impact` (`security_impact_f_udf`), and returns a verified snapshot.
If field-name resolution fails for a workspace, configure
`OCTANE_SECURITY_ASSESSMENT_FIELD` and `OCTANE_SECURITY_IMPACT_LEVEL_FIELD` in `.env`.

## Tags

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" list-tags --query "triaged" --limit 20
uv run "$SKILL_ROOT/scripts/octane_client.py" add-tag --entity-id 1013024 --tag "triaged"
uv run "$SKILL_ROOT/scripts/octane_client.py" add-tag --entity-id 1013024 --entity-type defect --tag "customer-commitment" --no-create
```

`add-tag` preserves existing tags, creates the workspace tag if missing unless
`--no-create` is supplied, sends `client_lock_stamp`, and returns a verified
snapshot when possible.

## Comments

Octane stores comment text as HTML (for example, `<html><body>\n<p>Fixed in build 42</p> \n</body></html>`). The CLI automatically formats plain text passed with `--text` into this Octane-compatible HTML envelope.

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" create-comment \
  --entity-id 2045 --entity-type defect --text "Fixed in build 42"

uv run "$SKILL_ROOT/scripts/octane_client.py" read-comment --entity-id 2045
uv run "$SKILL_ROOT/scripts/octane_client.py" read-comment --entity-id 2045 --limit 25
```

## Quality / testing

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" get-manual-test --entity-id 5001
uv run "$SKILL_ROOT/scripts/octane_client.py" get-suite-runs --entity-id 7001 --limit 50
uv run "$SKILL_ROOT/scripts/octane_client.py" get-run-history --entity-id 8001
uv run "$SKILL_ROOT/scripts/octane_client.py" get-run-history --limit 25
```

## Feature hierarchy

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" get-story-parent-feature --entity-id 912
uv run "$SKILL_ROOT/scripts/octane_client.py" list-feature-items --entity-id 3011
```

## Work Items

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" list-work-items
uv run "$SKILL_ROOT/scripts/octane_client.py" list-work-items --user-email "alice@example.com"
uv run "$SKILL_ROOT/scripts/octane_client.py" list-work-items --retry-on-empty
```

## Tasks

```bash
uv run "$SKILL_ROOT/scripts/octane_client.py" list-tasks --entity-id 1013024
uv run "$SKILL_ROOT/scripts/octane_client.py" add-task \
  --entity-id 1013024 \
  --name "Test that it all works" \
  --owner-id 1003
```

## Working with Octane URLs

```bash
uv run "$SKILL_ROOT/scripts/octane_url.py" "https://octane.example.com/ui/entity-navigation?p=1001/1002&entityType=work_item&id=42"
uv run "$SKILL_ROOT/scripts/octane_url.py" URL1 URL2 URL3
uv run "$SKILL_ROOT/scripts/octane_url.py" --action update-defect --phase phase.defect.fixed "https://...&id=1013024"
uv run "$SKILL_ROOT/scripts/octane_url.py" --action create-comment --entity-type defect --text "Fixed in build 42" "https://...&id=1013024"
uv run "$SKILL_ROOT/scripts/octane_url.py" --action read-comment "https://...&id=1013024"
uv run "$SKILL_ROOT/scripts/octane_url.py" --action list-feature-items "https://...entityType=feature&id=3011"
uv run "$SKILL_ROOT/scripts/octane_url.py" --action update-feature-security --security-assessment "Threat modelling completed" --security-impact-level "list_node.security_impact.high" "https://...entityType=feature&id=3011"
uv run "$SKILL_ROOT/scripts/octane_url.py" --action create-story-under-feature --name "As a user I want SSO" --description "Users need SSO" --acceptance-criteria "Successful SSO login" "https://...entityType=feature&id=3011"
uv run "$SKILL_ROOT/scripts/octane_url.py" --action update-story --description "Users need SSO" --acceptance-criteria "Successful SSO login" "https://...entityType=story&id=912"
uv run "$SKILL_ROOT/scripts/octane_url.py" --action get-story-parent-feature "https://...entityType=story&id=912"
uv run "$SKILL_ROOT/scripts/octane_url.py" --action list-tasks "https://...&id=1013024"
uv run "$SKILL_ROOT/scripts/octane_url.py" --action add-task --name "Test it" --owner-id 1003 "https://...&id=1013024"
uv run "$SKILL_ROOT/scripts/octane_url.py" --action add-tag --tag "triaged" "https://...&id=1013024"
uv run "$SKILL_ROOT/scripts/octane_url.py" --parse-only "https://...&id=1013024"
```

For `entityType=work_item`, the default fetch is `get-work-item`. Use the
returned `subtype` before switching to defect/story-specific follow-up commands.

URL format:

```text
https://<host>/ui/entity-navigation?p=<shared_space_id>/<workspace_id>&entityType=<type>&id=<entity_id>
```

## Triage workflow

1. Fetch the defect: `uv run "$SKILL_ROOT/scripts/octane_client.py" get-defect --entity-id <ID>`
2. Read the `description` and `comments` fields from JSON.
3. Suggest likely root causes based on logs and reported behavior.
4. Post findings with `create-comment` only if the user asked you to write back.
