# API Reference

Describe HTTP endpoints, CLI commands, request/response schemas, and integration contracts for
inventory.

## Endpoints

- `GET /inventory/health`: health snapshot (totals, low-stock counts).
- `GET /inventory/items`: list items.
- `POST /inventory/items/{sku}`: create/update an item.
- `POST /inventory/items/{sku}/adjust`: adjust stock counts.

## Data Contracts

- `InventoryItem`: SKU, name, quantity, price, currency.
- Validation errors map to 422; conflicts map to 409.
- Security: protect all write endpoints with authn/authz and validate currency/pricing bounds.
