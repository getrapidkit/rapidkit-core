# Advanced Topics

Capture extensibility hooks, override patterns, and performance considerations.

## Overrides

`overrides.py` supports generation-time defaults (e.g. currency, reservation TTL) via
`RAPIDKIT_INVENTORY_*`.

For production persistence, replace the in-memory store behind `InventoryService` with a DB-backed
repository adapter.
