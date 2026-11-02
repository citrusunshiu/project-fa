# Design docs

One design doc per slice of the system, from the [template](../templates/design-doc.md). Each catalog entry names the doc that covers it. A slice doc covers several components because they share data and failure modes.

Ordered by the phase that first needs each one. Docs whose components are all proposed or optional are written once those components are accepted.

| Design doc | Components | First needed |
|---|---|---|
| `harness.md` | Simulator, invariant checkers, load scenarios, fleet runner, eBPF probes | Phase 1 |
| `checkout-and-payments.md` | Order saga, payments and ledger, fake processor, payouts; proposed: pricing; optional: subscriptions | Phase 2 |
| `flash-sales.md` | Inventory and flash-sale reservation | Phase 2 |
| `edge-and-identity.md` | Rate limiter, web and mobile BFFs; proposed: accounts | Phase 1 |
| `experimentation.md` | Experiment assignment; proposed: client event ingestion | Phase 1 |
| `ml-platform.md` | Delivery-time and ranking models; proposed: ML platform, LLM gateway | Phase 1 |
| `deals-feed.md` | Deals feed | Phase 1 |
| `media.md` | Photo pipeline | Phase 1 |
| `dispatch-and-tracking.md` | Dispatch matching, location ingest, live updates gateway; proposed: geo, courier service | Phase 6 |
| `browse-and-search.md` | Catalog API, search indexer, typeahead, crawler, back-office; proposed: reviews, price alerts, trending | Phase 7 |
| `ads.md` | Ad-click aggregation; proposed: sponsored-listing auction | Phase 7 |
| `group-cart.md` | Group cart | Phase 8 |
| `clients.md` | Web, Android and iOS apps, and the client behaviour spec they share | Phase 8 |
| `notifications.md` | Notifications | Phase 9 |
| `share-links.md` | Share links | Phase 10 |
| `lab.md` | Raft config and lock service; optional: distributed cache | Lab track |
| `merchant-operations.md` | Proposed: merchant operations; optional: outbound webhooks | Once accepted |
| `trust-and-safety.md` | Proposed: fraud and risk, support and refunds, privacy deletion | Once accepted |

`tools/check_catalog.py` lists the docs still to write.
