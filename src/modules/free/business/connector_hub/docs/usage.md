# Connector Hub Usage Guide

## Quickstart

```bash
rapidkit modules add connector_hub --tier free --category business
python -m modules.free.business.connector_hub.generate fastapi ./tmp/connector_hub
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
