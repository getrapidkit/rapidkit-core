# Inventory Overview

The Inventory module provides an in-memory inventory and pricing facade with a stable API surface
and framework adapters for FastAPI and NestJS.

## Capabilities

- Create/update items by SKU with price/currency validation.
- List items and expose totals for monitoring and health.
- Adjust stock with explicit error conditions for underflow/reservation rules.

## Architecture

- Core runtime is `InventoryService` plus a small config model.
- FastAPI adapter exposes a router and a `register_inventory_health` helper.
- NestJS adapter exposes matching service/controller/module wrappers.

## Security considerations

This module may touch sensitive data or privileged actions depending on how it is configured.

- Security: treat SKU mutation endpoints as privileged and require authentication/authorization.
- Threat model: protect against stock manipulation and pricing tampering; rate-limit write
  endpoints.

If you operate in a regulated environment, include a brief audit trail strategy (what you log,
retention, who can access).
