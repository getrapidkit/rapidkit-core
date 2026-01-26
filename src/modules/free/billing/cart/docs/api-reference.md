# API Reference

This reference documents the generated FastAPI surface and core runtime contracts.

## REST Endpoints

| Method   | Path                                   | Description                                                     |
| -------- | -------------------------------------- | --------------------------------------------------------------- |
| `GET`    | `/api/cart/{cart_id}`                  | Retrieve a cart snapshot. Creates an empty cart if none exists. |
| `POST`   | `/api/cart/{cart_id}/items`            | Add or update an item. Body: `CartItemPayload`.                 |
| `PUT`    | `/api/cart/{cart_id}/items/{sku}`      | Replace quantity or metadata for an existing item.              |
| `DELETE` | `/api/cart/{cart_id}/items/{sku}`      | Remove an item from the cart.                                   |
| `POST`   | `/api/cart/{cart_id}/discounts/{code}` | Apply a discount code.                                          |
| `DELETE` | `/api/cart/{cart_id}/discounts/{code}` | Remove a discount code.                                         |
| `POST`   | `/api/cart/{cart_id}/clear`            | Clear items and discounts while keeping configuration.          |
| `GET`    | `/api/health/module/cart`              | Return module health payload (status + metrics).                |

## Request Models

```jsonc
// CartItemPayload
{
	"sku": "string",
	"name": "string",
	"quantity": 1,
	"unit_price": "19.99",
	"currency": "USD",
	"metadata": {}
}

// DiscountPayload (apply)
{
	"force": false
}
```

## Response Shape

```jsonc
{
	"cart_id": "string",
	"items": [
		{
			"sku": "string",
			"name": "string",
			"quantity": 1,
			"unit_price": "19.99",
			"currency": "USD",
			"metadata": {}
		}
	],
	"discount_codes": ["WELCOME10"],
	"totals": {
		"currency": "USD",
		"subtotal": "19.99",
		"discount_total": "2.00",
		"tax_total": "1.28",
		"grand_total": "19.27",
		"item_count": 1,
		"requires_payment": true,
		"discounts": [
			{"code": "WELCOME10", "amount": "2.00", "description": "10% off"}
		]
	},
	"metadata": {},
	"updated_at": "2025-11-04T12:00:00.000000+00:00"
}
```

## Runtime Contracts

- `CartService` — Primary API for manipulating carts. Methods include `add_item`, `update_item`,
  `remove_item`, `apply_discount`, `clear`, `inspect`.
- `CartConfig` — Validates configuration input. Accepts dicts and environment overrides.
- `CartStore` protocol — Persistence contract used by the runtime. Default implementation is
  `InMemoryCartStore`.
- `CartSnapshot` — Immutable view returned by service methods. Use `.to_dict()` for JSON
  serialisation.

## Security

- All endpoints expect your platform-level authentication/authorization middleware. The module does
  not embed auth logic.
- Validate `cart_id` upstream to prevent enumeration. Consider scoping IDs by tenant or session.
- Discount codes should not be user-generated without validation—persist known codes server-side and
  audit usage.
