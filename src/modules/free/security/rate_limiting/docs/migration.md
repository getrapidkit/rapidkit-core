# Rate Limiting Module Migration Guide

This playbook helps teams transition from existing throttling solutions to the RapidKit rate
limiting module.

## Migrating from Custom FastAPI Middleware

### Before

```python
import time
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException

requests_per_ip: dict[str, list[float]] = defaultdict(list)

app = FastAPI()


@app.middleware("http")
async def naive_rate_limiter(request: Request, call_next):
    window_seconds = 60
    limit = 100
    now = time.time()
    ip = request.client.host if request.client else "anonymous"

    history = requests_per_ip[ip]
    requests_per_ip[ip] = [stamp for stamp in history if now - stamp < window_seconds]

    if len(requests_per_ip[ip]) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests")

    requests_per_ip[ip].append(now)
    return await call_next(request)
```

### After

```python
from fastapi import Depends, FastAPI
from src.modules.free.security.rate_limiting.rate_limiting import RateLimitResult
from src.modules.free.security.rate_limiting.rate_limiting.dependencies import (
    rate_limit_dependency,
)

app = FastAPI()


@app.get("/api/data")
async def read_data(_: RateLimitResult = Depends(rate_limit_dependency())) -> dict:
    return {"items": [...]}  # 429 raised automatically when exhausted
```

**Key improvements**

- Shared runtime with rule priority, weighted costs, and Redis support.
- Standard headers (`X-RateLimit-*`) for clients and observability.
- Configuration driven by environment and overrides instead of hard-coded constants.

## Migrating from Starlette-Limiter / SlowAPI

| Concern         | Starlette-Limiter / SlowAPI | RapidKit Rate Limiting             |
| --------------- | --------------------------- | ---------------------------------- |
| Backend         | Redis-only                  | Memory or Redis                    |
| Rule Definition | Decorator-based strings     | Structured `RateLimitRule` objects |
| Metrics         | Limited                     | Headers + metadata endpoint        |
| Overrides       | Not built-in                | Override contract + snippets       |

### Example Conversion

```python
@router.get("/auth/login")
@limiter.limit("5/minute")
async def login(): ...
```

Becomes:

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

No code changes are required as the dependency enforces the rule by name and HTTP metadata.

## Migrating NestJS Guards

### Before

```typescript
@UseGuards(ThrottlerGuard)
@Throttle(10, 60)
@Get('reports')
async findReports() {
	return this.service.findAll();
}
```

### After

```typescript
import { RateLimitRule } from './rate-limiting.guard';

@RateLimitRule('reports')
@UseGuards(RateLimitingGuard)
@Get('reports')
async findReports() {
	return this.service.findAll();
}
```

Add an override that defines the `reports` rule (`RATE_LIMIT_RULES_JSON` or overrides contract).

## Transition Checklist

1. **Inventory existing limits** – document current rules, scopes, and penalties.
1. **Model rules** in JSON or overrides; keep names stable to ease observability migration.
1. **Enable headers** in dashboards or API gateway policies to maintain visibility.
1. **Run automated tests** using `poetry run pytest tests/modules/free/security/rate_limiting -q`.
1. **Shadow test** the new limiter (memory backend) behind feature flags before enabling Redis.
1. **Monitor rollout** using `get_rate_limiter_metadata()` and application metrics to confirm
   parity.

## Rolling Back

- Switch `RATE_LIMIT_BACKEND` back to `memory` to isolate Redis issues.
- Remove custom overrides to return to module defaults.
- Use the module’s uninstall rollback strategy (`rapidkit modules remove rate_limiting`) if full
  removal is required.
