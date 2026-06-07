# Queue Platform Usage Guide

## Quickstart

```bash
rapidkit modules add queue_platform --tier free --category tasks
python -m modules.free.tasks.queue_platform.generate fastapi ./tmp/queue_platform
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
