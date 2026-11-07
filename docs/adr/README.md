# Decision records

Each record follows the [template](../templates/adr.md): context, options, decision, a lab stance and a production stance, consequences, what would change my mind, and how we'd know. [ADR-0001](0001-record-decisions-with-lab-and-production-stances.md) explains the format.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-record-decisions-with-lab-and-production-stances.md) | Record decisions as MADR, with a lab stance and a production stance | Proposed |
| [0002](0002-fidelity-ladder-and-component-catalog.md) | Build through a fidelity ladder, tracked in a component catalog | Proposed |
| [0003](0003-local-runtime-k3d.md) | Run locally on k3d | Proposed |
| [0004](0004-language-policy.md) | Language policy: a closed list of nine, best fit first, spread as the tie-breaker | Proposed |
| [0005](0005-platform-contract.md) | One platform contract for every service | Proposed |
| [0006](0006-internal-grpc-edge-rest-bffs.md) | gRPC inside, REST at the edge behind one BFF per client type | Proposed |
| [0007](0007-kafka-log-nats-fan-out-rabbitmq-work-queues.md) | Kafka for the log, NATS for live fan-out, RabbitMQ for work queues | Proposed |
| [0008](0008-k6-load-and-chaos-mesh-faults.md) | k6 for load, Chaos Mesh and Toxiproxy for faults | Proposed |
| [0009](0009-terraform-over-opentofu.md) | Terraform, kept compatible with OpenTofu | Proposed |
| [0010](0010-licence-and-public-text-policy.md) | Licence and public-text policy | Proposed |
| [0011](0011-one-platform-many-targets-placement-files.md) | One platform on many targets, placed by a placement file | Proposed |
| [0012](0012-agent-working-memory-in-public.md) | Keep the agents' working memory in public | Proposed |
