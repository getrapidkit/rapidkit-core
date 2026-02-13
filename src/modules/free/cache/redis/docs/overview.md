# Redis Cache Module Overview

The Redis Cache module provides production-ready async/sync Redis clients with connection pooling,
retry logic, and health monitoring for FastAPI and NestJS applications.

## Key Capabilities

- **Async and sync clients** – Connection pooling with automatic retry/backoff for resilient cache
  operations.
- **Health monitoring** – `/api/health/module/redis` endpoint reports connectivity, latency, and
  configuration status.
- **TLS support** – Encrypted connections for production Redis instances with certificate
  validation.
- **Framework adapters** – FastAPI dependency injection and NestJS injectable service with lifespan
  management.
- **Metadata inspection** – Runtime configuration diagnostics via `get_redis_metadata()` helper.
- **Vendor runtime** – Upgrade-safe architecture with vendor snapshots in `.rapidkit/vendor`
  directory.

## Module Components

- **Redis Client**: Async/sync clients with connection pooling
- **Health Checks**: Connectivity probes and latency monitoring
- **Framework Adapters**: FastAPI dependencies and NestJS services
- **Metadata Helpers**: Runtime configuration inspection
- **Vendor System**: Immutable vendor snapshots for safe upgrades

## Architecture

```
┌──────────────────┐
│  Application     │
└──────────────────┘
         │
    ┌────────────────┐
    │  Redis Client  │ ← Connection pool
    │  (async/sync)  │
    └────────────────┘
         │
    ┌────────────────┐
    │  Retry Logic   │ ← Backoff strategy
    └────────────────┘
         │
    ┌────────────────┐
    │  Redis Server  │
    └────────────────┘
```

## Quick Start

### FastAPI

```python
from fastapi import FastAPI, Depends
from rapidkit.runtime.cache.redis import get_redis_client, AsyncRedisClient

app = FastAPI()


@app.get("/cache/{key}")
async def get_cached(key: str, redis: AsyncRedisClient = Depends(get_redis_client)):
    value = await redis.get(key)
    return {"key": key, "value": value}


@app.post("/cache/{key}")
async def set_cached(
    key: str, value: str, redis: AsyncRedisClient = Depends(get_redis_client)
):
    await redis.set(key, value, ex=3600)  # TTL: 1 hour
    return {"status": "cached"}
```

### NestJS

```typescript
import { Injectable } from '@nestjs/common';
import { RedisService } from './redis/redis.service';

@Injectable()
export class CacheService {
  constructor(private redis: RedisService) {}

  async getCached(key: string): Promise<string | null> {
    return await this.redis.get(key);
  }

  async setCached(key: string, value: string, ttl: number = 3600) {
    await this.redis.set(key, value, 'EX', ttl);
  }
}
```

## Configuration

Environment variables:

```bash
RAPIDKIT_REDIS_FORCE_URL=redis://localhost:6379/0
RAPIDKIT_REDIS_FORCE_HOST=localhost
RAPIDKIT_REDIS_FORCE_PORT=6379
RAPIDKIT_REDIS_FORCE_DB=0
RAPIDKIT_REDIS_FORCE_PASSWORD=your-password
RAPIDKIT_REDIS_FORCE_TLS=false
RAPIDKIT_REDIS_FORCE_RETRIES=3
RAPIDKIT_REDIS_FORCE_BACKOFF=1000
RAPIDKIT_REDIS_FORCE_TTL=3600
```

## Connection Pooling

Automatic connection pool management:

```python
from rapidkit.runtime.cache.redis import create_redis_pool

# Pool created with lifespan management
pool = await create_redis_pool(
    url="redis://localhost:6379/0", max_connections=50, decode_responses=True
)
```

## Retry Logic

Built-in retry with exponential backoff:

```python
# Automatic retry on connection failures
await redis.set("key", "value")  # Retries up to 3 times with backoff
```

## Health Monitoring

Health endpoint provides:

- Connection status (connected/disconnected)
- Latency measurement (ping time)
- Pool statistics (active/idle connections)
- Configuration details (host, port, database)

```json
{
  "status": "healthy",
  "module": "redis",
  "connection": {
    "connected": true,
    "host": "localhost",
    "port": 6379,
    "database": 0
  },
  "latency": {
    "ping_ms": 1.2
  },
  "pool": {
    "active": 5,
    "idle": 45,
    "max": 50
  }
}
```

Access at `/api/health/module/redis`.

## Metadata Inspection

Runtime diagnostics:

```python
from rapidkit.runtime.cache.redis import get_redis_metadata

metadata = get_redis_metadata()
print(f"Connected to: {metadata['url']}")
print(f"Retry policy: {metadata['retries']} attempts")
print(f"Default TTL: {metadata['ttl']} seconds")
```

## TLS Connections

Secure production Redis:

```bash
RAPIDKIT_REDIS_FORCE_URL=rediss://production.redis.com:6380/0
RAPIDKIT_REDIS_FORCE_TLS=true
```

## Vendor System

Upgrade-safe architecture:

- Vendor runtime stored in `.rapidkit/vendor/redis/<version>`
- Project wrappers remain thin and upgrade-safe
- Version upgrades are diffable and auditable

## Supported Frameworks

- **FastAPI**: Full async support with dependency injection
- **NestJS**: Injectable service with connection pooling
- **Custom**: Direct client instantiation for other frameworks

## Performance Features

- **Connection pooling**: Reuse connections efficiently
- **Pipelining**: Batch commands for reduced latency
- **Async operations**: Non-blocking cache access
- **Lazy connections**: Connect only when needed

## Getting Help

- **Overview**: This document
- **Usage Guide**: `docs/usage.md`
- **Migration Notes**: `docs/migration.md`

For issues and questions, visit our
[GitHub repository](https://github.com/getrapidkit/rapidkit-core).

## Security considerations

This module may touch sensitive data or privileged actions depending on how it is configured.

- Security: document configuration boundaries and expected trust assumptions.
- Threat model: consider abuse cases (rate limiting, replay, injection) relevant to your
  environment.

If you operate in a regulated environment, include a brief audit trail strategy (what you log,
retention, who can access).
