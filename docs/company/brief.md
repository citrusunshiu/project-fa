# Company brief

## The company

**Project FA** is a super-app holding company. One shared internal platform serves several business lines, which is how large regional super-apps are built in practice. It starts with a single line, a **local marketplace with delivery**. Other lines can arrive later, each starting on paper, when a topic needs one: a video line, for example, if a design question needs video.

The platform team is a first-class part of the design. It owns identity, the edge, the event backbone, observability, experimentation and the paved road that every service follows (the [platform contract](../architecture/platform-contract.md)).

## Who uses it

| Actor | What they do |
|---|---|
| Customers | Browse local shops and restaurants, build a cart alone or with friends, check out, track the courier live, chat with the courier, rate the order |
| Couriers | Go online for a shift, get offered orders, accept them, stream their location, prove delivery with a photo, get paid out |
| Merchants | Manage menus and listings, accept orders and set prep times, run limited-time drops, buy sponsored placement, get paid out |
| Operations staff | Handle support and refunds, review fraud, manage merchants and zones through a back-office |

## Features, and the problem each one forces

Every feature is here because it forces a well-known design problem.

| Feature | The problem it forces | Classic design question |
|---|---|---|
| Browse and search shops, typeahead | Read-heavy caching; a search index fed by change data capture; prefix search | Typeahead |
| Merchant catalog ingest from menu feeds and websites | Politeness, deduplication, idempotent upserts, batch versus streaming | Web crawler |
| Group cart: friends add to one cart | Concurrent edits, CRDTs versus operational transforms, offline edits merging | Collaborative editing |
| Checkout: order, payment, ledger | Sagas, idempotency keys, exactly-once *effects*, double-entry bookkeeping | Payment system |
| Limited drops and flash sales | Hot-key contention, inventory reservation, admission queues | Flash sale, rate limiter |
| Courier dispatch | Geo indexing (H3), matching, exactly one courier per order (leases and fencing tokens) | Ride matching, lock service |
| Live tracking | High-rate writes, pub/sub fan-out to clients over WebSockets, backpressure | Live comments, presence |
| Customer–courier chat | Ordering within a conversation, presence | Chat |
| Notifications: push, SMS, email | Deduplication, rate caps, retries with a dead-letter queue, provider failover | Notification system |
| Scheduled orders, merchant and courier payouts | Durable timers, exactly-once job execution | Job scheduler |
| Sponsored listings | Impression and click aggregation, late events, windows | Ad-click aggregator |
| Menu photos, proof-of-delivery photos | Presigned uploads, an image pipeline | Object storage |
| Deals feed from followed shops | Fan-out on write versus on read, very popular merchants | News feed |
| Share links for shops and orders | Short IDs, redirect latency | URL shortener |
| Platform: event backbone, telemetry | Partitions, retention, consumer lag; a metrics pipeline | Distributed log, metrics |
| Platform: config and coordination | Consensus, implemented in the lab track | Key-value store, lock service |

### Proposed additions

These are under review for Phase 0. Each one starts on paper or simulated.

| Addition | What it adds |
|---|---|
| Accounts and profiles | Customer, courier and merchant profiles, saved addresses, payment-method references. Identity only does login |
| Geo | Geocoding, delivery zones, "do we deliver here?", and travel times from an open-source routing engine |
| Pricing, fees, taxes and promotions | Delivery and service fees, surge from supply and demand, tax, promo codes with idempotent redemption and abuse limits. Checkout can't total an order without it |
| Courier service | Onboarding, shift and availability state that dispatch reads, earnings and incentives that payouts read |
| Merchant operations | Order acceptance, prep times, store hours, marking items unavailable |
| Client event ingestion | Analytics events from the apps into the event log and the analytics store; experiment metrics depend on them |
| Fraud and risk | Payment fraud, promo abuse, account takeover; rules plus a model |
| Support and refunds | Tickets, refunds and credits as ledger reversals; a support assistant that answers from help docs |
| Privacy deletion | The right to erasure across every store and the event log (crypto-shredding, tombstones) |
| Reviews and ratings | Aggregation, fake-review detection, ranking by rating |
| Price-drop and back-in-stock alerts | Watchers fired from catalog change events into notifications |
| Trending and leaderboards | Top-K items per area over sliding windows; courier and merchant leaderboards |
| Sponsored-listing auction | Bidding, budgets, pacing |
| Models with a business reason | Delivery-time estimates, search reranking, fraud scoring, served and rolled out like any other change |
| Optional: outbound webhooks, subscriptions, resumable uploads, semantic search | Signed and replayable webhooks to merchant point-of-sale systems; a membership with recurring billing; chunked uploads; vector search beside keyword search |

## Paper scale

These are the made-up numbers the design docs argue from, in the style of back-of-envelope capacity estimation. Each one is derived below so it can be challenged.

| Quantity | Estimate | Rate it implies |
|---|---|---|
| Customers | 30 M registered, 6 M daily active, 1.5 sessions each a day | 9 M sessions a day |
| Orders | 3 M a day | ~35/s on average, ~140/s at the dinner peak |
| Browse and search reads | ~30 API reads per session | ~3,100/s on average, ~12,500/s at peak |
| Couriers | 150 k active at peak, a location every 5 s | 30,000 location writes/s at peak |
| Location history | ~10,000 writes/s averaged over the day | ~0.9 B points and ~50 GB raw a day, before replication and downsampling |
| Live tracking | ~150 k customers watching at peak, plus every active courier | ~300 k open WebSocket connections at peak |
| Ledger | ~4 entries per order | ~12 M entries a day; ~140/s average, ~560/s peak |
| A flash sale | 50 k attempts in 60 s on one item | ~830/s against **one row** |

### How the numbers were derived

- **Orders.** 3 M a day is a large regional delivery business, a bit under half the daily volume the largest US delivery platform reported for 2024. With 9 M sessions a day it assumes a third of sessions end in an order, which is high for e-commerce and plausible for delivery, where people open the app intending to buy.
- **The peak factor of 4.** If a quarter of the day's orders land in the two-hour dinner window, that window runs at 3× the daily average. The busiest minute within it adds roughly another third.
- **Couriers.** At 140 orders a second and about 35 minutes from order to door, roughly 290 k orders are in flight at the peak. Couriers carry about two orders a trip at peak, so about 150 k couriers are on shift.
- **Location writes.** 150 k couriers sending every 5 seconds is 30,000 writes a second at peak. Averaged over the day, with about 50 k couriers online, it's 10,000 a second, or 864 M points a day.
- **Location storage.** A point is about 60 bytes stored (a courier ID, a timestamp, latitude and longitude, accuracy, speed, heading, and key overhead). That's about 52 GB a day raw, roughly 155 GB a day with three replicas, and about 4.7 TB for 30 days kept at full resolution. That volume, written in time order and read by courier and time range, is what pushes this data into a wide-column store with expiry and downsampling.
- **Live tracking.** About half the customers with an order in flight keep the tracking screen open. Each receives a position every 5 seconds, so about 30,000 messages a second go out, alongside the courier connections coming in.
- **Ledger.** About four entries per order: the customer charge, the merchant payable, the courier payable and the platform fee. Throughput is not the hard part at 560 entries a second. Correctness is: double-entry balance, idempotency, and surviving the loss of a zone.
- **A flash sale.** 50 k attempts in a minute on one item is 830 a second against one inventory row. A single row under row locks serialises: if each update holds the lock for 1–2 ms including commit, that row tops out between 500 and 1,000 updates a second before the queue of waiters grows without bound. The flash-sale design question starts there.

### Storage, roughly

| Data | Size |
|---|---|
| Orders, items and their events | ~2 KB per order, ~6 GB a day, ~2.2 TB a year |
| Catalog | ~500 k merchants averaging 200 items at ~2 KB each, ~200 GB, plus the search index |
| Location history | ~4.7 TB replicated for 30 days at full resolution |
| Ledger | ~12 M entries a day at ~200 bytes, ~2.4 GB a day |
| Photos | Menu and proof-of-delivery photos, ~3 M a day at ~300 KB after resizing, ~900 GB a day |

## Lab scale

Runs drive what a laptop and short-lived cloud environments can reach. Some paths can run at full paper scale locally: 140 checkouts a second, for example, or 30,000 small location writes a second into a log. For the rest, the system under test is squeezed until its saturation point falls inside what the lab can drive, and the report records the scale factor. Phase 1 measures what each local profile can sustain.

## Service-level objectives (drafts)

Drafted per user journey. Each becomes real when its slice reaches F3.

| Journey | What is measured | Draft objective |
|---|---|---|
| Checkout | Order-placement requests that succeed | 99.95% over 28 days (about 20 minutes of budget); p99 under 1 s |
| Browse and search | Read requests that succeed | 99.9%; p99 under 300 ms |
| Location ingest | Location writes accepted | 99.9%; p99 under 200 ms |
| Live tracking | Age of the courier position on the customer's screen | p95 under 3 s |
| Dispatch | Ready orders offered to a courier within 60 s | 99% |
| Notifications | Sends handed to a provider within 30 s of the event | 99% |

The business invariants (the ledger sums to zero, no item is oversold, no order has two couriers) are not objectives with a budget. They must always hold, and the chaos suite checks them.

## Assumptions to challenge

- Is a one-in-three session conversion rate defensible, and what changes if it's one in ten?
- Does the 4× peak factor hold for lunch as well as dinner, and what happens in the busiest minute of a holiday evening?
- Is a 5-second location interval right? What do 2 seconds and 15 seconds cost, in writes and in tracking freshness?
- Which numbers would change the choice of data store, and by how much would they have to move?
- What is the most expensive number on this page, in money, and which design choice controls it?
