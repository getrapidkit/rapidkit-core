# Usage Billing Usage Guide

## Quickstart

```bash
rapidkit modules add usage_billing --tier free --category billing
python -m modules.free.billing.usage_billing.generate fastapi ./tmp/usage_billing
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
