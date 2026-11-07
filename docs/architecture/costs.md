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
- **Not priced here yet:** Spot nodes, managed stores, volumes, load balancers and cloud logging. Infracost prices them from each Terraform plan ([environments](environments.md#lifecycle)), and they're added here when Phase 5 settles the sizes.

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

## Estimates before a run, bills after it

- **Before:** the driver prints Infracost's estimate for the Terraform plan, plus the data-movement estimate from the placement file and the traffic model. It refuses to start if the total exceeds the environment's budget.
- **After:** billing data lags by hours, so a scheduled job adds the billed cost to the run's report once it arrives. It reads AWS costs by the `fa-environment` tag (activated as a cost allocation tag), GCP's billing export by label, and Azure costs by resource group. The report shows the estimate and the billed cost side by side, and a large gap between them is a finding.

## Open question

What the paper-scale system would cost per month in production, and which design choice controls the largest line. The brief's [assumptions](../company/brief.md#assumptions-to-challenge) ask the same question. Each slice's design doc answers it for its own slice, using the prices on this page.
