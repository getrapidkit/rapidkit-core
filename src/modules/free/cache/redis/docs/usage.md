# Usage

## Configure environment

Populate the generated `.env` entries or set environment variables at runtime:

```bash
REDIS_URL=redis://localhost:6379/0
REDIS_PRECONNECT=false
REDIS_CONNECT_RETRIES=3
REDIS_CONNECT_BACKOFF_BASE=0.5
```

When `REDIS_URL` is omitted the client composes a connection string from `REDIS_HOST`, `REDIS_PORT`,
`REDIS_DB`, and `REDIS_PASSWORD`.

## FastAPI integration

The module exposes helpers under `modules.free.cache.redis`:

```python
from modules.free.cache.redis import get_redis, redis_dependency, register_redis

app = FastAPI(lifespan=register_redis(preconnect=True))


@router.get("/cache")
async def cached_value(client=Depends(redis_dependency)):
    value = await client.get("some-key")
    return {"value": value}
```

## Health and diagnostics

Include the generated health router to surface status and configuration metadata:

```python
from src.health.redis import register_redis_health

register_redis_health(app)
```

The `/api/health/module/redis` endpoint responds with a payload similar to:

```json
{
    "status": "ok",
    "module": "redis",
    "url": "redis://user:***@cache.internal:6380/2",
    "connection": {"host": "cache.internal", "port": 6380, "db": 2, "use_tls": false},
    "retry": {"preconnect": true, "attempts": 5, "backoff_base": 0.5},
    "cache_ttl": 7200,
    "features": ["redis.async-client", "redis.sync-client", "fastapi.dependency", "redis.health-check"]
}
```

Fields containing secrets are masked automatically.

```

## Sync usage

Import `get_redis_sync` for synchronous workloads (background tasks, CLI jobs). The sync client
reuses a connection pool to minimise overhead.
```
