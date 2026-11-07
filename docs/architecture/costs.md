# Costs

Every price this repository relies on, with its source and the date it was checked, plus worked estimates of what moving data costs. Other documents link here instead of repeating prices, so a price changes in one place. This page holds estimates; each experiment report records what its run actually cost.

## Prices

Checked 2026-11-06, mostly from third-party summaries of the providers' price lists. Every figure gets checked against the provider's own page before Phase 5, and this date changes when it is. Prices are for US regions.

### Control planes

| Cluster | Per hour | Notes |
|---|---|---|
| EKS | $0.10 | $0.60 while the cluster's Kubernetes version is in extended support |
| GKE Standard | $0.10 | A credit of $74.40 a month per billing account covers one zonal or Autopilot cluster |
| AKS, free tier | $0 | No financially backed SLA. The Standard tier is $0.10 and Premium $0.60 |
| k3d, k3s | $0 | Electricity only |

### Moving data

| Traffic | AWS | GCP | Azure |
|---|---|---|---|
| Into the cloud from the internet | Free | Free | Free |
| Within one zone | Free | Free | Free |
| Between zones in one region | $0.01/GB, billed on both sides, so $0.02 for each GB that crosses | $0.01/GB | $0.01/GB reported, with some regions free; not yet confirmed |
| Between regions in North America | About $0.02/GB | $0.01–0.02/GB depending on the regions; not yet confirmed | $0.02/GB |
| Out to the internet, first tier | $0.09/GB after 100 GB a month free | $0.12/GB on the Premium tier; about $0.085/GB on the Standard tier | $0.087/GB after 100 GB a month free |
| Through an AWS NAT gateway | $0.045/GB processed, on top of the above, plus $0.045 an hour per gateway | — | — |

### Smaller line items

- **Public IPv4 addresses on AWS:** $0.005 an hour each, in use or idle.
- **Not priced here yet:** Spot nodes, managed stores, volumes, load balancers and cloud logging. They're added here when Phase 5 settles the sizes, and the [cost meter](#the-cost-meter-planned) uses them from then on.

## Worked estimates

The numbers come from the [company brief](../company/brief.md#paper-scale), using the AWS prices above.

### The courier location stream crossing a cloud boundary

30,000 writes a second at about 200 bytes on the wire is 6 MB/s, or 21.6 GB an hour. Leaving AWS at $0.09/GB, that's about **$1.95 an hour**, or about $7.80 for a four-hour run. This is the number that makes `checkout-hybrid`-style splits of the tracking path expensive.

### Kafka replication across zones

A location topic with replication factor 3, one replica per zone, copies every produced byte to two other zones: 12 MB/s, or 43.2 GB an hour. At $0.02 for each GB that crosses, that's about $0.86 an hour. Two consumer groups reading from leaders add 8 MB/s of cross-zone reads (two thirds of their reads land in another zone), about $0.58 an hour, for **about $1.44 an hour** at peak.

Run continuously at the daily average (10,000 writes a second), that's about $350 a month for this one topic. Rack-aware follower fetching (Kafka's `client.rack`) lets consumers read from a replica in their own zone and removes the consumer share, about 40% of the total. That makes it a production-relevant experiment.

### Telemetry leaving a cloud

When `harness.observability` sits on the laptop, every span, log line and metric sample leaves the cloud. At 140 checkouts a second with about 20 spans each at about 500 bytes, traces alone are 1.4 MB/s, or about 5 GB and **$0.45 an hour**, before logs and metrics. Tail sampling in the collector, or keeping observability in the cloud for that run, cuts it.

### Container images through a NAT gateway

Nodes in private subnets pull images through the NAT gateway at $0.045/GB. An environment that pulls 20 GB of images pays about $0.90 in processing, on top of the gateway's hourly charge. Lab clusters put their nodes in public subnets (six nodes' addresses cost $0.03 an hour) or use an S3 gateway endpoint, which is free, plus endpoints for the container registry.

## The cost meter (planned)

A command-line tool in the harness that shows what an environment is expected to cost per hour, given what it's configured to run, and what it's costing while a test runs. Its numbers are estimates, not bills.

**Why build one.** Existing tools each cover part of the job (checked 2026-11-06):

- Infracost prices a Terraform plan before it's applied. Usage-based charges such as data transfer come from monthly volumes typed into a usage file, and it knows nothing about load plans or targets outside the cloud being planned.
- OpenCost runs inside a cluster and publishes live cost metrics to Prometheus: node, volume and load-balancer cost per hour, and network egress by zone, region and internet. It only sees a cluster that already exists, one cluster at a time.
- No open-source tool turned up that estimates data-transfer cost from a load plan and a service topology before a run.

So the meter stays thin. It adds what's missing (targets, placements, load plans) and reuses the rest: Infracost cross-checks the meter's prices for the Terraform parts in CI, and OpenCost feeds its live view in the clouds.

**Inputs:**

- the environment's [placement file](environments.md#placement-files);
- a machine-readable price table, with the source and check date of every price. When the meter lands, that table becomes the source of the price tables on this page, and a check keeps the two in sync;
- the `sim` topology, whose edges carry request and response sizes, replaced by the sizes measured from traces once a component is real;
- optionally, a load plan: stages with durations and arrival rates, kept as a data file that both k6 and the meter read, so the estimate and the run use the same numbers.

**Commands:**

| Command | Shows |
|---|---|
| `cost-meter estimate <environment>` | Expected cost per hour by line item (control planes, nodes by size class, addresses, gateways, managed stores) and by boundary for data movement, plus the total for the environment's time-to-live |
| `cost-meter estimate <environment> --plan <load plan>` | The same for each stage of the plan: the bytes crossing each boundary, which side is billed, and the cost of each stage and of the whole plan |
| `cost-meter watch <environment>` | A live terminal view during a run: estimated against live cost per hour, spend so far, projected spend at the time-to-live, and the budget |
| `cost-meter serve` | The same numbers as Prometheus metrics, so the run's Grafana dashboard shows cost per hour beside latency and errors |

**Where the live numbers come from:** OpenCost's metrics in each cloud cluster, plus the byte counters on the forwarding Services between targets, priced from the table. Targets with nothing to meter, such as the laptop, fall back to the estimate.

**A plan's estimate, for example.** This is a hypothetical split, with location ingest on AWS and the location history store on the laptop, under a plan that ramps to the peak courier rate. Only data leaving AWS is billed; the laptop's traffic into AWS is free.

```
$ cost-meter estimate tracking-split --plan load/plans/location-peak.yaml
stage       time    rate          billed boundary   GB     USD
ramp up     10 min  0 → 30,000/s  aws → laptop      1.8    0.16
peak        60 min  30,000/s      aws → laptop     21.6    1.94
ramp down   10 min  30,000/s → 0  aws → laptop      1.8    0.16
data movement                                      25.2    2.27
EKS control plane, 80 min                                  0.13
nodes                             priced once the size classes are set
```

Each line is rounded on its own, so the lines can differ from the total by a cent. The plan's estimate goes into the experiment report's cost section, next to the live and billed cost.

## Estimates before a run, bills after it

- **Before:** the driver runs `cost-meter estimate` for the environment and its load plan, and refuses to start if the total exceeds the environment's budget. Until the meter exists, Infracost and the worked estimates on this page stand in.
- **After:** billing data lags by hours, so a scheduled job adds the billed cost to the run's report once it arrives. It reads AWS costs by the `fa-environment` tag (activated as a cost allocation tag), GCP's billing export by label, and Azure costs by resource group. The report shows the estimate and the billed cost side by side, and a large gap between them is a finding.

## Open question

What the paper-scale system would cost per month in production, and which design choice controls the largest line. The brief's [assumptions](../company/brief.md#assumptions-to-challenge) ask the same question. Each slice's design doc answers it for its own slice, using the prices on this page.
