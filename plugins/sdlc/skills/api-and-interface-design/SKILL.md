---
name: api-and-interface-design
disable-model-invocation: true
description: Guides stack-neutral API and interface design. Use when designing service APIs, module boundaries, file formats, events, schemas, component contracts, CLI interfaces, or any public boundary between systems.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# API and Interface Design

## Overview

Design stable, well-documented interfaces that are hard to misuse. An interface is any contract where one component, service, team, process, or user-facing tool depends on another. This includes HTTP APIs, RPC services, GraphQL schemas, events, command-line interfaces, SDKs, modules, UI component inputs, database-facing contracts, and file formats.

This skill is stack-neutral. Follow the project's existing protocols, naming conventions, serialization formats, versioning policy, and compatibility requirements.

## When to Use

- Designing or changing public endpoints, events, schemas, commands, modules, or SDK surfaces
- Defining contracts between frontend/backend, services, packages, teams, plugins, or external consumers
- Changing inputs, outputs, errors, defaults, ordering, timing, or side effects that consumers can observe
- Creating contracts that will be documented, tested, versioned, or depended on outside the implementation

## Core Principles

### Hyrum's Law

> With enough users, every observable behavior of an interface will be depended on by somebody, regardless of whether it was documented.

Design implications:

- Be intentional about every observable behavior.
- Do not leak implementation details through names, timing, ordering, errors, or data shapes.
- Prefer additive evolution over breaking changes.
- Plan deprecation and migration before consumers depend on the interface.

### Contract First

Define the contract before implementation:

```text
Interface: Create item
Input contract:
  - title: required non-empty text
  - description: optional text
Output contract:
  - id: system-generated stable identifier
  - title: normalized title
  - status: default initial status
  - createdAt: server/system creation timestamp
Error contract:
  - validation error for invalid input
  - authorization error for insufficient permissions
  - conflict error when uniqueness constraints are violated
Compatibility:
  - adding optional fields is allowed
  - removing or changing field meanings requires migration/deprecation
```

The exact representation may be OpenAPI, protobuf, JSON Schema, GraphQL SDL, IDL, typed interfaces, Markdown, command help text, or project-specific documentation.

### Consistent Error Semantics

Pick one error strategy per interface family and use it consistently:

- Machine-readable error code
- Human-readable message safe for the audience
- Optional details for validation or diagnostics
- Stable mapping to transport-specific status, exit code, exception type, or event outcome
- No leaking secrets, stack traces, internal table names, or implementation details

Do not mix incompatible patterns in the same interface family: sometimes null, sometimes exception, sometimes embedded error object, sometimes partial success without explanation.

### Validate at Boundaries

Validate external or untrusted input at system boundaries:

- User input
- Incoming requests/messages/events/files
- CLI arguments and environment/configuration
- Third-party service responses
- Data crossing trust boundaries
- Deserialized persisted data when schema/version may vary

Avoid scattering duplicate validation through internal functions that receive already-validated domain objects. Internal assertions are fine for invariants, but boundary validation owns input trust.

### Prefer Addition Over Modification

Safe changes are usually additive:

- Add optional input fields
- Add output fields consumers can ignore
- Add new enum values only when consumers are designed to handle unknown values
- Add new endpoints/commands/events without changing existing semantics

Breaking changes require explicit migration/deprecation planning:

- Removing fields or commands
- Changing field type, meaning, units, defaults, ordering, or nullability
- Making optional input required
- Changing error semantics
- Changing idempotency, retry, authorization, or side-effect behavior

### Make Misuse Hard

A good interface guides correct use:

- Names reveal intent, units, and lifecycle
- Required and optional inputs are clear
- Defaults are documented and safe
- Idempotency and retry behavior are explicit
- Pagination/streaming limits are explicit for collections
- Security and authorization expectations are part of the contract
- Unknown/forward-compatible values have defined behavior

## Design Checklist

### Identify Consumers

Before changing an interface, list known and likely consumers:

- Internal modules/packages
- Other services or plugins
- UI clients
- Automation/CLI users
- External customers/integrations
- Tests, scripts, dashboards, data pipelines, or documentation examples

If you cannot identify consumers, use dependency search, logs, metrics, repository references, API gateway data, package downloads, or stakeholder input before assuming the surface is unused.

### Define Compatibility Policy

Document:

- Is this private, internal, partner-facing, or public?
- What changes are backward compatible?
- How are incompatible changes announced?
- How long are old contracts supported?
- How do consumers detect supported versions/capabilities?

### Define Collection Behavior

For list/search/stream interfaces, specify:

- Pagination, streaming, or batching model
- Default and maximum limits
- Sorting and stability guarantees
- Filtering semantics
- Empty result behavior
- Consistency expectations under concurrent changes

### Define Security Behavior

Specify:

- Authentication and authorization requirements
- Tenant/user scoping
- Data classification and redaction rules
- Rate limits or abuse controls
- Audit/logging expectations
- Error behavior that does not leak sensitive information

### Define Failure Behavior

Specify:

- Validation failures
- Not found / missing dependency behavior
- Conflict/concurrency behavior
- Timeout/retry/idempotency behavior
- Partial success and compensation behavior
- External dependency failure behavior

## Common Interface Families

Use project conventions for each family. These are examples, not defaults.

| Interface family | Design concerns |
|---|---|
| HTTP/REST | resources, methods, status mapping, cache semantics, pagination |
| GraphQL | schema evolution, nullable fields, resolver cost, error shape |
| RPC/gRPC | proto compatibility, deadlines, retries, streaming, status codes |
| Events/messages | schema versioning, ordering, deduplication, idempotency, replay |
| CLI | arguments, flags, exit codes, stdout/stderr contract, machine-readable output |
| SDK/module | types, exceptions/results, lifecycle, thread/concurrency safety |
| UI component | props/inputs, events/callbacks, accessibility contract, controlled/uncontrolled state |
| Frontend API integration | DTOs, view models, mappers, service boundaries, state ownership, loading/error semantics |
| File format | schema version, encoding, backward/forward compatibility, validation |

## Frontend API Integration

When a UI consumes an API, design the API-to-UI contract explicitly instead of wiring endpoint responses directly into components.

Recommended workflow:

1. Detect project conventions: framework version, state/data-fetching pattern, date/time handling, error handling, test runner, and generated-client conventions.
2. Discover the contract from OpenAPI/GraphQL/protobuf/schema files, existing DTOs, backend code, or documented endpoint behavior.
3. Keep wire DTOs distinct from UI view models when the API shape differs from presentation needs.
4. Add mappers at the boundary. Parse, normalize, and validate external data before it enters presentation state.
5. Put API calls behind the project's existing service/client abstraction; do not fetch directly from leaf UI components unless that is the established pattern.
6. Define loading, empty, validation, authorization, retryable failure, and terminal failure semantics as part of the contract.
7. Add contract, mapper, service, component, or integration tests at the smallest level that proves the behavior.

Record consequential API/UI contract decisions in the SDLC design or implementation plan, including open questions and compatibility risks.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We'll document the interface later" | Consumers start depending on behavior as soon as it exists. |
| "This is internal" | Internal consumers are still consumers; contracts prevent hidden coupling. |
| "Nobody uses that undocumented behavior" | Hyrum's Law says observable behavior becomes a dependency. Verify before changing. |
| "We'll version when we need to" | Without a compatibility policy, breaking changes become emergency migrations. |
| "Pagination/limits can wait" | Unbounded collection interfaces fail when data grows. |
| "Third-party data has the shape we expect" | External responses are untrusted and must be validated before use. |

## Red Flags

- Inconsistent error formats or exit/status semantics
- Unbounded list/search/export operations
- Breaking changes without deprecation/migration plan
- Public contracts that expose implementation names or storage details
- Required fields added to existing inputs
- Consumers expected to parse human-readable error text
- Unknown enum/status values not handled
- Third-party or cross-boundary data used without validation

## Verification

After designing or changing an interface:

- [ ] Inputs, outputs, errors, side effects, and compatibility rules are documented in the project’s preferred contract format
- [ ] Known consumers and migration impact are identified
- [ ] Validation occurs at trust boundaries
- [ ] Collection operations have limits, pagination, batching, or streaming semantics
- [ ] Error behavior is consistent and safe
- [ ] Changes are additive or have an explicit deprecation/migration plan
- [ ] Contract tests, schema checks, or compatibility tests cover the interface where feasible
- [ ] Documentation/examples are updated alongside implementation
