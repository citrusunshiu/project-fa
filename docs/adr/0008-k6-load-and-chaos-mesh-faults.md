# ADR-0008: k6 for load, Chaos Mesh and Toxiproxy for faults

- **Status:** Proposed
- **Date:** 2026-11-01
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

Every result in this repository rests on its load generator and its fault injector. A load generator that waits for each reply before sending the next request (a closed model) slows down when the system slows down, and hides exactly the queueing the experiments look for. This is coordinated omission. Faults have to reach the network, the clock, the disk and the pods, and be scriptable, repeatable and scheduled inside a pipeline.

## Options

### Load

- **k6:** open-model arrival-rate executors, scripts in TypeScript or JavaScript, built-in gRPC and WebSocket support, execution segments to split one test across machines without a coordinator, and Prometheus remote-write output.
- **Locust:** Python, flexible, closed model by default; open-model behaviour needs custom shaping.
- **Gatling:** strong open-model support, JVM-based, Scala, Java or Kotlin scripts.
- **wrk2:** corrects for coordinated omission at a constant rate, but HTTP only and hard to script for multi-step journeys.

### Faults

- **Chaos Mesh:** Kubernetes custom resources for pod, network (latency, loss, partition, bandwidth), time skew, I/O, DNS, stress and HTTP faults, with schedules and workflows. A CNCF incubating project.
- **LitmusChaos:** similar coverage, organised around a hub of experiments; heavier to run.
- **Toxiproxy:** a TCP proxy that injects latency, bandwidth limits and resets between a client and one dependency. Deterministic and ideal inside integration tests, not a cluster-wide tool.
- **Commercial services:** out of scope for an open repository.

## Decision

k6 for load, Chaos Mesh for cluster-level faults, and Toxiproxy for deterministic dependency faults in integration tests. The services' own fault endpoints (the [platform contract](../architecture/platform-contract.md#fault-endpoints)) cover application-level misbehaviour.

## Lab stance and production stance

- **Lab stance:** both tools are measurement plumbing, chosen to be trusted rather than novel. k6's execution segments make the multi-device phase possible without building a coordinator.
- **Production stance:** the same choices hold up in production use. Larger organisations often build a fault-injection platform on top, with blast-radius controls and automatic aborts on SLO burn.

## Consequences

- Load scripts are TypeScript and share the client behaviour spec's retry and reconnect rules, so the reconnect-storm experiment measures clients that behave like the real apps.
- Chaos Mesh needs k3s's containerd socket path ([ADR-0003](0003-local-runtime-k3d.md)).
- Time skew (TimeChaos) may not work on arm64 nodes. If it doesn't, clock-skew experiments move to an x86 cloud environment.

## What would change my mind

If k6 can't drive the WebSocket reconnect storm at the scale Phase 9 needs, or if Chaos Mesh's network faults behave differently from real partitions in the cloud phase, the tool goes.

## How we'd know

Before trusting any number, Phase 1 calibrates the load generator: a fixed-latency stub service must come back with the latency it was configured for, at every rate the test uses. Phase 5 reruns the partition suite on real zones and compares the results with the local ones.
