# Usage

This guide walks through installing the Cart module, configuring pricing rules, and wiring the
generated runtime into a FastAPI service.

## Quickstart

1. **Install the module**
   ```bash
   rapidkit add module cart
   rapidkit modules lock --overwrite
   ```
1. **Regenerate the FastAPI variant**
   ```bash
   poetry run python -m src.modules.free.billing.cart.generate fastapi ./tmp/cart
   rsync -a ./tmp/cart/ ./  # or copy the emitted files into your project root
   ```
1. **Register the service and routes**
   ```python
   from fastapi import FastAPI

   from src.modules.free.billing.cart.cart import CartConfig
   from src.modules.free.billing.cart.routers.cart import register_cart

   app = FastAPI()

   cart_service = register_cart(
       app,
       config=CartConfig.from_mapping(
           {
               "defaults": {
                   "currency": "USD",
                   "tax_rate": "0.07",
                   "auto_apply_default_discount": True,
               }
           }
       ),
   )
   ```

`register_cart` wires the API routes, health endpoints, and stores the `CartService` on
`app.state.cart_service` for dependency injection.

1. **Send a test request**
   ```bash
   curl -X POST http://localhost:8000/api/cart/demo/items \
     -H 'Content-Type: application/json' \
     -d '{"sku":"widget","name":"Widget","quantity":2,"unit_price":"19.99","currency":"USD"}'
   ```

## Configuration

- Update `config/base.yaml` to adjust currency, tax rates, default discounts, and maximum SKU count.
- Use `config/snippets.yaml` to enable market-specific bundles or loyalty programmes.
- For generation-time overrides via environment variables, see the README `Runtime Customisation`
  section.

## Health Integration

- `register_cart` automatically registers `src.health.cart.register_cart_health`, so generated apps
  expose `/api/health/module/cart` without extra wiring.
- Health payload fields:
  - `status`: `ok`/`error`.
  - `metrics.total_carts`, `metrics.empty_carts`, `metrics.active_discounts`.
  - `metrics.config.currency` and `metrics.config.tax_rate` for visibility.

## Common Tasks

- **Apply a discount**: `CartService.apply_discount(cart_id="demo", code="WELCOME10")`.
- **Replace a cart**: `CartService.replace_items(cart_id, items=list_of_cart_items)` for bulk
  updates.
- **Inspect metrics**: `CartService.inspect()` returns counts for observability pipelines.
