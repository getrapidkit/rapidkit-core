# Approval Engine Usage Guide

## Quickstart

```bash
rapidkit modules add approval_engine --tier free --category business
python -m modules.free.business.approval_engine.generate fastapi ./tmp/approval_engine
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
