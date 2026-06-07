# Workflow Engine Usage Guide

## Quickstart

```bash
rapidkit modules add workflow_engine --tier free --category tasks
python -m modules.free.tasks.workflow_engine.generate fastapi ./tmp/workflow_engine
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
