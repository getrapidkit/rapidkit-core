# Redis Cache Module Advanced Topics

This guide explains how to extend the Redis cache module beyond the default quick-start. It focuses
on runtime overrides, handling multiple Redis topologies, and surfacing richer telemetry for
production workloads.

## Override connection defaults safely

`RedisOverrides` reads the `RAPIDKIT_REDIS_FORCE_*` environment variables and mutates the generator
context before templates render. This allows you to change connection details without forking the
vendor runtime.

```python
from pathlib import Path
from src.modules.free.cache.redis.overrides import RedisOverrides

module_root = Path("src/modules/free/cache/redis")
overrides = RedisOverrides(module_root)
context = overrides.apply_base_context({"redis_defaults": {}})
print(context["redis_defaults"])  # mutated with env-driven values
```

Set values such as `RAPIDKIT_REDIS_FORCE_URL`, `RAPIDKIT_REDIS_FORCE_TLS`, or
`RAPIDKIT_REDIS_FORCE_RETRIES` to tune connectivity. Booleans accept `true/false`, integers are
clamped to non-negative values, and TLS can be toggled per environment.

## Inject extra configuration snippets

When you need bespoke configuration (for example, a provider-specific TLS block), point
`RAPIDKIT_REDIS_EXTRA_SNIPPET` to a file and RapidKit copies it into the generated project during
`post_variant_generation`.

```bash
export RAPIDKIT_REDIS_EXTRA_SNIPPET=snippets/redis_tls.py
export RAPIDKIT_REDIS_EXTRA_SNIPPET_DEST=config/redis_tls.py
export RAPIDKIT_REDIS_EXTRA_SNIPPET_VARIANTS='["fastapi"]'
```

The override honours the optional `RAPIDKIT_REDIS_EXTRA_SNIPPET_VARIANTS` filter so you can target
only FastAPI or NestJS renders.

## Manage multi-instance deployments

Create multiple named contexts by duplicating the module directory per role (for example,
`cache/session` and `cache/events`) or by feeding different override environments into the
generator:

```bash
RAPIDKIT_REDIS_FORCE_DB=1 \
rapidkit modules generate free/cache/redis fastapi ./build/redis-session

RAPIDKIT_REDIS_FORCE_DB=5 RAPIDKIT_REDIS_PROJECT_NAME="Events" \
rapidkit modules generate free/cache/redis fastapi ./build/redis-events
```

The `project_name` override updates generated logging namespaces and health metadata so each
deployment is easy to identify.

## Emit custom observability signals

The vendor runtime exposes `get_redis_metadata()` which already reports connection defaults and
enabled features. Call `describe_cache(extras=...)` from your app and pass additional key/value
pairs (latency, hit ratios, circuit breaker status) to enrich the health endpoint without modifying
the generated files.
