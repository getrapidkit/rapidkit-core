# Middleware Module Overview

The Middleware module provides production-ready HTTP middleware components for FastAPI applications,
including request timing, service headers, and custom middleware registration.

## Key Capabilities

- **Request timing** – Automatic `X-Process-Time` header tracking request processing duration in
  milliseconds.
- **Service identification** – `X-Service` header injection for service mesh and load balancer
  routing.
- **Custom headers** – Extensible middleware for adding application-specific headers to responses.
- **Health monitoring** – `/api/health/module/middleware` endpoint reports active middleware and
  configuration status.
- **Framework integration** – Simple registration API for FastAPI applications with middleware
  ordering control.
- **Performance tracking** – Built-in timing metrics for performance monitoring and optimization.

## Module Components

- **ProcessTimeMiddleware**: Request duration tracking with millisecond precision
- **ServiceHeaderMiddleware**: Service name injection for routing and identification
- **Custom Header Middleware**: Extensible header injection framework
- **Health Checks**: Middleware status and configuration diagnostics
- **Registration API**: Simplified middleware setup with ordering control

## Architecture

```
┌────────────────────┐
│  FastAPI Request   │
└────────────────────┘
         │
    ┌────────────────────────┐
    │  Middleware Stack      │
    ├────────────────────────┤
    │  1. Process Time       │ ← Start timing
    │  2. Service Headers    │ ← Add X-Service
    │  3. Custom Headers     │ ← Add X-Custom
    │  4. Application Logic  │
    │  ← Response            │
    │  ← Add X-Process-Time  │ ← End timing
    └────────────────────────┘
         │
    ┌────────────────────┐
    │  HTTP Response     │
    └────────────────────┘
```

## Quick Start

### Basic Usage

```python
from fastapi import FastAPI
from src.modules.free.essentials.middleware.middleware import register_middleware
from src.health.middleware import (
    register_middleware_health,
)

app = FastAPI(title="My Service")

# Register all middleware
register_middleware(app)

# Register health endpoint
register_middleware_health(app)
```

### Response Headers

Automatic headers added to all responses:

```http
HTTP/1.1 200 OK
X-Process-Time: 42.5
X-Service: my-service
X-Custom-Header: RapidKit
Content-Type: application/json
```

## Middleware Components

### 1. Process Time Middleware

Tracks request processing time:

```python
from src.modules.free.essentials.middleware.middleware import ProcessTimeMiddleware

app.add_middleware(ProcessTimeMiddleware)

# GET /api/users
# Response headers:
# X-Process-Time: 15.3  # milliseconds
```

### 2. Service Header Middleware

Adds service identification:

```python
from src.modules.free.essentials.middleware.middleware import ServiceHeaderMiddleware

app.add_middleware(ServiceHeaderMiddleware, service_name="user-service")

# Response headers:
# X-Service: user-service
```

### 3. Custom Headers

Add application-specific headers:

```python
from src.modules.free.essentials.middleware.middleware import CustomHeaderMiddleware

app.add_middleware(
    CustomHeaderMiddleware,
    headers={
        "X-API-Version": "v1",
        "X-Environment": "production",
        "X-RateLimit-Remaining": "1000",
    },
)
```

## Configuration

Environment variables:

```bash
SERVICE_NAME=my-service
ENABLE_TIMING_HEADER=true
ENABLE_SERVICE_HEADER=true
CUSTOM_HEADERS='{"X-API-Version": "v1"}'
```

## Middleware Ordering

Control execution order:

```python
from fastapi import FastAPI
from src.modules.free.essentials.middleware.middleware import (
    ProcessTimeMiddleware,
    ServiceHeaderMiddleware,
    CustomHeaderMiddleware,
)

app = FastAPI()

# Middleware executes in reverse registration order
# (last registered runs first)
app.add_middleware(CustomHeaderMiddleware)
app.add_middleware(ServiceHeaderMiddleware, service_name="my-service")
app.add_middleware(ProcessTimeMiddleware)
```

## Custom Middleware

Create custom middleware:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response


class CustomRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Pre-processing
        request.state.custom_data = "value"

        # Call endpoint
        response: Response = await call_next(request)

        # Post-processing
        response.headers["X-Custom"] = "header-value"

        return response


app.add_middleware(CustomRequestMiddleware)
```

## Health Monitoring

Health endpoint reports middleware status:

```json
{
  "status": "healthy",
  "module": "middleware",
  "middleware": [
    {
      "name": "ProcessTimeMiddleware",
      "enabled": true,
      "order": 1
    },
    {
      "name": "ServiceHeaderMiddleware",
      "enabled": true,
      "service_name": "my-service",
      "order": 2
    }
  ],
  "configuration": {
    "timing_enabled": true,
    "service_header_enabled": true
  }
}
```

Access health status at `/api/health/module/middleware`.

## Performance Considerations

- **Minimal overhead**: Middleware adds ~0.1-0.5ms per request
- **Async execution**: Non-blocking middleware operations
- **Timing accuracy**: Microsecond precision with Python's `time.perf_counter`
- **Header size**: Minimal response size impact (~50-100 bytes)

## Use Cases

### Service Mesh Integration

```python
app.add_middleware(ServiceHeaderMiddleware, service_name="order-service")
# Service mesh can route based on X-Service header
```

### Performance Monitoring

```python
app.add_middleware(ProcessTimeMiddleware)
# Export X-Process-Time to Prometheus/Datadog
```

### API Versioning

```python
app.add_middleware(CustomHeaderMiddleware, headers={"X-API-Version": "2.0"})
```

### Rate Limiting Headers

```python
from src.modules.free.essentials.middleware.middleware import RateLimitHeaderMiddleware

app.add_middleware(RateLimitHeaderMiddleware, limit=1000, window=3600)
# Adds: X-RateLimit-Limit, X-RateLimit-Remaining
```

## Supported Frameworks

- **FastAPI**: Full middleware support with async/await
- **Starlette**: Compatible with all Starlette middleware
- **Custom**: Extend BaseHTTPMiddleware for custom behavior

## Security Considerations

- **Header injection**: Validate custom header values
- **Information disclosure**: Avoid exposing sensitive data in headers
- **CORS compatibility**: Middleware plays nice with CORS configuration
- **Header size limits**: Keep custom headers under 8KB total

## Getting Help

- **Usage Guide**: Detailed middleware setup and patterns
- **Advanced Guide**: Custom middleware development
- **Troubleshooting**: Common middleware issues
- **Migration Guide**: Upgrading from previous versions

For issues and questions, visit our [GitHub repository](https://github.com/getrapidkit/core).
