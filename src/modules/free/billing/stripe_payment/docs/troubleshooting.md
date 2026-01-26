# Troubleshooting

Catalogue common issues and diagnostics for stripe payment.

## Diagnostics

- Confirm health endpoint reflects secret availability:

```bash
curl -s http://localhost:8000/stripe-payment/health
```

- If `has_api_key` is false, ensure `RAPIDKIT_STRIPE_API_KEY` is set in the environment used during
  generation/runtime.
- If webhook diagnostics fail, ensure `RAPIDKIT_STRIPE_WEBHOOK_SECRET` is set and signatures are
  verified.
