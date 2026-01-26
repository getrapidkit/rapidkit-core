# Advanced Rate Limiting Patterns

This document dives into distributed deployments, overrides, and operational practices for the
RapidKit rate limiting module.

## 1. Operating with Redis

Enable the Redis backend to share quotas across multiple pods or services:

```bash
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_REDIS_URL=redis://user:password@redis.internal:6379/5
RATE_LIMIT_REDIS_PREFIX=tenant-a
```

- Use separate logical databases or prefixes per tenant to avoid key collisions.
- When running behind a managed Redis cluster, switch to TLS via `rediss://` and configure
  certificates at the platform layer.
- The generator automatically adds the `redis` Python dependency when the backend is enabled during
  overrides.

Verify connectivity at startup:

```python
from src.modules.free.security.rate_limiting.rate_limiting import (
    configure_rate_limiter,
    RateLimiterConfig,
)

config = RateLimiterConfig(backend="redis", redis_url="redis://redis.internal:6379/5")
limiter = configure_rate_limiter(config)
assert limiter.backend.__class__.__name__ == "RedisRateLimitBackend"
```

## 2. Weighted Costs and Priority Rules

Model expensive operations with weighted costs and priority ordering:

```python
from src.modules.free.security.rate_limiting.rate_limiting import (
    RateLimiter,
    RateLimiterConfig,
    RateLimitRule,
)

bulk_rule = RateLimitRule(
    name="bulk",
    limit=100,
    window_seconds=60,
    scope="identity",
    cost=10,
    priority=10,
)

config = RateLimiterConfig(rules=(bulk_rule,))
limiter = RateLimiter(config)

asyncio.run(
    limiter.consume(
        identity="org:42", method="POST", path="/bulk/upload", cost=bulk_rule.cost
    )
)
```

Rules are merged with defaults and sorted by `priority` (lower values win). Pair a strict burst rule
with a relaxed sustained rule to emulate token-bucket behaviour.

## 3. Multi-Tenant Overrides

Leverage `overrides.py` to mutate defaults during generation:

```python
from core.services.override_contracts import OverridesContext
from src.modules.free.security.rate_limiting.overrides import RateLimitingOverrides


class TenantAwareOverrides(RateLimitingOverrides):
    def before_render(self, context: OverridesContext) -> None:
        tenant = context.runtime.get("tenant", "default")
        if tenant == "enterprise":
            context.defaults["default_limit"] = 600
            context.defaults.setdefault("rules", []).append(
                {
                    "name": "enterprise-burst",
                    "limit": 250,
                    "window_seconds": 30,
                    "priority": 25,
                }
            )
```

Overrides apply to both FastAPI and NestJS variants, keeping cross-framework policies aligned.

## 4. Custom Identity Resolution

The generated FastAPI dependency resolves identity in the order header → forwarded IP → socket peer.
Override it for tenant-aware quotas:

```python
from fastapi import Depends, Request
from src.modules.free.security.rate_limiting.rate_limiting import RateLimitResult
from src.modules.free.security.rate_limiting.rate_limiting.dependencies import (
    get_rate_limiter_instance,
    rate_limit_dependency,
)

default_limit = rate_limit_dependency()


async def tenant_identity_limit(
    request: Request,
    rate_result: RateLimitResult = Depends(default_limit),
    limiter=Depends(get_rate_limiter_instance),
) -> RateLimitResult:
    tenant = request.headers.get("X-Tenant")
    if tenant:
        return await limiter.consume(
            identity=f"tenant:{tenant}",
            method=request.method,
            path=request.url.path,
            raise_on_failure=False,
        )
    return rate_result
```

Alternatively, set `RATE_LIMIT_IDENTITY_HEADER` or `RATE_LIMIT_TRUST_FORWARDED_FOR` to change
behaviour without custom code.

## 5. Observability Hooks

- `RateLimitResult.to_headers` produces standard headers for logging/monitoring.
- `get_rate_limiter_metadata()` exposes sanitized configuration for dashboards and health endpoints.
- Capture decisions at the edge by logging the `bucket`, `allowed`, and `retry_after` fields.

## 6. Safe Rollouts

- Record baseline metrics (allowed vs blocked counts) before adjusting limits.
- Use canary deployments when switching from memory to Redis to validate TTLs and key patterns.
- Run `poetry run pytest tests/modules/free/security/rate_limiting -q` and regenerate variants after
  changing templates.
