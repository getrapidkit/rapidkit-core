# CORS Module Usage Guide

The CORS (Cross-Origin Resource Sharing) module provides secure and configurable CORS middleware for
FastAPI applications, enabling controlled cross-origin requests from web browsers.

## Overview

This module generates FastAPI CORS middleware that helps you handle cross-origin requests securely.
It supports configurable origins, methods, headers, and credentials handling.

## Installation

```bash
rapidkit add module cors
```

This generates:

- `src/modules/free/security/cors/cors.py` - CORS middleware implementation and configuration
- Health check integration (when combined with health module)
- Integration tests for CORS functionality

## Quick Start

### Basic Setup

After installation, configure CORS in your FastAPI application:

```python
from fastapi import FastAPI
from src.modules.free.security.cors.cors import setup_cors, CORSConfig

app = FastAPI(title="My API")

# Option 1: Use default permissive configuration
setup_cors(app)

# Option 2: Custom configuration
cors_config = CORSConfig(
    allow_origins=["https://myapp.com", "https://app.myapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
setup_cors(app, cors_config)
```

### Configuration Options

The `CORSConfig` class supports:

- `allow_origins`: List of allowed origins (default: `["*"]`)
- `allow_credentials`: Whether to allow credentials (default: `true`)
- `allow_methods`: List of allowed HTTP methods (default: `["*"]`)
- `allow_headers`: List of allowed headers (default: `["*"]`)
- `expose_headers`: Headers to expose to browser (optional)
- `max_age`: Cache duration for preflight requests in seconds (default: `600`)

## Security Considerations

### Production Configuration

For production environments, always specify explicit origins:

```python
# ✅ Secure configuration
cors_config = CORSConfig(
    allow_origins=["https://myapp.com", "https://staging.myapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    max_age=3600,
)

# ❌ Avoid in production
cors_config = CORSConfig(allow_origins=["*"], allow_credentials=True)  # Too permissive
```

### Credentials and Wildcards

When `allow_credentials=True`, you cannot use `"*"` for origins. Specify explicit domains:

```python
# ✅ Correct with credentials
cors_config = CORSConfig(
    allow_origins=["https://trusted-domain.com"], allow_credentials=True
)

# ❌ Invalid combination
cors_config = CORSConfig(allow_origins=["*"], allow_credentials=True)  # This won't work
```

## Integration with Other Modules

### Health Module

When used with the health module, CORS is automatically configured for health endpoints:

```python
from src.health.cors import router as health_router
from src.modules.free.security.cors.cors import setup_cors

app = FastAPI()
setup_cors(app)
app.include_router(health_router, prefix="/health")
```

### Authentication Modules

CORS works seamlessly with authentication modules. Ensure `Authorization` header is allowed:

```python
cors_config = CORSConfig(
    allow_origins=["https://myapp.com"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)
```

## Testing

### Unit Testing

Test your CORS configuration:

```python
from src.modules.free.security.cors.cors import CORSConfig, create_cors_middleware


def test_cors_config():
    config = CORSConfig(allow_origins=["https://example.com"], allow_credentials=True)

    middleware = create_cors_middleware(config)
    assert middleware.allow_origins == ["https://example.com"]
    assert middleware.allow_credentials is True
```

### Integration Testing

The module includes integration tests that verify CORS headers are properly set:

```bash
# Run CORS integration tests
pytest tests/modules/integration/security/test_cors_integration.py
```

## Examples

### SPA Integration

For Single Page Applications:

```python
# Allow your SPA domain
cors_config = CORSConfig(
    allow_origins=["http://localhost:3000", "https://myapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    max_age=86400,  # 24 hours
)
```

### API Gateway

For API gateways or proxies:

```python
# Allow internal services and external clients
cors_config = CORSConfig(
    allow_origins=["https://api.myapp.com", "https://internal.myapp.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    max_age=3600,
)
```

## Troubleshooting

See the [troubleshooting guide](troubleshooting.md) for common issues and solutions.
