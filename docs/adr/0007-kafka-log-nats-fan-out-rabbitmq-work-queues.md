# ADR-0007: Kafka for the log, NATS for live fan-out, RabbitMQ for work queues

- **Status:** Proposed
- **Date:** 2026-11-01
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

The system moves three kinds of messages, with different needs:

- **Domain events and change data** (orders placed, payments captured, catalog changes, the location stream): durable, replayable, ordered per key, consumed by several independent readers. Up to 30,000 location events a second at the peak.
- **Live updates to connected clients** (courier positions, chat): low latency, fan-out to whoever is subscribed right now, short retention; losing an old position is fine, delivering it late is useless.
- **Units of work** (notification sends): each handled by exactly one worker, acknowledged individually, retried with delay, dead-lettered after repeated failure, sometimes prioritised.

## Options

### Option A: Kafka for everything

One system to run. Kafka is excellent for the log. It is awkward for per-message acknowledgement, delayed retry and priorities, and a topic per client subscription doesn't scale to hundreds of thousands of subscribers.

### Option B: NATS JetStream for everything

Light and fast, with streams, work queues and plain pub/sub in one product. Less common as a company-wide event log, with a smaller ecosystem for change data capture and stream processing.

### Option C: Redpanda or Pulsar instead of Kafka

Redpanda speaks the Kafka protocol with a different architecture. Pulsar adds tiered storage and built-in multi-tenancy. Kafka is the reference most of the ecosystem (Debezium, Flink, Kafka Connect) is built against.

### Option D: One tool per job

Kafka 4 in KRaft mode for the log, with Apicurio as the schema registry. NATS JetStream for live fan-out. RabbitMQ for the notification work queue.

## Decision

Option D. Kafka is the system of record for events; NATS and RabbitMQ are fed from Kafka by bridges and never hold the only copy of anything important. Services publish to Kafka through a transactional outbox, never by writing to a database and a broker separately.

## Lab stance and production stance

- **Lab stance:** three messaging models side by side make "log, pub/sub or queue?" a measured comparison instead of a recited one: throughput, latency, delivery guarantees and behaviour when a consumer dies.
- **Production stance:** many companies run Kafka plus one other system: a pub/sub layer for live updates, or a queue for jobs. Some run Kafka alone and accept the awkward parts. Three is more than most should operate.

## Consequences

- Three brokers to run, monitor and break. The minimal profile runs none of them; the standard profile adds Kafka; the full profile runs all three.
- Bridges between brokers are themselves failure points, and each gets a failure-mode row in its slice's design doc.
- Exactly-once *effects* come from idempotent consumers, not from broker guarantees.

## What would change my mind

If NATS or RabbitMQ never shows a measurable advantage over Kafka for its job in the comparison experiments, it is variety without a lesson, and it goes.

## How we'd know

The Phase 6 and Phase 9 experiments measure each broker on its own job and on the others' jobs: fan-out latency at 150,000 subscribers, and redelivery behaviour when a worker crashes mid-message.
