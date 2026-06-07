# Document Pipeline Usage Guide

## Quickstart

```bash
rapidkit modules add document_pipeline --tier free --category business
python -m modules.free.business.document_pipeline.generate fastapi ./tmp/document_pipeline
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
