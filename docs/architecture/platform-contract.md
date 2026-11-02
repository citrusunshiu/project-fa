# Platform contract

Every service meets this contract, whatever its language. It is what makes nine languages affordable: a new language costs one service template that already meets the contract, not one rewrite per concern. [ADR-0005](../adr/0005-platform-contract.md) is the decision behind it.

The numbers below are starting defaults. Experiments are expected to change them, and each change cites the report that justified it.

## Lifecycle

- **`GET /healthz`** returns 200 while the process can do work. It checks nothing downstream, so a slow database never gets a healthy pod killed.
- **`GET /readyz`** returns 200 only when the service can serve traffic: config loaded, required connections open, warm-up done.
- **Graceful shutdown on SIGTERM.** Fail readiness first, keep serving in-flight requests while the endpoints update (5 s), drain, then exit within 25 s, inside Kubernetes' default 30-second grace period.
- **Config comes from the environment.** No config files baked into images; secrets come from mounted files.

## Telemetry

- **Traces, metrics and logs through OpenTelemetry**, exported over OTLP to the collector. W3C trace context propagates on every inbound and outbound call, including through Kafka headers.
- **Metrics:** request rate, errors and duration as histograms (never averages) per endpoint, plus saturation for every pool and queue: connections in use, waiters, queue depth.
- **Logs:** structured JSON, one event per line, with the trace and span IDs. No personal data in logs, even fake personal data, so the habit holds.
- **Resource attributes:** `service.name`, `service.version`, `deployment.environment`, and the component's fidelity level, so dashboards can tell simulated components from real ones.

## Deadlines and timeouts

- **Every inbound request has a deadline.** The edge sets one (checkout: 2 s; reads: 500 ms). Services propagate the remaining budget downstream: gRPC deadlines internally, and an `x-request-deadline` header at HTTP boundaries.
- **Every outbound call has a timeout**, the smaller of the remaining deadline and the dependency's own limit. No call ever waits indefinitely.
- **Work stops when the deadline passes.** A request whose caller has given up is cancelled, not completed.

## Retries

One shared policy, implemented once per language template:

- **Only retry what is safe to repeat:** reads, and writes that carry an idempotency key.
- **Only retry transient failures:** `UNAVAILABLE`, `RESOURCE_EXHAUSTED` with a retry hint, connection resets. Never `DEADLINE_EXCEEDED` from the caller's own deadline.
- **At most 3 attempts,** with exponential backoff and full jitter (base 50 ms, cap 1 s), never past the deadline.
- **A retry budget per client:** retries may add at most 10% to the request rate. Above that, calls fail fast instead of retrying. This is what stops a slow dependency from turning into a retry storm, and Phase 1's second experiment measures it.
- **Retries happen at one layer only,** the caller closest to the failure. The edge does not retry what a service already retried.

## Idempotency

- **Every write accepts an `Idempotency-Key`** (a header at the edge, a request field internally).
- **The key lives in the owning service's database, written in the same transaction as the effect.** Never in a cache, where an evicted key turns a retry into a double charge.
- **A repeated key returns the original result.** A repeated key with a different request body is rejected with a conflict.
- **Keys are kept for 24 hours,** longer than any client's retry window.
- **Event consumers deduplicate by event ID** in the same transaction as their effect, because Kafka delivers at least once.

## Contracts

- **Internal APIs are gRPC with protobuf,** managed with `buf`: lint and breaking-change checks run in CI.
- **The edge is REST and JSON,** served by one backend-for-frontend per client type ([ADR-0006](../adr/0006-internal-grpc-edge-rest-bffs.md)).
- **Events are protobuf with schemas in the registry** (Apicurio), checked for backward compatibility before a producer ships.

## Store switch

Every service with state can run against an in-memory store or the real one, selected by `STORE=memory` or `STORE=real`. The minimal profile runs without heavy databases, and unit tests need no containers. The in-memory store must honour the same idempotency and ordering rules, or the switch hides bugs.

## Fault endpoints

Each service exposes fault toggles, gated by a flagd flag (`chaos.<service>.enabled`) that is off by default:

- **`POST /chaos/latency`** adds a fixed or distributed delay to some or all requests;
- **`POST /chaos/status`** makes some fraction of requests fail with a given status code;
- **`POST /chaos/health`** makes `/healthz` or `/readyz` fail.

These complement Chaos Mesh, which works below the application; they let an experiment break one dependency's behaviour precisely without touching the network.

## Security baseline

- **Mutual TLS between services,** provided by the mesh; services don't handle certificates.
- **Every request carries an identity.** End-user tokens come from Keycloak through the edge; service identities come from the mesh.
- **Authorization checks go through OpenFGA,** not ad-hoc role checks in each service.
- **Network policy denies by default;** each service's chart declares what it may call.

## Shipping

- **One container image per service,** built from its language template, running as non-root on a read-only root filesystem.
- **One Helm chart per service,** built on a shared library chart, so health probes, resources, telemetry and network policy look the same everywhere.
- **A language's first service ships with its template and its CI job,** in the same change.
