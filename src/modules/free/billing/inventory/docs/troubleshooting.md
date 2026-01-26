# Troubleshooting

Catalogue common issues and diagnostics for inventory.

## Diagnostics

- Confirm the health endpoint responds:

```bash
curl -s http://localhost:8000/api/health/module/inventory
```

- If you see frequent 409/422 responses, validate SKU inputs and ensure pricing/currency defaults
  are configured in `config/inventory.yaml`.
