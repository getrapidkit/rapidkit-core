# Rate Limiting Module Usage Guide

This guide walks through installing, configuring, and operating the RapidKit rate limiting module in
generated projects. It covers both Python/FastAPI and NestJS targets and highlights the runtime
helpers that ship with the module.

## Prerequisites

- RapidKit CLI v1.11.0 or later
- Python 3.10+ for FastAPI projects
- Node.js 18+ for NestJS projects
- Optional: Redis 6+ for distributed quota storage

## Installation

```bash
# Add the module to an existing project (select framework variant interactively)
rapidkit add module rate_limiting

# Re-render vendor artefacts and snippets after upgrades
rapidkit modules lock --overwrite
```

Generated projects receive the shared runtime under
`src/modules/free/security/rate_limiting/rate_limiting.py` and framework-specific shims.

## Configuring Defaults

The module reads defaults from environment variables. Add the snippet bundle or define the values
manually:

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_BACKEND=memory        # memory | redis
RATE_LIMIT_DEFAULT_LIMIT=120
RATE_LIMIT_DEFAULT_WINDOW=60
RATE_LIMIT_RULES_JSON=[]         # Optional JSON array of extra rules
RATE_LIMIT_REDIS_URL=redis://localhost:6379/2
```

> Tip: Use `rapidkit snippets add rate_limiting/rate_limiting_env` to inject the managed `.env`
> samples.

## FastAPI Integration

```python
from fastapi import Depends, FastAPI, HTTPException
from src.modules.free.security.rate_limiting.rate_limiting.dependencies import (
    configure_rate_limiting,
    RateLimitContext,
    rate_limit_dependency,
)

app = FastAPI()


@app.on_event("startup")
async def configure_rate_limiter() -> None:
    configure_rate_limiting()


@app.get("/api/resources", dependencies=[Depends(rate_limit_dependency)])
async def list_resources(context: RateLimitContext) -> dict:
    if not context.allowed:
        raise HTTPException(status_code=context.status_code, detail=context.detail)
    return {"items": [...], "remaining": context.remaining}
```

- `configure_rate_limiting()` bootstraps the singleton limiter using environment values.
- `rate_limit_dependency` evaluates the request and exposes a `RateLimitContext` with metadata.
- Responses automatically include rate limit headers and (when blocked) `Retry-After`.

## NestJS Integration

```typescript
// rate-limiting.module.ts (generated)
import { Module } from '@nestjs/common';
import { RateLimitingService } from './rate-limiting.service';
import { RateLimitingGuard } from './rate-limiting.guard';

@Module({
	providers: [RateLimitingService, RateLimitingGuard],
	exports: [RateLimitingService, RateLimitingGuard],
})
export class RateLimitingModule {}

// users.controller.ts
@UseGuards(RateLimitingGuard)
@Controller('users')
export class UsersController {
	constructor(private readonly rateLimiter: RateLimitingService) {}

	@Get()
	findAll(@RateLimitContext() context: RateLimitContext) {
		return { items: [], remaining: context.remaining };
	}
}
```

- `RateLimitingGuard` enforces the configured rules and throws HTTP 429 when limits are exceeded.
- `RateLimitingService` proxies to the shared runtime through the generated vendor bridge.

## Defining Custom Rules

Augment rules at runtime by setting `RATE_LIMIT_RULES_JSON`:

```bash
RATE_LIMIT_RULES_JSON='[
	{
		"name": "login",
		"limit": 5,
		"window_seconds": 60,
		"methods": ["POST"],
		"routes": ["/auth/login"],
		"scope": "route-identity"
	}
]'
```

Rules are merged by name and ordered by `priority`. Use the overrides contract (`overrides.py`) for
install-time mutations.

## Exposing Metadata and Health Checks

- FastAPI router (`src/modules/free/security/rate_limiting/rate_limiting/router.py`) provides:
  - `GET /api/security/rate-limiting/status` – current quota snapshot.
  - `GET /api/security/rate-limiting/metadata` – sanitized configuration.
- NestJS exports a health helper that surfaces similar metadata for dashboards.

## Testing the Integration

```bash
# Python runtime and generator tests
poetry run pytest tests/modules/free/security/rate_limiting -q

# Verify FastAPI variant generation
poetry run python -m src.modules.free.security.rate_limiting.generate fastapi /tmp/rate-limit-fastapi

# Verify NestJS variant generation
poetry run python -m src.modules.free.security.rate_limiting.generate nestjs /tmp/rate-limit-nestjs
```

## Next Steps

- Review the advanced guide for Redis, weighted costs, and saga-style orchestration.
- Keep environment defaults in sync with production traffic patterns.
- Automate regression testing with the provided Pytest and generation commands.
