# Feature Flags Usage Guide

## Quickstart

```bash
rapidkit modules add feature_flags --tier free --category business
python -m modules.free.business.feature_flags.generate fastapi ./tmp/feature_flags
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
