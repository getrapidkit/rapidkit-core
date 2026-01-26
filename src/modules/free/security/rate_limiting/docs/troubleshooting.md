# Rate Limiting Troubleshooting Guide

This guide lists frequent issues encountered when operating the RapidKit rate limiting module and
how to resolve them.

## Requests Always Return 429

**Symptoms**: Every request is blocked immediately after enabling the module.

**Checks**:

1. Verify that `RATE_LIMIT_DEFAULT_LIMIT` and `RATE_LIMIT_DEFAULT_WINDOW` are set to realistic
   values.

1. Confirm the effective configuration using:

   ```python
   from src.modules.free.security.rate_limiting.rate_limiting import (
       get_rate_limiter_metadata,
   )

   print(get_rate_limiter_metadata())
   ```

1. Inspect custom rules in `RATE_LIMIT_RULES_JSON` to ensure limits are greater than zero.

**Resolution**: Increase the default limit or adjust rule priorities so broader rules (e.g.
sustained) run after specialized ones.

## Redis Backend Cannot Connect

**Symptoms**: Startup logs include
`RuntimeError: Redis backend selected but RATE_LIMIT_REDIS_URL is not configured.`

**Checks**:

1. Ensure the `redis` package is installed (`poetry add redis` if necessary).
1. Set `RATE_LIMIT_REDIS_URL` and confirm credentials by running `redis-cli -u <url> PING`.
1. Validate DNS/network access from the application container.

**Resolution**: Provide a complete Redis URL, or switch back to the memory backend via
`RATE_LIMIT_BACKEND=memory`.

## Forwarded Identity Not Honoured

**Symptoms**: Clients behind load balancers share the same quota despite custom headers.

**Checks**:

1. Ensure the header is set: `RATE_LIMIT_IDENTITY_HEADER=X-Real-IP` (or similar).
1. If using `X-Forwarded-For`, enable `RATE_LIMIT_TRUST_FORWARDED_FOR=true` and confirm the proxy
   injects the header.
1. Review FastAPI middleware order; custom middleware that modifies headers must run before the
   dependency executes.

**Resolution**: Set or adjust the identity header, or implement a custom dependency that resolves
identity from your preferred source (see the advanced guide).

## Custom Rules Not Applied

**Symptoms**: Added rules in `RATE_LIMIT_RULES_JSON` never trigger.

**Checks**:

1. Verify the JSON is valid (`python -m json.tool <<< "$RATE_LIMIT_RULES_JSON"`).
1. Ensure rule `methods` and `routes` match the incoming request method and path prefix.
1. Confirm `priority` is lower (higher precedence) than the default rule if needed.

**Resolution**: Correct the JSON payload or adjust priority ordering; restart the application to
reload configuration.

## Tests Failing with Import Errors

**Symptoms**: Running the provided Pytest suite raises
`ModuleNotFoundError: No module named 'redis.asyncio'`.

**Resolution**: Install optional dependencies used in Redis tests:

```bash
poetry install --with redis
```

Alternatively, skip Redis-specific tests with `-k "not redis"` while investigating.

## Observability Headers Missing

**Symptoms**: Rate limit headers are absent from responses.

**Checks**:

1. Confirm the dependency is applied as a parameter (`Depends(rate_limit_dependency())`).
1. Ensure reverse proxies do not strip the custom headers.
1. For NestJS, verify the guard is applied at the controller or route level.

**Resolution**: Attach the dependency/guard to the relevant routes and whitelist the headers in
upstream load balancers.
