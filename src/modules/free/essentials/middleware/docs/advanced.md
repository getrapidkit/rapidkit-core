# Middleware Module - Advanced Configuration

## Custom Middleware Classes

### Creating Custom Middleware

Extend the base middleware pattern:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""

    async def dispatch(self, request: Request, call_next):
        import uuid

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

Register your custom middleware:

```python
from src.modules.free.essentials.middleware.middleware import register_middleware


def register_all_middleware(app: FastAPI):
    # Register built-in middleware
    register_middleware(app)

    # Add custom middleware
    app.add_middleware(RequestIDMiddleware)
```

## Middleware Order

Middleware executes in reverse order of registration. Last registered runs first:

```python
app.add_middleware(FirstMiddleware)  # Runs third
app.add_middleware(SecondMiddleware)  # Runs second
app.add_middleware(ThirdMiddleware)  # Runs first
```

## Performance Monitoring

### Detailed Timing Middleware

Track individual route performance:

```python
import time
from collections import defaultdict


class DetailedTimingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.timings = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        route = f"{request.method} {request.url.path}"
        self.timings[route].append(duration)

        # Add percentile timing header
        timings = self.timings[route]
        avg = sum(timings) / len(timings)
        response.headers["X-Route-Avg-Time"] = f"{avg:.4f}"

        return response
```

## Request Context

### Adding Context to Requests

Store request-scoped data:

```python
class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Add context
        request.state.user_id = None
        request.state.trace_id = generate_trace_id()
        request.state.start_time = time.time()

        response = await call_next(request)
        return response
```

Access in route handlers:

```python
@app.get("/profile")
async def get_profile(request: Request):
    trace_id = request.state.trace_id
    # Use trace_id...
```

## Error Handling Middleware

### Graceful Error Recovery

```python
import logging


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logging.error(f"Request failed: {exc}", exc_info=True)
            return Response(
                content={"error": "Internal server error"},
                status_code=500,
                media_type="application/json",
            )
```

## Security Middleware

### Security Headers

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"

        return response
```

## Rate Limiting

### Simple Rate Limiter

```python
from datetime import datetime, timedelta
from collections import defaultdict


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute=60):
        super().__init__(app)
        self.requests = defaultdict(list)
        self.limit = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Clean old requests
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > minute_ago
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.limit:
            return Response(content={"error": "Rate limit exceeded"}, status_code=429)

        self.requests[client_ip].append(now)
        return await call_next(request)
```

## Compression

### Response Compression

```python
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Testing Custom Middleware

```python
from fastapi.testclient import TestClient


def test_custom_middleware():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    def test_route():
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/test")

    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 36  # UUID length
```

## Best Practices

1. **Order Matters** - Security headers first, then CORS, then custom logic
1. **Async Preferred** - Use async middleware for I/O operations
1. **Keep It Fast** - Minimize processing in middleware
1. **Error Recovery** - Always handle exceptions gracefully
1. **Logging** - Log middleware errors but not every request
1. **Testing** - Write tests for custom middleware

## Related Documentation

- [Usage Guide](usage.md)
- [Troubleshooting](troubleshooting.md)
- [Migration Guide](migration.md)
