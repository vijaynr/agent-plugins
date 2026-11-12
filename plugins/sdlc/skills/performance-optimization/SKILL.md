---
name: performance-optimization
disable-model-invocation: true
description: Optimizes performance in a stack-neutral way across UI, services, data access, storage, batch jobs, CLIs, integrations, and distributed systems. Use when performance requirements, regressions, monitoring signals, or profiling evidence identify a bottleneck.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Performance Optimization

## Overview

Measure before optimizing. Performance work without measurement is guessing, and guessing often adds complexity without improving what matters. Establish a baseline, identify the real bottleneck, fix the smallest useful thing, measure again, and add a guard against regression.

This skill is stack-neutral. Use the profiling, tracing, benchmarking, logging, and monitoring tools already appropriate to the project's technology stack.

## When to Use

- Performance requirements exist: latency, throughput, startup time, memory, CPU, battery, bandwidth, storage, render time, job duration, or cost
- Users, monitoring, or CI report slow behavior or regressions
- A feature handles large data volumes, high traffic, expensive computation, or constrained devices
- Profiling or traces show a bottleneck
- A change risks slower response, rendering, startup, synchronization, migration, or batch processing

**When NOT to use:** Do not optimize without evidence. Fix obvious pathological issues if they are already visible, but avoid speculative micro-optimization.

## Optimization Workflow

```text
1. MEASURE  -> Establish baseline with representative data/environment
2. IDENTIFY -> Find the actual bottleneck
3. FIX      -> Address that bottleneck with the smallest maintainable change
4. VERIFY   -> Re-measure and compare before/after numbers
5. GUARD    -> Add tests, budgets, alerts, or dashboards to prevent regression
```

## Step 1: Measure

Capture numbers before changing code.

Potential measures:

| Area | Example metrics |
|---|---|
| User interaction/UI | first useful render, interaction latency, frame drops, accessibility tree/update cost |
| Service/API | p50/p95/p99 latency, throughput, error rate, queue time, timeout rate |
| Data access | query count, query latency, rows scanned, lock wait, cache hit rate |
| Batch/job/CLI | total duration, per-record cost, memory peak, I/O time, startup time |
| Distributed systems | trace spans, retries, fan-out, queue depth, backpressure, dependency latency |
| Resource usage | CPU, memory, GC/allocator pressure, disk I/O, network I/O, battery, cloud cost |

Use representative inputs and environments. A local microbenchmark is useful for isolating code paths, but production/staging telemetry or realistic load is needed for user-impact claims.

## Step 2: Identify the Bottleneck

Start from the symptom:

```text
What is slow?
├── User-visible interaction/rendering
│   ├── Slow initial display -> profile startup, data fetch, rendering/layout, asset loading
│   ├── Sluggish interaction -> profile event handling, main-thread/UI-thread work, re-render/re-layout
│   └── Jank/stutter -> profile frame timing, expensive drawing/layout, synchronous work
├── Service/API/integration
│   ├── Single operation slow -> trace request path, profile handlers, inspect dependency calls
│   ├── All operations slow -> check CPU, memory, connection pools, thread pools, saturation
│   └── Intermittent latency -> check locks, GC/allocator pauses, retries, queues, noisy dependencies
├── Data/storage
│   ├── Many small calls -> look for N+1/fan-out patterns
│   ├── Slow query/search -> inspect plan/indexes/scan volume
│   └── Large payload -> check projection, pagination, compression, serialization
└── Batch/CLI/background work
    ├── Startup slow -> profile initialization and dependency loading
    ├── Per-item slow -> benchmark loop body and I/O
    └── Memory growth -> heap/allocation/profile retained objects or unbounded buffers
```

Do not change the system until the bottleneck is specific enough to explain the symptom.

## Common Bottleneck Patterns

### Unbounded Work

Bad pattern: loading, rendering, exporting, scanning, or processing everything when only a bounded subset is needed.

Fix options:

- Pagination, streaming, chunking, or virtualized rendering
- Server-side filtering/projection
- Backpressure and bounded queues
- Limits with explicit user feedback
- Incremental processing with checkpoints

### N+1 / Fan-Out Calls

Bad pattern: one call to fetch a list, then one call per item for related data.

Fix options:

- Batch fetch
- Join/include/preload according to the data technology
- Cache stable lookups
- Denormalize carefully when read patterns justify it
- Change contract to return needed related data in one bounded call

### Missing or Wrong Indexing / Lookup Strategy

Symptoms: high scan counts, slow filters/sorts, lock contention, or expensive repeated lookups.

Fix options:

- Add the right index/search structure/cache for the access pattern
- Change query shape to use existing indexes
- Avoid sorting/filtering huge result sets in memory when the storage engine can do it
- Validate write overhead and migration risk before adding indexes or materialized views

### Expensive Serialization or Payloads

Symptoms: large responses/files/messages, high CPU in encode/decode, slow network transfer.

Fix options:

- Return only needed fields
- Compress where appropriate
- Use streaming for large payloads
- Avoid repeated serialization/deserialization across layers
- Use a more appropriate format only when measurement justifies the added complexity

### Blocking User-Interaction or Event Loops

Symptoms: frozen UI, slow command responsiveness, missed heartbeats, delayed queue processing.

Fix options:

- Move heavy work off the interaction/event thread
- Break work into chunks/yields
- Use async/non-blocking I/O where the stack supports it
- Precompute/cache expensive stable results
- Reduce unnecessary re-render/re-layout/recomposition work

### Ineffective Caching

Caching helps only when access patterns, invalidation, freshness, and memory bounds are understood.

Before adding a cache, define:

- What key identifies the result?
- How is it invalidated or expired?
- What staleness is acceptable?
- What is the maximum size/cost?
- How will hit rate and correctness be measured?
- What happens under concurrent misses?

### Concurrency and Contention

Symptoms: throughput plateaus, high lock wait, retries, deadlocks, queue buildup.

Fix options:

- Reduce shared mutable state
- Shorten critical sections
- Partition/shard work
- Add backpressure instead of unbounded concurrency
- Tune pools only after measuring saturation and wait time

## Performance Budgets

Define budgets in terms that matter for this product. Examples:

| System | Budget examples |
|---|---|
| UI | first useful render, interaction latency, frame rate, memory, asset size |
| API/service | p95 latency, throughput, timeout rate, dependency fan-out |
| Data | max query count, max rows scanned, query p95, migration duration |
| Batch/CLI | max runtime, startup time, memory peak, per-record throughput |
| Integration | retry rate, queue age, end-to-end processing time |

Budgets should be enforced where practical: tests, benchmarks, CI checks, dashboards, alerts, or release gates.

## Trade-Offs

Performance changes often trade against simplicity, correctness, cost, operability, or compatibility. Document trade-offs explicitly when adding:

- Caches
- Denormalized data
- Concurrency
- Specialized data structures
- Protocol/format changes
- Lazy loading or eventual consistency
- Background processing

If the optimization makes correctness harder to reason about, pair it with stronger tests and observability.

## Verification

After performance work:

- [ ] Baseline measurement exists with environment/input details
- [ ] Bottleneck is identified with profiling, tracing, logs, benchmark, or monitoring evidence
- [ ] Fix targets the measured bottleneck, not a guessed one
- [ ] Before/after numbers show improvement or justify rollback/no-change
- [ ] Correctness tests still pass
- [ ] Performance budget, benchmark, alert, dashboard, or regression test was added/updated when feasible
- [ ] Trade-offs and operational impacts are documented

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This optimization is obvious" | If it was not measured, it may not affect the user-visible bottleneck. |
| "It's fast on my machine" | Local hardware and data rarely match real users or production workloads. |
| "We'll optimize later" | Performance debt compounds; fix measured problems and obvious pathological patterns early. |
| "Caching will solve it" | Caches add invalidation, memory, stampede, and staleness risks. |
| "The framework/runtime/database handles this" | Tools help, but cannot fix unbounded work, poor contracts, or wrong access patterns. |

## Red Flags

- Optimization without before/after data
- Benchmarks with unrealistic data or environment
- Unbounded list/export/render/query/process operations
- N+1 or fan-out patterns on hot paths
- Added cache without invalidation, bounds, or hit-rate measurement
- Performance fix that weakens correctness or security without explicit trade-off
- No regression guard for a previously measured bottleneck
