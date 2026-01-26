# Observability Core Usage Guide

This module ships a ready-to-mount observability surface (FastAPI router / NestJS controller) backed
by a small runtime facade.

## 1. Generate Artefacts

```bash
rapidkit add module observability_core
rapidkit modules lock --overwrite
```

When iterating on templates or switching frameworks, run the generator manually:

```bash
poetry run python -m src.modules.free.observability.core.generate fastapi .
poetry run python -m src.modules.free.observability.core.generate nestjs ./examples/observability-core-nest
```

## 2. Configure Defaults

For FastAPI projects the generator emits a defaults file at:

- `config/observability/observability_core.yaml`

You can tune the rendered defaults by setting the environment variables in `README.md` **before**
running the generator (they are consumed by `overrides.py`).

## 3. FastAPI Integration

Mount the generated router:

```python
from fastapi import FastAPI

from src.modules.free.observability.core.routers.observability_core import build_router

app = FastAPI()
app.include_router(build_router())
```

The router is exposed under `/observability-core/*`.

Smoke-test the surface:

```bash
curl -s http://localhost:8000/observability-core/health | jq .
curl -s http://localhost:8000/observability-core/metrics | jq .
curl -s http://localhost:8000/observability-core/events | jq .
curl -s http://localhost:8000/observability-core/traces | jq .
```

If you want raw Prometheus exposition, use:

```bash
curl -s http://localhost:8000/observability-core/metrics/raw
```

## 4. NestJS Integration

Import the generated module into your NestJS application module:

```typescript
import { Module } from "@nestjs/common";

import { ObservabilityCoreModule } from "./modules/free/observability/core/observability-core/observability-core.module";

@Module({
	imports: [ObservabilityCoreModule],
})
export class AppModule {}
```

Endpoints are exposed under `/observability-core/*` (see the API reference).

## 5. Testing

Generator/runtime/override unit tests live under:

- `tests/modules/free/observability/observability_core/*`

Run the module tests:

```bash
poetry run pytest tests/modules/free/observability/observability_core -q
```
