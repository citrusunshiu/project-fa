# ADR-0002: Build through a fidelity ladder, tracked in a component catalog

- **Status:** Proposed
- **Date:** 2026-11-01
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

The first business line has more than 30 components. Building all of them for real would take years and would bury the interesting parts under CRUD. Building only a few leaves the system's shape (fan-out, pools, retries, queueing) untested, and that shape is where many production failures come from. Comparable demo systems died either by sprawling or by rotting once their sponsor's reason ended.

## Options

### Option A: Build every component for real, slice by slice

Honest, but slow. The whole system can't run until late, so topology-level failures appear last.

### Option B: Build a few components for real, leave the rest as diagrams

Fast, but the system never runs as a whole.

### Option C: A fidelity ladder

Every component exists first on paper (F0), then as a simulated service doing fake work (F1), and only the parts worth learning get a real path (F2) and then hardening (F3). A generic simulator, configured by a topology file, plays every component that isn't real yet. A real service replaces its simulated twin behind the same contract, and the experiments run again.

## Decision

Option C, with the [component catalog](../../catalog/components.yaml) as the source of truth for each component's level, language, stores, dependencies and design doc. A CI check, `tools/check_catalog.py`, keeps the catalog honest:

- every entry has a design doc, and every service directory has an entry;
- F2 and above needs a service directory, and its language needs a service template;
- F3 needs an SLO file, a runbook and at least one passing experiment.

The levels are defined in the [charter](../charter.md#the-fidelity-ladder).

## Lab stance and production stance

- **Lab stance:** the ladder makes the project finishable. The whole architecture can run, and show where it bottlenecks, long before most of it is written. The gap between a simulated component's predicted behaviour and the real one's measured behaviour is itself a finding.
- **Production stance:** real organisations do a version of this when they model capacity or run load tests against stubs. The catalog maps directly onto a service catalog in a developer portal (Backstage's `catalog-info.yaml`).

## Consequences

- Most components stay at F0 or F1 permanently. That is intended.
- The simulator has to be good enough to be wrong in interesting ways: it models pools, retries, timeouts and CPU cost, not just latency.
- Docs can't silently drift: a component without a design doc, or a service directory without a catalog entry, fails CI.

## What would change my mind

If simulated components routinely mislead, so that F1 findings don't survive the swap to F2, the simulator isn't earning its place.

## How we'd know

Each swap from F1 to F2 reruns the experiments that covered the component, and the report compares predicted and measured results. A pattern of large, unexplained gaps means the simulator needs another parameter, or the ladder needs rethinking.
