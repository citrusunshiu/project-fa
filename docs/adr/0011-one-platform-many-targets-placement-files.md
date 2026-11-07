# ADR-0011: One platform on many targets, placed by a placement file

- **Status:** Proposed
- **Date:** 2026-11-06
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

The system has to run in more than one place. Phase 1 runs on a laptop ([ADR-0003](0003-local-runtime-k3d.md)). Phase 4 adds other devices. Phase 5 adds short-lived cloud environments, AWS first, and later experiments want a second cloud and machines the maintainer owns. Some experiments want a split: the stateful core in one place and the edge in another, load from a third place, or a primary and a standby in different clouds.

Without a rule, each target grows its own copy of the manifests and the copies drift. The questions are which parts may differ per target, and how a split is declared.

The numbers that matter, as of this record's date ([costs](../architecture/costs.md) keeps the current figures):

- A managed control plane costs about $0.10 an hour on EKS and on GKE Standard (GKE's monthly credit covers one zonal cluster), and nothing on AKS's free tier.
- Data leaving AWS for the internet costs about $0.09 per GB in the first pricing tier. The courier location stream at peak (30,000 writes a second at about 200 bytes, so 6 MB/s or 21.6 GB an hour) would cost about $2 an hour by itself if it crossed a cloud boundary.

## Options

### Option A: One target per phase, each with its own manifests

What the roadmap implied. Simple to start, but each new target copies the last one and diverges, and nothing records which parts are portable.

### Option B: Terraform for every target, one root per environment

One `apply` brings up everything, local and cloud. But one state spans every cloud, so a failure in one leaves the whole environment half-applied, and laptop clusters fit Terraform badly.

### Option C: Cluster API or Crossplane from a management cluster

Clusters and cloud resources become Kubernetes objects that controllers reconcile, which is how many platform teams run fleets. It needs a management cluster that outlives every environment, the managed-Kubernetes providers vary in maturity, and it adds the most moving parts before the first experiment.

### Option D: Three layers and a placement file

- **Substrate, per target:** whatever produces a Kubernetes cluster and its network. k3d on the laptop, k3s on owned machines, Terraform for EKS, GKE and AKS.
- **Platform, shared:** the same add-ons on every cluster, plus a small overlay per target for what genuinely differs: the network plugin's mode, the storage class, the load balancer, the container runtime socket.
- **Workloads, shared:** the same charts everywhere.

A placement file names an environment's targets and which slices, components, stores and harness parts run on each. A driver reads it and runs each layer per target, each target with its own state.

## Decision

Option D. The substrates are k3d ([ADR-0003](0003-local-runtime-k3d.md)), k3s installed by Ansible on owned machines, and Terraform ([ADR-0009](0009-terraform-over-opentofu.md)) for the clouds. Clusters on different targets join over Tailscale by default; Cilium Cluster Mesh is an experiment, not the default. Services find their stores and brokers through bindings (mounted files in the [Service Binding for Kubernetes](https://servicebinding.io/) layout), so a managed store and an in-cluster one look the same to the code. The build order is the laptop, then owned machines (Phase 4), AWS (Phase 5), GCP for multi-region and cross-cloud recovery, and Azure as an optional third cloud. [Environments](../architecture/environments.md) describes the method per target.

## Lab stance and production stance

- **Lab stance:** one platform on five substrates shows which parts are portable and which aren't, and the overlays list the differences explicitly. A split is declared in a file and simulated by `sim` before it costs money.
- **Production stance:** one cloud, several zones, a managed control plane. A second region only for a stated recovery objective. A second cloud or a hybrid only when a requirement forces it, such as data residency, an existing data centre or a contract. When a system must split, it splits at asynchronous seams (a replicated log or database), never in the middle of a synchronous call chain. The lab breaks that rule on purpose to measure what it costs.

## Consequences

- The overlays are the list of what isn't portable. An overlay that grows past a few files is a finding worth a reading note or an experiment.
- Images are built for linux/amd64 and linux/arm64, because Raspberry Pis, Apple silicon and the clouds' cheaper Arm instances are all in play. The [platform contract](../architecture/platform-contract.md) says so.
- The platform contract gains bindings.
- Every cloud environment lives inside something that deletes as one unit: a sandbox AWS account, a sandbox GCP project, an Azure resource group per environment. Expiry labels and the reaper back that up.
- A placement checker validates placement files the way the catalog check validates the catalog.
- Inventories of owned machines (hostnames, addresses) stay private and git-ignored. Only an example is committed ([ADR-0010](0010-licence-and-public-text-policy.md)).
- Ruled out for now: Cluster API, Crossplane, and Terraform for laptop clusters.

## What would change my mind

- If the driver grows into a scheduler of its own (retries, dependency graphs, drift detection), Cluster API or Crossplane does that job better.
- If Tailscale's hosted coordination becomes a problem (cost, terms, or an outage during a run), Headscale, its open-source counterpart, replaces it, or cloud VPNs connect the clouds.

## How we'd know

- The Phase 3 chaos suite passes unchanged on k3d, on EKS and on at least one more target. Each test that needs a target-specific edit names a portability gap.
- The simulator's predicted p99 for a split lands within 20% of the measured one, a starting threshold. If it doesn't, the latency model between targets is wrong.
