# Structured Logging & Observability Module Overview

The Logging module provides production-ready structured logging with correlation IDs, multi-sink
support, and framework adapters for FastAPI and NestJS applications.

## Key Capabilities

- **Structured logging** – JSON and text formatters with consistent field naming, timestamps, and
  log levels.
- **Correlation context** – Automatic request ID tracking across async operations and service
  boundaries.
- **Multi-sink architecture** – Simultaneous output to stderr, files, syslog, and custom handlers.
- **Async queue handlers** – Non-blocking log writing with configurable queue depth and overflow
  policies.
- **Secret redaction** – Automatic masking of sensitive values (passwords, tokens, API keys) in log
  output.
- **Sampling & filtering** – Rate-based sampling and custom filters to control log volume in
  production.
- **Health monitoring** – `/api/health/module/logging` endpoint exposes sink status, queue depth,
  and configuration.
- **Framework integration** – FastAPI middleware for automatic correlation context and NestJS
  service wiring.

## Module Components

- **Logger Runtime**: Core logging configuration with queue handlers
- **Formatters**: JSON, colored text, and structured text formatters
- **Context Middleware**: Request correlation ID injection and propagation
- **Health Checks**: Logging system status and diagnostics
- **Framework Adapters**: FastAPI middleware and NestJS logging service

## Architecture

```
┌──────────────────┐
│  Application     │
│  Code            │
└──────────────────┘
         │
    ┌────────────────┐
    │  get_logger()  │ ← Correlation context
    └────────────────┘
         │
    ┌────────────────────────────────┐
    │  Async Queue Handler           │
    │  (non-blocking writes)         │
    └────────────────────────────────┘
         │
    ┌────────────────────────────────┐
    │  Log Sinks                     │
    ├────────────┬──────────┬────────┤
    │  stderr    │  files   │ syslog │
    └────────────┴──────────┴────────┘
```

## Quick Start

```python
from fastapi import FastAPI
from src.modules.free.essentials.logging.logging import (
    get_logger,
    RequestContextMiddleware,
)

app = FastAPI()
app.add_middleware(RequestContextMiddleware)
logger = get_logger(__name__)


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    logger.info("Fetching user", extra={"user_id": user_id})
    # Logs include automatic request_id correlation
    return {"id": user_id, "name": "Alice"}
```

## Configuration

Environment variables:

```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_SINKS=stderr,file
LOG_FILE_PATH=/var/log/app.log
LOG_ASYNC_QUEUE=true
LOG_SAMPLING_RATE=1.0
LOG_ENABLE_REDACTION=true
OTEL_BRIDGE_ENABLED=false
METRICS_BRIDGE_ENABLED=false
RAPIDKIT_LOGGING_REQUEST_CONTEXT=true
```

## Log Formats

### JSON Format (production)

```json
{
  "timestamp": "2025-11-03T10:15:30.123Z",
  "level": "INFO",
  "logger": "app.services.users",
  "message": "User created successfully",
  "request_id": "abc123",
  "user_id": 42
}
```

### Colored Text Format (development)

```text
2025-11-03 10:15:30,123 | INFO | app.services.users | User created successfully | request_id=abc123 user_id=42
```

## Correlation Context

Automatic request tracking:

```python
from src.modules.free.essentials.logging.logging import get_logger, set_correlation_id

logger = get_logger(__name__)

# Request ID automatically added to all logs in this context
set_correlation_id("req-abc-123")
logger.info("Processing payment")  # Includes request_id=req-abc-123
```

## Supported Frameworks

- **FastAPI**: Middleware-based correlation context injection
- **NestJS**: Injectable logging service with Winston
- **Custom**: Direct logger access for other frameworks

## Log Sinks

Multiple simultaneous output destinations:

- **stderr**: Console output for container environments
- **file**: Rotating file handler with size/time-based rotation
- **syslog**: System log integration for centralized logging
- **custom**: Extend with CloudWatch, Datadog, or other handlers

## Secret Redaction

Automatic masking of sensitive data:

```python
logger.info(
    "User login",
    extra={
        "username": "alice",
        "password": "secret123",  # Automatically redacted
        "api_key": "sk_live_xxx",  # Automatically redacted
    },
)
# Output: password=***REDACTED***, api_key=***REDACTED***
```

## Performance Features

- **Async queue handlers**: Non-blocking log writes
- **Sampling**: Reduce log volume in high-traffic scenarios
- **Lazy formatting**: Deferred string formatting for performance
- **Batch writing**: Efficient disk I/O with buffered handlers

## Health & Monitoring

Built-in health endpoint monitors:

- Active sinks and their status
- Queue depth and overflow events
- Log level configuration
- Redaction filter status

Access health status at `/api/health/module/logging`.

## Observability Integration

- **OpenTelemetry**: Trace ID correlation support
- **Prometheus**: Log metrics (error rates, log volume)
- **Grafana**: Log aggregation and dashboards
- **ELK Stack**: Structured JSON output compatible with Elasticsearch

## Getting Help

- **Usage Guide**: Setup and common logging patterns
- **Advanced Guide**: Custom formatters and sinks
- **Troubleshooting**: Performance issues and debugging
- **Migration Guide**: Upgrading from Python logging

For issues and questions, visit our [GitHub repository](https://github.com/getrapidkit/core).

## Security considerations

This module may touch sensitive data or privileged actions depending on how it is configured.

- Security: document configuration boundaries and expected trust assumptions.
- Threat model: consider abuse cases (rate limiting, replay, injection) relevant to your
  environment.

If you operate in a regulated environment, include a brief audit trail strategy (what you log,
retention, who can access).
