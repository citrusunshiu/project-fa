# Charter

## Purpose

Design notes can explain a retry policy or a cache. What they can't give you is the moment a decision meets its consequences: the retry policy that looked fine until a dependency slowed down, or the cache that hid a hot key until the flash sale. This repository exists to produce those moments on purpose and measure them.

It describes the system of one fictional company, Project FA, end to end, builds the parts worth learning, and runs the whole thing under load and under faults. It is the place where many designs meet in one system, where behaviour under failure gets measured instead of guessed, and where decisions can be deliberately wrong so the result can be watched.

## Non-goals

- **A product.** There are no real users, real payments or personal data.
- **Production-scale claims.** See [what results may claim](#what-results-may-claim).
- **A framework for others.** The repository is public so it can be read and checked, not adopted.
- **Completeness for its own sake.** A component exists because it forces a question worth answering. Most components stay on paper or simulated.

## The fidelity ladder

Every component sits on one rung, recorded in the [catalog](../catalog/components.yaml). [ADR-0002](adr/0002-fidelity-ladder-and-component-catalog.md) is the decision behind it.

| Level | What exists | What it can teach |
|---|---|---|
| **F0 Paper** | A design doc: requirements, estimates, API, data model, failure table, open questions | The decision and its trade-offs |
| **F1 Simulated** | The generic simulator, `sim`, configured to play this component | How the topology behaves: fan-out, tail amplification, pool exhaustion, retry storms, queueing |
| **F2 Real path** | A real implementation of the core path, on a real data store, meeting the [platform contract](architecture/platform-contract.md) | How the data behaves: contention, consistency, duplicates, lag |
| **F3 Hardened** | F2 plus SLOs, burn-rate alerts, dashboards, a runbook and a chaos suite that passes | Operations: whether you'd notice, and how you'd recover |

**The simulator** is one image that reads a topology file. For each endpoint the file sets its downstream calls (sequential or in a parallel fan-out), a latency distribution, CPU cost per request, payload size, an error rate, connection-pool sizes, timeouts and a retry policy. Istio's [isotope](https://github.com/istio/tools/tree/master/isotope) is the precedent; pools, retries and CPU cost are added because those are what make bottlenecks.

**The swap rule.** A real service replaces its simulated twin behind the same contract, and the experiments that covered it run again. The gap between what the simulation predicted and what the real service measured is a finding in its own right, and it recalibrates the simulator.

## The unit of output: the experiment

Each experiment report follows the [template](templates/experiment-report.md):

1. the question;
2. a steady-state hypothesis with a number in it;
3. a prediction, from Little's law or a back-of-envelope estimate, written before the run;
4. the setup: commit, profile, the fidelity of each component involved, resource limits, load profile, seed;
5. the fault;
6. the result, as percentiles from histograms, never averages, with the variance across repeat runs;
7. prediction versus result, and why they differ;
8. what changed: the decision record or design doc edited because of it;
9. one command that reproduces it.

**Each experiment runs as one pipeline.** It creates the environment, loads it, injects the fault, checks the result against committed baselines (one normal, one under chaos, each with pass/fail criteria) and destroys the environment. The run writes its own results file. No result table is ever filled in by hand.

**Invariants are the oracle.** A chaos run that "passes" because the dashboards stayed green proves little. Checkers run while faults are injected and again afterwards, and assert business invariants over the recorded history: the ledger sums to zero, no item is oversold, no order has two couriers, every paid order has exactly one payment effect, and no acknowledged write is lost.

## What results may claim

- **Lab scale is not paper scale.** The design docs argue from made-up paper-scale numbers (the [company brief](company/brief.md)). Runs drive lab scale. Where the lab can't reach a paper-scale rate, the system under test is deliberately squeezed (CPU limits, small pools, added latency) so its saturation point falls inside what the lab can drive, and the report records that scale factor. A lab number is never quoted as a paper-scale claim.
- **Measurements must be trustworthy before they are interesting.** Load is an open model (a constant arrival rate, not a fixed number of waiting users), the load generator never shares CPUs with the system under test, and results come from histograms over repeat runs.
- **Simulated is not real.** A finding from an F1 component says something about the topology, not the implementation.

## Principles

- **Measure with tools you trust; experiment on what you're learning.** The load generator, metrics and traces stay boring and familiar, so a strange result points at the system under test and not at the instruments.
- **Every decision has a lab stance and a production stance.** This repository uses more languages and data stores than any real team should. Each decision record says why the variety is here, and what a real organisation would standardise on instead.
- **The docs match `main`.** CI checks the catalog against the code, every link, and every experiment report's commit and reproduce command. The reasoning lives in this repository, next to the code it explains.
- **Every reading note changes something.** A note on a paper or blog post must change a design doc, add a decision record or start an experiment, or say why it changes nothing.
- **Thin vertical slices over broad skeletons.** Each phase ends with something that runs and at least one experiment report.

## Roles

The maintainer decides every decision record, and answers each design doc's question chain before reading the model answers. AI coding agents draft documents and implement code from issues. Each decision record names who decided it.

## Roadmap

Each phase ends with something that runs and at least one experiment report. Phases 4 to 7 may be reordered.

| Phase | Builds | Exit criteria |
|---|---|---|
| **0. Paper architecture** | Charter, company brief with estimates, architecture diagrams, catalog with every component at F0, templates, founding decision records, doc checks in CI | Each founding decision can be defended from its own text; the repository goes public |
| **1. Harness, everything at F1** | One-command local cluster; profiles; observability; the simulator; the whole first business line as a simulated topology; k6 baseline; Chaos Mesh; invariant-checker skeleton | Two reports: where the saturation knee is and why; a retry storm under a slow dependency, with and without retry budgets and deadlines. Each profile's memory and disk footprint measured |
| **2. Checkout, for real** | Order saga, ledger, inventory reservation and fake payment processor at F2; Postgres with an outbox into Kafka; idempotency keys | Invariant checker live. Reports: duplicate delivery, a consumer crash mid-batch, a flash sale on one row with three reservation designs compared |
| **3. Chaos and SLOs** | SLOs and burn-rate alerts; a chaos suite (partition, clock skew, broker loss, database failover); eBPF probes and an XDP packet dropper; the first game day | Checkout at F3; one postmortem; an orchestrated saga against choreography, compared under failure |
| **4. Multi-device load** | A fleet runner, LAN exposure, k6 execution segments, remote-write metrics | One test split across two or more devices with merged results; the network ceiling measured first |
| **5. Cloud** | Terraform for AWS, a short-lived environment per experiment, placement files and the first laptop-plus-cloud split ([environments](architecture/environments.md)), the [cost meter](architecture/costs.md#the-cost-meter-planned), OIDC, budgets, a reaper | Up and down within a fixed time; zero leftovers; the Phase 3 suite rerun across real zones; the same split measured through a synchronous hop and through an asynchronous seam; a cost report |
| **6. Dispatch and tracking** | Location ingest, geo matching with leases and fencing, a WebSocket fan-out gateway over NATS | Reports: 30,000 location writes a second, a hot geo cell, a lease expiring mid-delivery |
| **7. Browse and search** | Catalog API on MongoDB with a change-data-capture indexer, typeahead, the catalog crawler and back-office, click aggregation in Flink | Reports: indexing lag against search freshness, a cache stampede, late events in click windows |
| **8. Web client** | The web app and its backend-for-frontend; the group cart in the browser | Reports: concurrent cart edits merging; the backend-for-frontend's fan-out latency |
| **9. Android app** | Customer and courier modes, the mobile backend-for-frontend, background location, push notifications | Reports: a reconnect storm with and without jitter; offline cart merge correctness |
| **10. iOS app** | The same modes and client behaviour spec, push notifications, share links | Both apps pass the same behaviour-spec tests; the reconnect storm rerun with mixed clients |
| **Lab** (any time) | Gossip Glomers on Maelstrom, then Raft, then that Raft deployed as the system's config and lock service | Maelstrom's checks pass; the service survives a partition plus clock skew inside the cluster |
| **Reading** (ongoing) | A few notes a week, each changing something | A sources index by company and topic |

Components no phase names stay at F1 until a phase or a reading note pulls them up.

## Phase 0 is done when

- every planned component in the catalog has a design doc (`tools/check_catalog.py` lists no pending design docs);
- each founding decision record is decided, and can be defended from its own text;
- the company brief's estimates have been challenged and either defended or changed;
- the checks pass in CI, and the public-text check finds nothing.
