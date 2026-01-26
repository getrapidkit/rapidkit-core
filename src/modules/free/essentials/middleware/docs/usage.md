# Middleware Module Usage Guide

## Overview

The RapidKit Middleware module provides HTTP middleware components for FastAPI applications,
including request timing, service headers, and CORS support.

## Installation

```bash
rapidkit add module middleware
```

This will generate:

- `src/modules/free/essentials/middleware/middleware.py` - Main middleware implementations
- `src/health/middleware.py` - Health check endpoint
- `tests/modules/free/essentials/middleware/test_middleware_integration.py` - Integration tests

## Quick Start

### Basic Usage

After installation, register middleware in your FastAPI application:

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

### Available Middleware

The module provides three middleware components:

1. **ProcessTimeMiddleware** - Adds `X-Process-Time` header with request processing time
1. **ServiceHeaderMiddleware** - Adds `X-Service` header with service name
1. **Custom Header Middleware** - Adds `X-Custom-Header: RapidKit` to all responses

## Testing Middleware

Test your middleware is working:

```bash
# Start your application
poetry run dev

# Check headers
curl -I http://localhost:8000/api/v1/health

# You should see:
# X-Process-Time: 0.001234
# X-Service: My Service
# X-Custom-Header: RapidKit
```

## Health Check Endpoint

The module provides a dedicated health check at `/health/middleware`:

```bash
curl http://localhost:8000/health/middleware
```

Response:

```json
{
  "status": "ok",
  "module": "middleware",
  "version": "0.1.0",
  "middleware_count": 3,
  "checked_at": "2025-10-24T08:30:00.000Z"
}
```

## Customization

### Disable Specific Middleware

Edit `src/modules/free/essentials/middleware/middleware.py` and comment out unwanted middleware:

```python
def register_middleware(app: FastAPI) -> None:
    # app.add_middleware(ProcessTimeMiddleware)  # Disabled
    app.add_middleware(ServiceHeaderMiddleware, service_name=app.title)
```

### Enable CORS

Uncomment CORS configuration in `src/modules/free/essentials/middleware/middleware.py`:

```python
from starlette.middleware.cors import CORSMiddleware


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

### Custom Service Name

Override the default service name:

```python
app.add_middleware(ServiceHeaderMiddleware, service_name="Custom Name")
```

## Integration Tests

Run the generated integration tests:

```bash
poetry run pytest tests/modules/free/essentials/middleware/test_middleware_integration.py -v
```

Tests cover:

- Middleware imports
- Header injection
- Request/response flow
- Error handling
- Registration order

## Next Steps

- [Advanced Configuration](advanced.md)
- [Troubleshooting](troubleshooting.md)
- [Migration Guide](migration.md)
