# Troubleshooting

Use this guide to resolve the most common Cart module issues.

## Diagnostics

- **Health endpoint fails** — Hit `/api/health/module/cart` and inspect the `status`/`metrics`. An
  `error` status often indicates a misconfigured discount rule or persistence failure. Enable debug
  logs with `RAPIDKIT_LOG_LEVEL=DEBUG`.
- **Unexpected totals** — Verify incoming prices are strings or decimals. Mixing floats can
  introduce rounding errors. Inspect the cart via `CartService.get_cart(cart_id).to_dict()`.
- **Discount not applied** — Confirm the discount code exists in `CartConfig.discount_rules` and
  that `minimum_subtotal` thresholds are satisfied.

## Remediation

- **Reset a stalled cart** — Call `CartService.clear(cart_id)` then retry the operation. This also
  removes dangling discounts.
- **Replace persistence layer** — If multiple processes need shared state, swap the default
  in-memory store with a Redis-backed implementation via overrides (see `docs/advanced.md`).
- **Generator errors** — Run `rapidkit doctor` to validate project dependencies. Template rendering
  issues usually stem from missing Jinja2 (installed via module requirements).
