# ALM Octane Generic CLI: API Contract Research

## Status and evidence limits

T1 research complete; G0 policies explicitly approved for autonomous implementation. This is a source-backed implementation
contract proposal, not implemented behavior. No configured Octane instance or real
keyring was accessed. The deployed server version is unknown. Public documentation
establishes contracts for the cited releases, not universal deployment support.

No production changes or tests were added. TDD's documentation-only exemption
applies to this research task; T2 onward requires RED/GREEN behavior tests.

## Authoritative sources

All REST references below are ALM Octane **26.1**, unless labeled otherwise.

- **E — Entity metadata:** https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/MetadataEntities.htm
- **R — REST features:** https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/MetadataFeatures.htm
- **F — Field metadata:** https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/MetadataFields.htm
- **Q — Query language:** https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/query_Clause.htm
- **P — Paging:** https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/Paging.htm
- **O — Ordering:** https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/order-by.htm
- **S — Field selection:** https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/fields_clause.htm
- **C — Create:** https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/Create_an_Instance.htm
- **U — Update:** https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/Update_an_Instance.htm
- **L — Locking:** https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/Lock.htm
- **T — Keyword search, ValueEdge latest (unversioned):** https://admhelp.microfocus.com/valueedge/en/latest/Online/Content/API/text_search.htm
- **M — MCP tool documentation, ValueEdge latest (unversioned):** https://admhelp.microfocus.com/valueedge/en/latest/Online/Content/AdminGuide/mcp-server-advanced-setup.htm
- **G — Official MCP overview:** https://github.com/opentext/OpenText-Model-Context-Protocol-Server/

E/R expose the REST collection URL and supported methods, not a requirement to
guess a plural. F says: "Only the query clause is supported" for field metadata;
`limit`, `offset`, `total_count`, and `order_by` are not supported there.

M describes `get_filter_metadata` as: "Return the Octane filter query syntax
documentation - operators, value formats, logical connectors, and special tokens."
Its documented inputs are shared-space/workspace IDs, not an entity type. Thus
an operator-discovery REST endpoint is not necessary to match that capability.
The earlier planning concern about needing such an endpoint was too restrictive.
No such endpoint was verified, and none should be invented.

G confirms the seven tools and documents two product guides. It supplies product
documentation, not implementation source establishing a REST translation. M's
examples are useful context, not a guarantee of the deployed MCP schema.

## Capability matrix

Let `W` be the existing selected endpoint plus
`/api/shared_spaces/{space}/workspaces/{workspace}`. The following routes are
workspace-scoped; administration/site-level operations are out of scope.

| CLI command | HTTP contract | Output/constraints | Sources |
|---|---|---|---|
| `get-entity-types` | GET `W/metadata/entities` | Entity metadata with `name`, `features`, available labels/descriptions; `rest.url` maps collection and `rest.methods` indicates supported operations. Do not add ordinary paging parameters without evidence. | E/R |
| `get-entity-field-metadata` | GET `W/metadata/fields`, query `"entity_name EQ ^defect^"` for the exact discovered metadata name | Preserve available `name`, `field_type`, `field_type_data`, `required`, `editable`, `final`, `filterable`, `sortable`, and `selectable`. No synthesized constraints or guessed fallback entities; no metadata limit/offset/order_by. | F |
| `get-filter-metadata` | Proposed composition: bundled Q syntax rules plus GET of exact entity field metadata | Clearly label documented grammar versus workspace-reported field capabilities. Not a server operator-discovery claim. Keep proposed `--entity-type` for field context. Requires G0 approval. | Q/F/M |
| `get-entities` | GET `W/{rest.url}` | Collection `data` array and supplied server totals; one page only. `query`, `fields`, `order_by`, `limit`, `offset`; proposed search uses `text_search` only on explicitly supported collections. | E/R/Q/P/O/S/T |
| `get-entity` | GET `W/{rest.url}/{id}`, optional `fields` | Single entity response in existing request envelope. Preserve legacy printing adapter while new helper returns data. | U/S and existing client |
| `create-entity` | POST `W/{rest.url}`, body `{"data":[{...fields...}]}` | Exactly one record. Documented success 201; extract/validate the one returned ID, then GET it. Preserve any server error evidence. | C |
| `update-entity` | PUT `W/{rest.url}/{id}`, body `{...changed_fields...}` | Plain object, NOT a collection `data` envelope. Documented success 200; read-back required. Current/supplied lock stamp as below. | U/L |

Read/list payloads remain inside the existing outer CLI `data` envelope; do not
flatten or rename existing command outputs. Discovery helpers must distinguish
empty successful metadata from transport/authorization failure. Unsupported
methods fail before mutation. A discovery failure never justifies another host.

## Query, fields, sort, and pagination contracts

- `--query` accepts the native expression, without its outer double-quote pair.
  Wrap it once as required by Q and let `requests` encode the parameter once.
  Reject already outer-quoted input with actionable guidance rather than silently
  double-wrapping it. This convention needs explicit reference examples/tests.
- Example: `--query 'id EQ 1234'` produces the query parameter `"id EQ 1234"`.
  Existing spec shorthand examples using `id=1234` need not be globally rewritten;
  new documentation should prefer the consistently documented `EQ` syntax.
- Operators from Q: `EQ`, `LT`, `GT`, `LE`, `GE`, `IN`, `BTW`; logical `;`, `||`,
  `!`, and parentheses. Operators depend on field type; do not claim all apply
  to every field. Preserve native expressions, special tokens, and references.
- String values use caret delimiters; wildcards use `*`. Q provides escape rules
  and disallows literal-star filtering. Do not generate queries by copying the
  legacy `search_all` helper's undocumented `BK` pattern. Leave that helper alone.
- Metadata query restrictions differ: no OR between metadata query phrases;
  `entity_name` supplies context. F can report `filterable` for actual fields.
- `fields` is comma-separated; server identity/type fields may be added. New
  generic commands omit `fields` when absent (server defaults), rather than
  inheriting subtype convenience field lists. Initial CLI supports flat selection;
  do not advertise recursive expansion as part of this change.
- `order_by` is comma-separated fields; prefix `-` means descending. Examples:
  `id`, `severity,-creation_time`. Proposed default is `id` for stable paging.
  Honor explicit `sortable: false`; missing metadata is not proof of support.
- CLI defaults: limit 50, offset 0. Reject limit <= 0 and offset < 0. Server maximum
  page size is configurable; do not hardcode the MCP documentation's 500 as the
  REST server maximum. Surface server rejection and never truncate silently.
- Return requested page parameters and preserve `total_count` and
  `exceeds_total_count` if supplied. Do not invent totals or auto-fetch more pages.

## Text search: version limitation and proposal

T documents `text_search` as a JSON query-parameter value, e.g.
`{"type":"global","text":"login"}`. Serialize text as JSON, not by inserting it
into a native field query. No need to synthesize wildcard expressions.

T lists: `work_items`, `tests`, `runs`, `run_suite_schedules`,
`run_suite_schedule_runs`, `requirements`, `releases`, `milestones`, `tasks`,
`environments`, `bdd_specs`, `pipelines`, and `comments`.

**Proposed first-release limit:** expose `--search` on `work_items` only; reject it
for other collections, including direct `defects`/`stories`, rather than secretly
switching collections. Keep `--search` and `--query` mutually exclusive per spec.
If the server rejects `text_search`, return a clear unsupported-search error;
never retry with BK or reinterpret it as a name filter. Other failures retain
their actual auth/network/server classification.

The Octane 26.1 and Octane latest text_search URLs returned 404 during research;
this is a documentation availability limitation, NOT proof that those servers
lack search. The ValueEdge latest source is explicit but not release-pinned.
G0 must approve this limited, version-qualified contract or require target-version
documentation first. Similarity/context search and licensing are out of scope.

## Input and targeting policy (CLI design, not server requirements)

- Keep Python 3.10+ and existing profile precedence/session/redirect behavior.
- For new commands validate entity names, metadata collection paths, and all
  scope/entity ID segments before entity requests. Proposed safe segment grammar:
  ASCII `[A-Za-z0-9_][A-Za-z0-9_.-]*`, excluding `.` and `..` and whitespace.
  Reject slash, backslash, colon, percent-encoded input, query/fragment syntax,
  controls, absolute URLs, and leading/trailing padding. No URL decoding tricks.
- IDs remain strings (F), including list-node-style identifiers; do not coerce
  arbitrary IDs to integers. Do not change legacy argument validation globally.
- Resolve exact metadata names or collection names via R, with explicit existing
  known aliases. Unknown names never become guessed plurals. Metadata URL values
  must be safe single collection segments; reject unsupported nested paths.
- Read JSON as UTF-8. Reject malformed/nonstandard JSON, duplicate keys, nonobject
  roots, empty objects, and a top-level collection `data` envelope. A nested
  relationship `data` object is valid and must be preserved.
- Reject top-level `id` on create: this interface creates a server-assigned ID.
  On update, allow only an ID equal to `--entity-id`; strip a redundant matching
  top-level ID from field comparison and reject conflicts. Reject ID-only/stamp-only
  updates. These are conservative CLI rules, not claims about every collection.
- Validate nested JSON references without rewriting field values or guessing entity
  types. Unknown/required/read-only fields are ultimately server-validated; expose
  metadata but do not introduce an incomplete schema engine or strip caller fields.

## Concurrency and field verification policy

- L recommends `client_lock_stamp` for updates and documents HTTP 500 with
  `platform.version_conflict` for stale stamps. Do not only recognize HTTP 409.
- Caller-supplied stamp: preserve it exactly; do not refresh it before PUT. If
  absent and exact entity metadata advertises the field, GET the current stamp
  first and block mutation if that read fails or lacks the advertised stamp.
- If successful exact metadata definitively lacks a stamp field, use a documented
  unprotected update path and label protection unavailable. If metadata fails,
  stop rather than assuming no protection. No automatic refresh/retry after conflict.
- Verify the returned/explicit ID in the same scope and explicitly request supplied
  readable fields. Identity mismatch, missing fields, unreadable fields, or failed
  GET is not verification success. Missing create ID is uncertain, not a reason
  to search by name and possibly verify the wrong record.
- Compare scalar values strictly with JSON type awareness. For references compare
  `(type,id)` identities using F, ignoring response expansion/default fields;
  normalize numeric response IDs to strings only where the value is an ID.
  Multi-references may use F's `{data:[...]}` representation; compare complete
  identity sets when metadata establishes unordered multi-reference semantics.
  A truncated or unknown-order reference result is unverified, not matched.
- Q documents empty string storage as null for nullable string fields; apply that
  one normalization only when metadata establishes nullable string semantics.
  No HTML stripping, case folding, trimming, arbitrary date conversion, or broad
  sanitization equivalence. A changed/sanitized value without a verified rule
  remains a mismatch. Do not infer that a successful GET proves every field applied.
- Exclude transport `id` and `client_lock_stamp` from changed-field equality; stamps
  can advance. Still validate entity identity separately. Omitted fields stay omitted.

### Proposed new-command result states

Keep the established outer `ok`, `data`, optional `status`, `url`, and `error`
conventions. New writes add separate `mutation` and `verification` evidence.

| State | Exit / ok | Required evidence |
|---|---|---|
| Read or validated mutation + matching read-back | 0 / true | Data; write includes ID, mutation success, verification read/match success. |
| Local validation / prerequisite failure | nonzero / false | Actionable error; no mutation attempted. |
| Server rejects mutation | nonzero / false | Actual safe status/error; mutation rejection and no automatic retry. |
| Mutation response received, read-back fails/mismatches | nonzero / false | Preserve mutation success/ID; report failed or unverified fields/read, may-have-succeeded/no-blind-retry guidance. |
| Mutation transport failure or missing returned ID | nonzero / false | Explicit unknown or incomplete mutation outcome; no replay. |

Error fixtures must prove no credential sentinel appears in serialized outputs.
Do not dump raw stack traces or authorization headers. Preserve server error codes
needed to diagnose conflicts without changing legacy command error contracts.

## Baseline and environment evidence

- Windows; development `python --version`: **3.11.12**. Existing client PEP 723
  and smoke grammar contract target Python **3.10+**. No Python 3.10 runtime
  execution was performed; workspace smoke tests cover minimum-version syntax.
- `python -m pytest skills/alm-octane/tests -q` failed before collection because
  the default Python lacks pytest. Used the already documented isolated runner;
  no project dependencies or environment files were changed.
- From `plugins/octane`:
  `uvx --from pytest --with requests --with python-dotenv --with keyring pytest skills/alm-octane/tests -q`
  → **106 passed, 1 skipped**, exit 0. The existing skip is the Windows/POSIX
  permission-bit test; it was not added or disabled by this task.
- From repository root:
  `uvx --from pytest pytest tests plugins/okf/tests -q`
  → **4 failed, 324 passed, 2 skipped**, exit 1. `tests/test_agents_helper.py`
  defaulted to `bash` because Git is not installed at its default Program Files
  location; child Windows PATH resolution selected WSL Bash. WSL lacked Python,
  causing validation/list/status/missing-Copilot checks to fail.
- Environment-only correction using the existing test override (Git Bash syntax):
  `GIT_BASH='C:\Users\vnr\AppData\Local\Programs\Git\bin\bash.exe' uvx --from pytest pytest tests plugins/okf/tests -q -rs`
  → **328 passed, 2 skipped**, exit 0. Existing OKF skips report symlinks unavailable.
  This path is local evidence only; other developers must set their own Git Bash
  path when nonstandard. No tests, helper scripts, or shell defaults were changed.
- Dependency setup may access the package index; tests use fake service/keyring
  boundaries. No new behavior test or runtime build exists for this docs-only task.
  Repository smoke validation covers compilation and Python 3.10 grammar.
- Explicit build-equivalent check: in-memory `compile` and
  `ast.parse(feature_version=(3, 10))` succeeded for all **4** Octane scripts,
  exit 0; no bytecode was written. `git diff --cached --check` also passed.

## G0 review decisions

1. Approve source-cited bundled query grammar plus live contextual field metadata
   for `get-filter-metadata`, explicitly labeled as two different provenance types.
   This clarifies the existing spec; it is not a claim of a server operator endpoint.
2. Approve `--search` limited to `work_items` via documented ValueEdge `text_search`,
   with version qualification/unsupported-server errors, or provide target-version
   documentation before search implementation.
3. Approve the conservative input, concurrency, and verification policies above.

The user approved these proposals and autonomous T2–T10 implementation, and
explicitly authorized committing the plugin `SPEC.md` despite its ignore rule.
No live Octane access is authorized.
