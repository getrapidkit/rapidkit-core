# Usage

This guide walks through installing the Inventory module, configuring stock rules, and exposing the
generated APIs inside a FastAPI service.

## Quickstart

1. **Install the module**
   ```bash
   rapidkit add module inventory
   rapidkit modules lock --overwrite
   ```
1. **Generate the FastAPI variant**
   ```bash
   poetry run python -m src.modules.free.billing.inventory.generate fastapi ./tmp/inventory
   rsync -a ./tmp/inventory/ ./  # or copy the emitted files into your project root
   ```
1. **Wire the runtime and routes**
   ```python
   from fastapi import FastAPI

   from src.health.inventory import register_inventory_health
   from src.modules.free.billing.inventory.inventory import (
       InventoryService,
       InventoryServiceConfig,
   )
   from src.modules.free.billing.inventory.routers.inventory import build_router

   app = FastAPI()

   inventory_service = InventoryService(
       InventoryServiceConfig.from_mapping(
           {
               "defaults": {
                   "default_currency": "USD",
                   "low_stock_threshold": 5,
               }
           }
       )
   )

   app.include_router(build_router(service=inventory_service))
   register_inventory_health(app)
   ```
1. **Test the HTTP surface**
   ```bash
   curl -X POST http://localhost:8000/inventory/items/widget \
   -H 'Content-Type: application/json' \
   -d '{"name":"Widget","quantity":10,"price":"19.99","currency":"USD"}'
   ```

## Configuration

- `config/inventory.yaml` captures stock defaults, pricing policies, notifications, and warehouse
  metadata. Adjust `defaults.low_stock_threshold` and `pricing` bounds to match production
  tolerances.
- Environment overrides are available through the generated `inventory_env` snippet. Enable it with
  `rapidkit snippets add inventory/inventory_env` to scaffold `.env` examples.
- The override contract (`overrides.py`) can mutate defaults at generation time if you need
  marketplace-specific rules baked into emitted projects.

## Health Integration

- `register_inventory_health` exposes `/api/health/module/inventory` and reports metrics for tracked
  SKUs, reservations, and low-stock breaches.
- The payload contains `status`, `totals`, and a `warehouses` section summarising active facilities.
  Attach it to observability dashboards to monitor replenishment workflows.

## Common Tasks

- **List inventory**: `inventory_service.list_items()` returns a mapping keyed by SKU with live
  availability counts.
- **Adjust stock**: `inventory_service.adjust_stock(sku="widget", delta=-1)` decrements reservations
  safely.
- **Inspect metrics**: `inventory_service.health_check()` surfaces totals that align with the health
  endpoint—useful for scheduled diagnostics.
