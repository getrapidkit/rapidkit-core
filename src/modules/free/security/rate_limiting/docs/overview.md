# Rate Limiting Module Overview

The RapidKit rate limiting module delivers production-ready throttling for asynchronous and
synchronous APIs. It provides a shared runtime with memory and Redis backends, framework adapters
for FastAPI and NestJS, and observability hooks that keep quota enforcement transparent across
services.

## Key Capabilities

- **Flexible Backends**: Memory backend for single-instance deployments and Redis backend for
  distributed quotas.
- **Declarative Rules**: Priority-ordered rules with per-route, per-identity, and global scopes.
- **Framework Integrations**: FastAPI middleware and dependency helpers, plus NestJS guards and
  services.
- **Operational Telemetry**: Consistent headers, metadata endpoints, and optional Prometheus
  metrics.
- **Override Contract**: Install-time overrides for defaults, snippet injection, and vendor artefact
  extensions.

## Architecture Snapshot

```text
┌────────────────────────────┐
│  Application Endpoints     │
│ (FastAPI / NestJS routes)  │
└──────────────┬─────────────┘
               │
        ┌──────▼──────┐
        │ Integrations│  FastAPI dependency, NestJS guard
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │ RateLimiter │  Shared runtime (memory + Redis backends)
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │ Storage     │  In-memory buckets or Redis counters
        └─────────────┘
```

## Delivered Assets

| Path                                                                           | Purpose                                                          |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| `src/modules/free/security/rate_limiting/rate_limiting.py`                     | Shared runtime and backend implementations.                      |
| `src/modules/free/security/rate_limiting/rate_limiting/dependencies.py`        | FastAPI dependency/utility helpers.                              |
| `src/modules/free/security/rate_limiting/rate_limiting/router.py`              | Ready-to-use FastAPI router exposing health and metadata routes. |
| `src/modules/free/security/rate_limiting/rate-limiting/rate-limiting.guard.ts` | NestJS guard enforcing limits per request.                       |
| `config/base.yaml`                                                             | Defaults, features, and dependency manifests.                    |
| `templates/snippets/rate_limiting_env.snippet.j2`                              | Environment variable samples for generated projects.             |

## Supported Frameworks

- **FastAPI** via middleware, dependency injection, and router extensions.
- **NestJS** through guard, service, and configuration templates.
- **Headless Runtime** for custom integration using `RateLimiter` directly.

## Operational Highlights

- Emits standard headers (`X-RateLimit-*`, `Retry-After`) for compliant clients.
- Supports weighted costs, temporary blocking windows, and custom identity resolution.
- Provides metadata endpoints and Python helpers for dashboards and health checks.
- Integrates optional Redis backend with atomic counters and TTL semantics.

Consult the usage, advanced, and troubleshooting guides for detailed setup instructions and
operational runbooks.
