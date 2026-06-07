# Audit Policy Usage Guide

## Quickstart

```bash
rapidkit modules add audit_policy --tier free --category security
python -m modules.free.security.audit_policy.generate fastapi ./tmp/audit_policy
```

## Configuration

Document required configuration keys, defaults declared in `config/base.yaml`, and how snippets
augment the base context.

## Framework Examples

Describe how to integrate the generated FastAPI router and NestJS service into an application,
including health endpoints and dependency injection touchpoints.
