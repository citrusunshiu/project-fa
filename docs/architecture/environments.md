# Environments

How the system runs on a laptop, on machines the maintainer owns, on AWS, GCP and Azure, or split across several of them. [ADR-0011](../adr/0011-one-platform-many-targets-placement-files.md) is the decision behind it. Nothing here exists yet: the laptop target arrives in Phase 1, owned machines in Phase 4 and the first cloud in Phase 5.

An **environment** is one named set of clusters running one copy of the system for one experiment. A **target** is a place a cluster can run. A **placement file** says which targets an environment uses and what runs on each.

## Three layers

Only the bottom layer differs per target.

| Layer | What it is | Per target? | Tools |
|---|---|---|---|
| Substrate | A Kubernetes cluster, its nodes, network and load balancer, and the cloud resources the environment needs (managed stores, buckets) | Yes | k3d, k3s with Ansible, Terraform |
| Platform | Cilium, Envoy Gateway, cert-manager, the operators, observability, Chaos Mesh, flagd, External Secrets | Shared, with an overlay per target | Helm and Kustomize, Flux later |
| Workloads | The services and the harness, one chart each | Shared | Helm |

## Targets

| | Laptop | Owned machines | AWS | GCP | Azure |
|---|---|---|---|---|---|
| Cluster | k3d (k3s in Docker) | k3s | EKS | GKE Standard | AKS |
| Created by | `k3d cluster create` from a config file | The k3s Ansible playbook and an inventory | Terraform | Terraform | Terraform |
| Zones | Node labels | One zone per machine, or per network switch | Three availability zones | Three zones | Three availability zones |
| Nodes | Docker containers | The machines themselves | Managed node groups, Spot by default | Spot VMs | Spot node pools |
| Network plugin | Cilium (flannel off) | Cilium | Cilium in place of the VPC CNI | Dataplane V2 (Google's managed Cilium) | Azure CNI powered by Cilium |
| Load balancer | k3d's built-in load balancer | Cilium LB IPAM with L2 announcements | AWS Load Balancer Controller | GKE's load balancer | Azure Load Balancer |
| Storage class | local-path | local-path; Longhorn if volumes must survive a machine | gp3 through the EBS CSI driver | pd-balanced | managed-csi |
| Chaos Mesh runtime socket | `/run/k3s/containerd/containerd.sock` | `/run/k3s/containerd/containerd.sock` | `/run/containerd/containerd.sock` | `/run/containerd/containerd.sock` | `/run/containerd/containerd.sock` |
| How CI signs in | — | — | GitHub OIDC to an IAM role | Workload Identity Federation | A federated credential on a managed identity |
| How pods get cloud access | — | — | EKS Pod Identity | Workload Identity Federation for GKE | Microsoft Entra Workload ID |
| Secrets behind bindings | SOPS and age | SOPS and age; OpenBao later | Secrets Manager through External Secrets | Secret Manager through External Secrets | Key Vault through External Secrets |
| Terraform state | — | — | S3 with a native lock file | Cloud Storage | Blob Storage with lease locking |
| Deletes as one unit | The cluster | `k3s-uninstall.sh` on each machine | A sandbox account: the tag reaper, then aws-nuke as a last resort | A sandbox project: the label reaper, then shutting the project down | A resource group per environment |
| Cloud-level faults | — | Pull a cable or a plug | AWS Fault Injection Service, including an availability-zone power interruption | No first-party service; Chaos Mesh covers it | Azure Chaos Studio |

What each target costs to run, and what moving data between targets costs, is in [costs](costs.md).

### Laptop

[ADR-0003](../adr/0003-local-runtime-k3d.md): k3d with three or four nodes labelled as zones, in one of three profiles (minimal, standard, full). This is the default target and the only one Phase 1 needs.

### Owned machines

- **Which machines.** Linux machines join directly. Raspberry Pi 4 or 5 boards need a 64-bit OS and, in practice, 8 GB of memory. A Mac joins through a Linux VM (Lima or OrbStack) and a Windows PC through WSL 2 with mirrored networking. Neither is a native k3s node.
- **Install.** The official k3s Ansible playbook installs k3s from an inventory file. The real inventory names hostnames and addresses, so it's git-ignored; `infra/self-hosted/inventory.example.yaml` shows its shape.
- **Zones are physical.** Each machine (or each switch) is a zone, so a partition can be a pulled cable instead of an iptables rule, and a node failure can be a pulled plug.
- **Off the LAN.** Machines elsewhere join over Tailscale, which also adds real WAN latency.
- **Teardown** is a reset, not a deletion: `k3s-uninstall.sh` on each machine returns it to its starting state.

### AWS

- **Long-lived, applied once by the maintainer:** a sandbox account in an AWS Organization, the S3 state bucket, the GitHub OIDC provider and the CI role, a budget with alerts, and the reaper's permissions.
- **Per environment:** a VPC across three zones, an EKS cluster, Spot node groups, and any managed stores the placement asks for (RDS or Aurora PostgreSQL, MSK, ElastiCache for Valkey, OpenSearch Service).
- **Testing rules.** AWS's EC2 testing policy asks that tests against AWS-hosted targets run from the same Region, and forbids volumetric DDoS simulation. Load generators sit in the target's Region unless the WAN itself is under test.

### GCP

- **Long-lived:** a sandbox project, a Cloud Storage state bucket, Workload Identity Federation for GitHub, and a budget with alerts.
- **Per environment:** a VPC, a GKE Standard cluster (zonal when the credit should cover it, regional for zone experiments), Spot node pools, and managed stores on request (Cloud SQL for PostgreSQL, Memorystore for Valkey).
- **What it's for:** the multi-region experiment, and the standby side of cross-cloud recovery.

### Azure

- **Long-lived:** a subscription used only for this repository, a storage account for state, a managed identity with a federated credential for GitHub, and a budget with alerts.
- **Per environment:** one resource group holding a virtual network, an AKS cluster on the free tier, Spot node pools, and managed stores on request (Azure Database for PostgreSQL, Azure Cache). Deleting the resource group deletes the environment.
- **What it's for:** an optional third substrate, to test how portable the platform layer really is. AKS's free control plane makes it the cheapest cloud cluster ([costs](costs.md#control-planes)).

### What differs, and where it lives

Every difference in the table above lives in `platform/overlays/<target>/`. The managed Cilium variants (GKE, AKS) offer fewer features than a self-installed Cilium, and each overlay lists which experiments lose something on that target.

## Placement files

One file per environment, in `infra/environments/`.

```yaml
name: checkout-hybrid
ttl: 4h               # cloud targets are destroyed after this, whatever happens
budget_usd: 15        # the driver refuses to start if the estimate is higher
targets:
  laptop: {kind: k3d, profile: standard}
  aws:    {kind: eks, region: us-west-2, nodes: {size: medium, count: 3, spot: true}}
network: tailscale    # or cluster-mesh, or public-mtls
placement:
  default: laptop
  slices:
    checkout-and-payments: aws
  stores:
    ledger-postgres: {target: aws, mode: managed}   # RDS instead of CloudNativePG
  harness:
    load: laptop
    observability: laptop
```

Node sizes are classes (`small`, `medium`, `large`), which each cloud's Terraform module maps to an instance type and caps through variable validation. A placement file therefore never names a cloud's instance types.

**The placement checker enforces these rules:**

1. Every component in the environment's profile is placed exactly once, or explicitly replicated (`replicas: [aws, gcp]` with a replication mode).
2. A store sits on the same target as the service that owns it, unless the entry says `remote: true`. The split is then the experiment.
3. The harness never shares nodes with the system under test.
4. Every cloud target has a time-to-live and a budget below the repository-wide caps.
5. It lists each synchronous call that crosses targets, with the round-trip time measured between those targets. The simulator then predicts each journey's p99 with that latency added, before anything is paid for.
6. It estimates the bytes crossing each target boundary from the traffic model and prices them with the [data-movement prices](costs.md#moving-data). That number goes into the run's cost report.

## Splits

**Calls between targets.** A caller always uses the same Service name. When the callee runs on another target, the driver creates a Service of that name in the caller's cluster that forwards to the other cluster: a Tailscale egress Service by default, or a Cilium global service under Cluster Mesh. The platform contract's deadlines and retries apply unchanged, so the WAN hop shows up in traces and eats into the deadline budget like any other latency.

**Data between targets.** Each store replicates with its own mechanism: natively for CockroachDB and Cassandra (multiple data centres), as a replica cluster for CloudNativePG, and through MirrorMaker 2 for Kafka.

**Measurements between targets.** Each cluster runs its own OpenTelemetry Collector and Prometheus agent, which forward to the one Grafana stack named by `harness.observability`. Every span and series carries `deployment.environment`, `k8s.cluster.name`, `cloud.provider`, `cloud.region` and `cloud.availability_zone`.

**The rule the lab breaks on purpose.** The production stance in ADR-0011 is to split only at asynchronous seams. Two of the environments below measure the same split both ways.

| Environment | Targets | What it shows | Phase |
|---|---|---|---|
| `local` | Laptop | Everything not listed below | 1 |
| `lan-load` | Laptop, plus devices generating load | One test split across devices, with merged results | 4 |
| `owned` | Owned machines, with the harness on the laptop | Physical zones: partitions are cables | 4 or later |
| `aws` | EKS in three zones, load from a separate node pool | Real zones, managed failover, autoscaling on real capacity, an actual bill | 5 |
| `checkout-hybrid` | Laptop and AWS | A WAN hop in the middle of a synchronous call chain: the anti-pattern, measured | 5 |
| `checkout-async-seam` | Laptop and AWS | The same split along a replicated log instead | 5 |
| `multi-region` | GKE in two regions | Cross-region latency; CockroachDB surviving the loss of a region | After 5 |
| `cross-cloud-recovery` | An AWS primary and a GCP standby | A timed failover drill, with recovery point and recovery time measured | After 5 |
| `portability` | AKS | The Phase 3 suite on a third substrate: what breaks | Optional |

## Lifecycle

`just env up <name>` runs these steps:

1. Check the placement file, then print the [cost meter](costs.md#the-cost-meter-planned)'s estimate for the environment and its load plan.
2. Bring up each target's substrate in parallel. Each cloud target has its own Terraform state, keyed by environment.
3. Install the platform on each cluster: the base add-ons plus that target's overlay.
4. Join the clusters and create the forwarding Services.
5. Create the bindings: managed stores' credentials come from the cloud's secret manager through External Secrets, and in-cluster stores' credentials from their operators.
6. Deploy to each cluster the charts placed on it.
7. Wait until every `/readyz` is green and the invariant checkers are attached.

`just env down <name>` reverses steps 6 to 2, then asks the reaper to confirm that nothing labelled with the environment remains. The experiment pipeline (create, load, inject a fault, check against baselines, tear down) is the same on every target, because it only ever calls these two commands.

## Safety

- **No long-lived keys.** CI reaches each cloud through OIDC, and the trust policy admits only this repository's `main` branch running in a GitHub environment that the maintainer must approve. A fork or a pull request can't assume a cloud role.
- **Expiry on everything.** Every resource carries the labels `fa-environment` and `fa-expires-at`. A scheduled reaper deletes expired environments in each cloud and reports anything it found.
- **Budgets.** Every cloud account has a budget with alerts, and the driver refuses to start a run whose estimate exceeds the environment's own budget.
- **Size caps.** Variable validation caps node sizes and counts. Spot capacity is the default.
- **Private details stay private.** Inventories, kubeconfigs, Terraform state and Tailscale keys never enter git ([ADR-0010](../adr/0010-licence-and-public-text-policy.md)).

## Layout

```
infra/
  local/                 k3d configs, one per profile
  self-hosted/           k3s via Ansible; inventory.example.yaml (the real inventory is git-ignored)
  foundation/<cloud>/    long-lived resources, applied once by the maintainer
  clusters/<cloud>/      the per-environment Terraform root for each cloud
  modules/               shared Terraform modules: labels and expiry, size classes, managed stores
  environments/          placement files
  reaper/                scheduled clean-up for each cloud
platform/
  base/                  add-ons every cluster gets
  overlays/<target>/     what differs per target
```

## Open questions

- Which machines are available as owned nodes, and whether all of them are on one LAN.
- Whether the system needs a public domain. The default is none: cert-manager issues certificates from a private CA, and clients use the load balancer's address.
- The driver's language: Python, like the checks in `tools/` (the default), or Go, like `sim`.
