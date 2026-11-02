# ADR-0003: Run locally on k3d

- **Status:** Proposed
- **Date:** 2026-11-01
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

The system has to run on one laptop, with zones to partition, nodes to drain and operators to manage databases. The experiments need Kubernetes-level features: Chaos Mesh, operators (CloudNativePG, Strimzi), horizontal autoscaling and network policy. The laptop's container VM has limited memory, so per-node overhead matters.

## Options

### Option A: Docker Compose

The lightest, but no operators, no Chaos Mesh, no network policy, no autoscaling. Most of the planned experiments are impossible.

### Option B: kind

Upstream Kubernetes (kubeadm) in Docker containers. Conformance-identical to managed clusters, well supported by Chaos Mesh and Cilium. Heavier per node.

### Option C: k3d

k3s (a lightweight, certified Kubernetes distribution) in Docker containers. Multi-node clusters start in seconds and use less memory per node. It has a built-in image registry. Its defaults (Traefik, flannel, the local-path provisioner) can be turned off where the experiments need something else.

### Option D: minikube

Mature, but multi-node support is weaker, and it adds little over kind or k3d for this use.

## Decision

Option C: k3d with 3 or 4 agent nodes, each labelled as a zone (`topology.kubernetes.io/zone`), so zone partitions and zone-aware placement can be tested. Traefik and flannel are disabled: Envoy Gateway is the edge and Cilium is the network ([the overview](../architecture/overview.md)).

## Lab stance and production stance

- **Lab stance:** lighter nodes leave more of the laptop for the system under test, and fast cluster creation makes create-run-destroy experiment pipelines practical.
- **Production stance:** a managed Kubernetes service (EKS, GKE, AKS). k3s is a sound production choice at the edge, not for a company this size. The cloud phase reruns the experiments on a managed cluster, which tests whether local findings transfer.

## Consequences

- Chaos Mesh must be pointed at k3s's containerd socket (`/run/k3s/containerd/containerd.sock`), not the default.
- Cilium on k3d needs flannel and k3s's network policy controller disabled, and BPF filesystem mounts on the nodes.
- Zones on one laptop share one kernel and one disk. A "zone failure" here is a scheduling and network fact, not a hardware one; the cloud phase covers the rest.

## What would change my mind

If Cilium or Chaos Mesh can't be made to work reliably on k3d, switch to kind. Both run in Docker, so the switch is cheap.

## How we'd know

Phase 1's smoke test: create the cluster, install Cilium and Chaos Mesh, run one NetworkChaos partition between two zone labels and one TimeChaos skew. If any of them fails on k3d and works on kind, this record is superseded.
