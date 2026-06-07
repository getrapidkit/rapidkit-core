# Forms Engine Usage Guide

## Quickstart

```bash
rapidkit modules add forms_engine --tier free --category business
python -m modules.free.business.forms_engine.generate fastapi ./tmp/forms_engine
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
