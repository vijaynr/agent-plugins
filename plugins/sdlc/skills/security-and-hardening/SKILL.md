---
name: security-and-hardening
disable-model-invocation: true
description: Hardens code against vulnerabilities in a stack-neutral way. Use when handling untrusted input, authentication, authorization, sensitive data, persistence, files, external integrations, or privileged operations.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Security and Hardening

## Overview

Security is a design constraint, not a final review step. Treat every external input as hostile, every secret as sacred, every authorization decision as explicit, and every external dependency as a trust boundary.

This skill is technology-neutral. Apply the patterns using the framework, language, and infrastructure already present in the project.

## When to Use

- Accepting input from users, services, files, messages, CLIs, webhooks, or AI/LLM output
- Implementing authentication, authorization, sessions, roles, or permissions
- Storing, processing, or transmitting sensitive data
- Integrating with external services
- Adding file upload/download, import/export, callbacks, or background jobs
- Handling money movement, PII, secrets, privileged operations, or destructive actions

## Process: Threat Model First

Before hardening, identify what can go wrong:

1. **Map trust boundaries.** Where does untrusted data enter or leave the system?
2. **Name assets.** Credentials, PII, financial data, business records, admin actions, availability, integrity.
3. **Identify actors.** Anonymous users, authenticated users, admins, services, CI jobs, compromised dependencies.
4. **Run STRIDE over each boundary:**

| Threat | Ask | Typical mitigations |
|---|---|---|
| Spoofing | Can someone impersonate another actor? | Strong authentication, signed requests, mTLS/service identity |
| Tampering | Can data be altered? | Integrity checks, parameterized queries, immutable audit records |
| Repudiation | Can actions be denied later? | Audit logs with actor, action, target, time, correlation ID |
| Information disclosure | Can data leak? | Encryption, redaction, field allowlists, generic errors |
| Denial of service | Can it be overwhelmed? | Rate limits, quotas, timeouts, size caps, backpressure |
| Elevation of privilege | Can rights be expanded? | Authorization checks, least privilege, scoped tokens |

5. **Write abuse cases.** For every important use case, write at least one misuse case and verify it is blocked.

## Boundary Rules

### Always Do

- Validate and normalize untrusted input at the boundary.
- Authorize every privileged action on the server/service side.
- Use parameterized queries or safe persistence APIs for user-influenced data.
- Encode or escape output according to the target context.
- Use least privilege for users, services, jobs, and tokens.
- Keep secrets out of source control, logs, telemetry, and error messages.
- Use secure transport for external communication.
- Add timeouts, retries with bounds, and payload size limits for external calls.
- Log security-relevant events without sensitive values.
- Run the project's dependency and license/security checks before release.

### Ask First

- New authentication or authorization flows
- New sensitive data collection or retention
- New external service integration
- File upload/download/import/export surfaces
- Changes to permission models, roles, scopes, or service accounts
- Changes to rate limits, throttling, or abuse controls
- Disabling or weakening security controls

### Never Do

- Commit secrets, tokens, passwords, private keys, or production credentials.
- Log secrets, auth headers, session IDs, full payment data, or unnecessary PII.
- Trust client-side validation as a security boundary.
- Build SQL/queries/shell commands by concatenating untrusted input.
- Expose stack traces or internal details to untrusted users.
- Disable TLS/certificate validation except in controlled local test harnesses.
- Store auth/session credentials in client-readable storage unless the platform security model explicitly requires it and risks are accepted.
- Execute untrusted code or commands without sandboxing and explicit approval.

## Common Vulnerability Patterns

### Injection

Risk: untrusted data changes the meaning of a query, command, expression, or template.

Mitigations:

- Prefer parameterized APIs and safe builders.
- Avoid shell invocation; if unavoidable, pass arguments as structured arrays, not strings.
- Treat template/expression languages as code execution surfaces.
- Validate allowlisted values for identifiers such as sort fields, table names, paths, or command names.

### Broken Authentication

Mitigations:

- Use established authentication libraries/protocols.
- Store passwords only with modern password hashing designed for credentials.
- Rotate and scope tokens.
- Expire sessions appropriately.
- Protect reset and enrollment flows as authentication flows.
- Rate-limit credential attempts and recovery flows.

### Broken Access Control

Mitigations:

- Check authorization at the point of action, not just at navigation/UI entry points.
- Verify ownership/tenant/project/workspace boundaries for every resource access.
- Deny by default.
- Keep role/scope checks close to the operation they protect.
- Add negative tests for cross-user and cross-tenant access.

### Sensitive Data Exposure

Mitigations:

- Return allowlisted response fields only.
- Redact sensitive fields in logs and telemetry.
- Encrypt sensitive data where required by policy/regulation.
- Minimize retention and collection.
- Use generic external errors and detailed internal diagnostics.

### Server-Side Request Forgery / Unsafe Outbound Calls

Risk: user-influenced destinations can target internal services or metadata endpoints.

Mitigations:

- Allowlist schemes and hosts.
- Reject private, loopback, link-local, and metadata addresses.
- Disable or tightly control redirects.
- Set strict timeouts and size limits.
- Use an egress proxy/filter for high-risk surfaces.

### File and Path Handling

Mitigations:

- Restrict file types and sizes.
- Store uploads outside executable paths.
- Generate server-side names; do not trust supplied paths.
- Normalize and validate paths before use.
- Scan or quarantine untrusted files where appropriate.

### Supply Chain Risk

Mitigations:

- Prefer standard library and existing project dependencies.
- Review dependency health, provenance, license, and known vulnerabilities.
- Pin or lock versions according to ecosystem best practice.
- Use reproducible installs/builds in CI.
- Treat generated code and AI output as untrusted until reviewed.

## Verification

For security-sensitive changes:

- [ ] Trust boundaries and assets are identified.
- [ ] Abuse cases are documented or covered by tests.
- [ ] Input validation exists at all external boundaries.
- [ ] Authorization is enforced for privileged actions and resource access.
- [ ] Secrets are not present in source, logs, telemetry, or test fixtures.
- [ ] Error messages do not leak internals to untrusted users.
- [ ] External calls have allowlists/timeouts/size limits where needed.
- [ ] Dependency/security checks appropriate to the project have been run.
- [ ] High-risk or irreversible changes received explicit approval.
