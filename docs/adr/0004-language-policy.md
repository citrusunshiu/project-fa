# ADR-0004: Language policy

- **Status:** Proposed
- **Date:** 2026-11-01
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

Part of the point of this repository is to work in the languages most widely used for backend, web and mobile engineering, each where it is strongest. Unbounded polyglot is how demo systems became unmaintainable: one of the best-known microservice demos later warned against its own "intentionally polyglot" design. So the language set has to be closed, each choice has to be justified, and adding a language has to carry its own cost.

## Options

### Option A: One language for every service

What most real organisations of this size converge on. It teaches one ecosystem deeply and nothing about choosing.

### Option B: Free polyglot

Any language for any service. Maximum variety, no discipline.

### Option C: A closed list, best fit first, spread as the tie-breaker

Nine languages, counting C and C++ together: **Go, Python, Java, C#, Rust, C++, C, TypeScript, Kotlin, Swift**. Each component gets the language that fits it best. Where several fit equally well, the tie goes to whichever keeps the spread across languages even.

## Decision

Option C, with these rules:

- **The list is closed.** A tenth language needs a new decision record.
- **A language's first service ships its template and its CI job in the same change.** Later services in that language start from the template. The catalog check fails if a real service's language has no template.
- **Mainstream frameworks only:** the ones industry uses for that job, not niche alternatives.
- **Every language reaches F2 inside the roadmap,** so every one gets a template and CI.

### The map

| Component | Language | Why it fits | Pick |
|---|---|---|---|
| Web client | TypeScript | The browser's language | Best fit |
| Android app (customer and courier modes) | Kotlin | Native Android | Best fit |
| iOS app (customer and courier modes) | Swift | Native iOS | Best fit |
| Web BFF | TypeScript (Node) | Shares types with the web client; owned by the web side | Best fit |
| Mobile BFF | Kotlin (Ktor) | The mobile side's language; coroutines for fan-out | Tie (Go, Java) |
| Global rate limiter (Envoy's rate-limit gRPC API) | Rust | On every request's path, so tail latency matters | Tie (Go, C++) |
| Catalog API | Java (Spring Boot) | The default e-commerce service stack | Tie (C#, Kotlin) |
| Search indexer | Java | Debezium and Kafka Connect are JVM | Best fit |
| Typeahead | Rust | The `fst` crate: finite-state transducers, the structure search engines use for prefixes | Best fit |
| Catalog crawler | Python | The fetching and parsing ecosystem | Best fit |
| Back-office | Python (Django) | Django's admin is the standard internal CRUD tool | Best fit |
| Group cart | C# (Orleans) | One virtual actor per cart: single-threaded, no locks, placement handled by the runtime | Best fit |
| Order and checkout saga | Kotlin (Spring Boot + Temporal) | Common for this domain at delivery companies; Temporal's JVM SDK | Best fit |
| Payments and ledger | C# | A built-in base-10 `decimal` for money; .NET is common in finance | Tie (Java) |
| Payouts scheduler | C# (Temporal .NET) | Same team and data as the ledger | Tie (Java, Go) |
| Fake payment processor | Python (FastAPI) | Small and quick to change | Tie (TypeScript, Go) |
| Inventory and flash sale | Go | Many concurrent waiters, an admission queue, low latency | Tie (Rust) |
| Dispatch matching | C++ | Matching engines are C++ territory; the H3 geo index is a C library | Best fit |
| Location ingest | Rust | The hottest write path, with no garbage-collection pauses | Best fit |
| Live updates gateway | Go | A goroutine per connection; the usual home for connection gateways | Best fit |
| Notifications | TypeScript (Node) | I/O-bound calls to provider SDKs | Tie (Go, Python, Kotlin) |
| Deals feed | Go | No language is clearly better | Tie (Java, C#) |
| Photo pipeline | C++ (libvips) | Image-processing libraries are C and C++ | Best fit (tie Rust) |
| Share links | Swift (Vapor) | Any language can run a shortener; this gives Swift one server-side use | Tie, for spread |
| Ad-click aggregation | Java (Flink) | Stream processing's home | Best fit |
| Delivery-time and ranking models | Python | ML training and serving | Best fit |
| `sim`, operators | Go | The Kubernetes ecosystem's language | Best fit |
| Raft config and lock service (lab) | Go | The language of etcd and Consul; Maelstrom has a Go library | Best fit (tie Rust) |
| Kernel probes, XDP packet dropper | C | eBPF programs are restricted C, and libbpf is the canonical C loader | Best fit |
| Invariant checkers, experiment analysis | Python | Data analysis | Best fit |
| Load scenarios | TypeScript (k6) | k6 runs TypeScript scripts | Best fit |
| Cost meter | Rust | One static binary with a live terminal view; no language is clearly better | Tie (Go, Python), for spread |

Proposed components carry a suggested language in the [catalog](../../catalog/components.yaml); this record's map is updated when each one is accepted.

### Spread across the 23 backend services

| Language | Services | Also |
|---|---|---|
| Go | 3 | `sim`, operators, the Raft lab |
| Rust | 3 | The cost meter |
| Java | 3 | |
| C# | 3 | |
| Python | 4 | Checkers and analysis |
| Kotlin | 2 | The Android app |
| TypeScript | 2 | The web client, k6 scenarios |
| C++ | 2 | |
| Swift | 1 | The iOS app |
| C | 0 | The eBPF programs and their loader |

## Lab stance and production stance

- **Lab stance:** using each language where it is strongest is the study goal. The platform contract and per-language templates keep the cost bounded.
- **Production stance:** a company this size would standardise on two or three: one language for most backend services (Go, Kotlin or Java), TypeScript for the web, and Kotlin and Swift for the native apps, with exceptions (C++ for matching, Python for ML) argued case by case. Every extra language costs hiring, on-call depth, security patching and shared libraries.

## Consequences

- Nine toolchains means nine sets of dependency updates. Grouped automated update PRs and keeping most components simulated contain that.
- Templates are first-class code: a contract change lands in every template at once.
- The map is a draft until each component reaches F2; a component's language can change before its first real code, with a note here.

## What would change my mind

If templates fall behind the contract, or dependency updates eat more time than features, the variety has stopped paying for itself, and some services should consolidate.

## How we'd know

Track the share of merged changes that are dependency or template maintenance per phase. If it passes a third, revisit this record.
