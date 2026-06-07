# Analytics Dashboard Usage Guide

## Quickstart

```bash
rapidkit modules add analytics_dashboard --tier free --category observability
python -m modules.free.observability.analytics_dashboard.generate fastapi ./tmp/analytics_dashboard
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
