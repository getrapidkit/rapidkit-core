# Tool Registry Usage Guide

## Quickstart

```bash
rapidkit modules add tool_registry --tier free --category ai
python -m modules.free.ai.tool_registry.generate fastapi ./tmp/tool_registry
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
