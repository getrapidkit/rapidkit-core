# Connector Pack Library Usage Guide

## Quickstart

```bash
rapidkit modules add connector_pack_library --tier free --category business
python -m modules.free.business.connector_pack_library.generate fastapi ./tmp/connector_pack_library
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
