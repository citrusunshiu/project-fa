# ADR-0005: One platform contract for every service

- **Status:** Proposed
- **Date:** 2026-11-01
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

Experiments compare behaviour across services: how a retry storm spreads, where a deadline gets lost, which consumer double-applies an event. That only works if every service behaves the same way at its edges, whatever its language. Without a shared contract, each service invents its own timeouts and retries, and every experiment measures the inconsistencies instead of the design.

## Options

### Option A: Each service decides for itself

The common failure mode of polyglot systems. Experiments become unreadable.

### Option B: Put it all in the mesh

Let the service mesh handle retries, timeouts and mutual TLS. It works for transport concerns, but the mesh can't see idempotency keys, deadlines inside a request, or which writes are safe to retry. Mesh retries stacked on application retries are a classic source of retry storms.

### Option C: A sidecar runtime (Dapr)

Building blocks for state, pub/sub and retries behind a sidecar API. It solves the consistency problem by hiding the mechanisms, and the mechanisms are what this repository exists to learn and measure.

### Option D: A written contract, implemented once per language template

A short list of rules every service meets, implemented in each language's service template and checked by tests.

## Decision

Option D. The contract is the [platform contract](../architecture/platform-contract.md): health and readiness endpoints with graceful shutdown, OpenTelemetry, deadlines and timeouts, one budgeted retry policy, idempotency keys stored with their effects, protobuf contracts, a store switch, and fault endpoints gated by flags. The mesh handles mutual TLS only, with mesh-level retries off.

## Lab stance and production stance

- **Lab stance:** the contract makes nine languages comparable, and it is itself a subject of experiments: retry budgets against no budgets, deadlines against none.
- **Production stance:** the same idea is usually called a paved road or golden path, delivered as service templates and shared libraries. In a company with two or three languages it would be a library per language plus mesh policy.

## Consequences

- Every language template must implement the whole contract before its first service ships.
- Contract changes are expensive: they touch every template. The contract stays short.
- Retry and timeout values are defaults, changed only with an experiment report that justifies the change.

## What would change my mind

If a contract rule causes more incidents than it prevents in experiments (a retry budget that starves legitimate retries, say), the rule changes.

## How we'd know

Phase 1's retry-storm experiment runs with and without the retry budget and deadlines. If the contract's version doesn't contain the storm, the contract is wrong.
