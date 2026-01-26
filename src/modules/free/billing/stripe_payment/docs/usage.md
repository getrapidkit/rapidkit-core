# Usage

Setup, configuration, and end-to-end flows for Stripe Payment.

## Quickstart

1. Install the module:

```bash
rapidkit add module stripe_payment
rapidkit modules lock --overwrite
```

2. Configure secrets (test mode for local dev):

```bash
export RAPIDKIT_STRIPE_API_KEY="sk_test_..."
export RAPIDKIT_STRIPE_WEBHOOK_SECRET="whsec_..."
```

3. Wire the FastAPI router:

```python
from fastapi import FastAPI

from src.modules.free.billing.stripe_payment.stripe_payment import build_router

app = FastAPI()
app.include_router(build_router(prefix="/stripe-payment"))
```

4. Validate health:

```bash
curl -s http://localhost:8000/stripe-payment/health
```

## Demo

Run the module demo harness:

```bash
python scripts/run_demo.py
```
