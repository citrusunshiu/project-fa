# ADR-0006: gRPC inside, REST at the edge behind one BFF per client type

- **Status:** Proposed
- **Date:** 2026-11-01
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

Services talk to each other at high rates and across nine languages, so internal APIs need a strict, generated contract with deadlines. The clients (web, Android, iOS) can't be updated in step with the backend: old app versions stay in use for months. The edge API has to version well and be shaped for each client's screens.

## Options

### Option A: REST and JSON everywhere

Universal, but hand-written clients in nine languages, no deadline propagation, and loose contracts.

### Option B: gRPC everywhere, including the clients

Strong contracts, but browsers need a proxy for gRPC, and mobile clients get a schema shaped for services rather than screens.

### Option C: GraphQL at the edge

One flexible endpoint, clients choose their fields. It is well suited to many clients with different needs. It would teach this project less than the alternatives.

### Option D: gRPC inside; REST and JSON at the edge, through one backend-for-frontend per client type

Services expose gRPC with protobuf. A web BFF and a mobile BFF aggregate those services into screen-shaped REST endpoints, own the edge versioning, and shield services from client release cycles.

### Option E: Connect

Connect speaks the gRPC protocol and plain HTTP/JSON from the same handlers, so browsers can call it directly. Worth adopting if browsers ever need to call services directly.

## Decision

Option D. Protobuf schemas live in one directory, managed with `buf`, with lint and breaking-change checks in CI. Each BFF publishes a versioned OpenAPI document that its client repository pins.

## Lab stance and production stance

- **Lab stance:** BFFs make the client-versioning problem explicit and testable: old client versions keep working against a newer BFF, and contract tests between client and BFF catch breaks before release.
- **Production stance:** BFFs are common at companies with distinct web and mobile teams. Many would choose GraphQL, often federated, for the same job. Both are reasonable; the BFF is simpler to operate at this size.

## Consequences

- Every edge change goes through a BFF, which adds a hop and one more service per client type.
- The BFF fan-out is a latency question in its own right, measured in Phase 8.
- Clients never call internal services, so internal APIs can change freely behind the BFFs.

## What would change my mind

If the BFFs turn into thin pass-throughs, so that most endpoints just mirror one service, the extra hop isn't buying anything.

## How we'd know

Count the BFF endpoints that call more than one service, or reshape a response. If that share stays low by Phase 9, merge the BFFs or reconsider GraphQL.
