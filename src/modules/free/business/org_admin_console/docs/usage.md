# Org Admin Console Usage Guide

## Quickstart

```bash
rapidkit modules add org_admin_console --tier free --category business
python -m modules.free.business.org_admin_console.generate fastapi ./tmp/org_admin_console
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
