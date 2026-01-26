# Troubleshooting

## "Connection refused"

Ensure the Redis service is reachable from the application container. Verify `REDIS_HOST`,
`REDIS_PORT`, and network policies. When using Docker Compose expose the Redis port to the
application network.

## TLS handshake failures

Set `REDIS_USE_TLS=true` and verify that the certificate authority is trusted by the container.
Provide `rediss://` URLs when connecting to managed services that require TLS (Azure Cache, AWS
Elasticache).

## Slow responses

Enable connection pooling by reusing the shared clients shipped with the module. Avoid instantiating
new clients per request. If latency persists, review eviction policies and key TTLs.

## Unknown configuration state

Call `get_redis_metadata()` or query `/api/health/module/redis` to confirm the resolved connection
URL, retry attempts, and cache TTL. Secrets are masked automatically, which makes the payload safe
to capture in logs when debugging.
