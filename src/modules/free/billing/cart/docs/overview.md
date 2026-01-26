# Cart Overview

The RapidKit Cart module manages shopping cart state, deterministic pricing, and discount
orchestration for checkout flows. It mirrors the stability guarantees of the `auth_core` module: a
strongly typed vendor runtime augmented by thin framework adapters and exhaustive health checks.

## Capabilities

- Maintain itemised carts with subtotal, discount, tax, and grand-total calculations.
- Support percentage or fixed-amount discounts (global, SKU-specific) backed by configuration.
- Enforce validation rules (max unique items, positive quantities, consistent currencies).
- Publish health metrics describing active carts, discount coverage, and configuration drift.
- Expose REST endpoints via FastAPI with predictable JSON serialisation.

## Architecture

- **Vendor runtime (`templates/base/`)** — Implements `CartService`, type definitions, discount
  engine, and health helpers. Generated files land in `.rapidkit/vendor/cart/<version>`.
- **Framework adapters (`templates/variants/`)** — FastAPI/NestJS wrappers that translate HTTP
  payloads into service calls. They register dependency wiring through `frameworks/*` helpers.
- **Source layout (`src/modules/free/billing/cart`)** — Canonical location for runtime, routers,
  health surface, and shared types across frameworks.
- **Configuration (`config/base.yaml`)** — Supplies defaults such as `currency`, `tax_rate`, and
  bundled discounts. Snippets can extend this configuration per market.
- **Testing (`tests/modules/free/billing/cart`)** — Mirrors production workflows: runtime
  validation, framework adapters, health reporting, and generator behaviour.

## Security considerations

This module may touch sensitive data or privileged actions depending on how it is configured.

- Security: document configuration boundaries and expected trust assumptions.
- Threat model: consider abuse cases (rate limiting, replay, injection) relevant to your
  environment.

If you operate in a regulated environment, include a brief audit trail strategy (what you log,
retention, who can access).
