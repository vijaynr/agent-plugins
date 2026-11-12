---
name: observability-and-instrumentation
disable-model-invocation: true
description: Instruments code so production behavior is visible and diagnosable in a stack-neutral way. Use when adding logging, metrics, tracing, alerts, or shipping behavior that must be operated in production.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Observability and Instrumentation

## Overview

Observability lets operators answer what happened, where, why, and who was affected without reading code or reproducing production. Instrumentation is part of the feature, not an afterthought.

This skill is stack-neutral. Use the project's existing logging, metrics, tracing, alerting, and dashboard tools.

## When to Use

- Shipping code that runs in production
- Adding external service calls, queues, jobs, APIs, CLIs, or scheduled work
- Adding retry, timeout, fallback, or error-handling behavior
- Debugging production issues with insufficient telemetry
- Creating or changing alerts, dashboards, or runbooks

## Start with Questions

Before adding signals, write 2-4 questions an on-call person will ask, for example:

- Is the feature receiving traffic/work?
- Is it succeeding or failing?
- How slow is it for users or downstream systems?
- Which dependency, tenant, operation, or queue is causing impact?
- Can we correlate one user's request across components?

Every log, metric, trace, dashboard, and alert should answer one of those questions.

## Signal Types

### Logs: Why did this happen?

Use structured logs for discrete events and decisions.

Include:

- Stable event name
- Timestamp from logging system
- Correlation/request/trace ID
- Actor or sanitized subject identifier when appropriate
- Operation/action
- Outcome and error category
- Dependency name/status/latency where relevant

Never include secrets, tokens, passwords, auth headers, or unnecessary PII.

### Metrics: Is something wrong?

Use metrics for aggregate health and alerting.

Recommended patterns:

- **RED** for services/endpoints/jobs: Rate, Errors, Duration
- **USE** for resources: Utilization, Saturation, Errors
- Histograms/percentiles for latency, not averages only
- Low-cardinality labels only: route template, operation, status class, dependency name

Avoid unbounded labels such as user IDs, emails, request IDs, raw URLs, or full error messages.

### Traces: Where did time go?

Use tracing across boundaries:

- Accept or create trace context at entry points.
- Propagate context through outbound calls and asynchronous work.
- Add spans around meaningful operations.
- Attach safe attributes that help filtering.
- Avoid secrets or PII in span attributes.

### Alerts: Who needs to act?

Alerts should be symptom-based and actionable.

Good alert sources:

- Elevated error rate
- Sustained high latency
- Queue/backlog age
- Failed scheduled job
- SLO burn rate
- Dependency outage impacting users

Avoid paging on causes without user impact unless the team has explicitly accepted that policy.

## Instrumentation Process

1. **Define on-call questions.** What must be diagnosable?
2. **Identify boundaries.** Entry points, dependencies, queues, storage, scheduled jobs.
3. **Add structured logs.** Log significant state transitions and failure decisions.
4. **Add metrics.** Count work, errors, duration, saturation, and queue/backlog health.
5. **Add tracing.** Propagate correlation across components.
6. **Add dashboards.** Make the common questions visible.
7. **Add alerts.** Page only when action is required.
8. **Write/update runbooks.** Every alert needs a first diagnostic step.
9. **Verify telemetry.** Force success and failure paths in a safe environment.

## Error and Event Taxonomy

Use stable categories rather than arbitrary messages:

```text
operation_started
operation_succeeded
operation_failed
validation_rejected
authorization_denied
dependency_timeout
dependency_error
retry_scheduled
fallback_used
```

Names should be consistent across the project.

## Verification

For a new production behavior:

- [ ] On-call questions are written down.
- [ ] Logs include correlation IDs and stable event names.
- [ ] Metrics capture rate, errors, and duration where relevant.
- [ ] Trace/correlation context crosses service or async boundaries.
- [ ] Sensitive data is redacted/omitted from telemetry.
- [ ] Dashboards answer the on-call questions.
- [ ] Alerts are actionable and link to runbooks.
- [ ] Success and failure telemetry was verified in a safe environment.

For detailed checklist form, see `references/observability-checklist.md`.
