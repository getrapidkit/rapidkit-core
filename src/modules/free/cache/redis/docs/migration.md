# Migration guide

## Migrating from legacy cache helpers

1. Remove direct imports of `aioredis` or `redis.StrictRedis` from your codebase.
1. Import helpers from `src.modules.free.cache.redis` instead (`get_redis`, `RedisClient`).
1. Update environment variables to the canonical names documented in `config/base.yaml`.
1. If you previously instantiated clients per request, replace that logic with the provided FastAPI
   dependency or lifespan hook.

## Replacing custom health checks

The new `health_probe_redis.snippet.j2` registers a probe automatically. Remove any bespoke Redis
probes once the snippet has been applied.
