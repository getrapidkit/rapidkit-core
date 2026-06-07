# Webhook Platform Usage Guide

## Quickstart

```bash
rapidkit modules add webhook_platform --tier free --category communication
python -m modules.free.communication.webhook_platform.generate fastapi ./tmp/webhook_platform
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
