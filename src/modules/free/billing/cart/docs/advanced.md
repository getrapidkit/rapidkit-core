# Advanced Topics

This guide covers extension points, override strategies, and performance tuning for the Cart module.

## Overrides

- The module registers override hooks in `overrides.py` using
  `modules.shared.overrides.register_override`.
- Replace the default persistence layer by providing a custom `CartStore` implementation and
  registering it via the `cart.service_factory` override.
- Use `cart.health_enricher` to append additional observability data (e.g., inventory alerts) to the
  health payload.

## Custom Persistence

- Implement the `CartStore` protocol (methods: `get`, `set`, `delete`, `list_ids`).
- Ensure snapshots are deep-copied to avoid mutating cached references.
- Register the store through dependency injection in framework adapters or override the service
  factory.

## Discount Engine Extension

- Extend `CartConfig.discount_rules` with snippet packs or runtime overrides.
- Add custom rule evaluators by subclassing `DiscountRuleEvaluator` (exposed in the vendor runtime)
  and registering it via `CartService.register_discount_strategy`.

## Performance Considerations

- Default in-memory store suits low-volume workloads. For high throughput, back your store with
  Redis or a relational database.
- Quantisation uses `Decimal` with `ROUND_HALF_UP`; ensure upstream systems send prices as strings
  to avoid floating point precision drift.
- Health checks cut across store operations but are read-only; they can be gated behind feature
  flags in latency-sensitive deployments.
