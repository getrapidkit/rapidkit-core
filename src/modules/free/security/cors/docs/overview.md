# CORS Module Overview

The CORS (Cross-Origin Resource Sharing) module provides production-ready cross-origin request
handling for FastAPI and NestJS applications with fine-grained origin, method, and header controls.

## Key Capabilities

- **Origin control** – Whitelist specific domains or allow all origins with wildcard support.
- **Method filtering** – Control allowed HTTP methods (GET, POST, PUT, DELETE, etc.) per route or
  globally.
- **Header management** – Configure allowed request headers and exposed response headers.
- **Credentials support** – Enable/disable credentials (cookies, authorization headers) for
  cross-origin requests.
- **Preflight caching** – Control browser preflight request cache duration with
  `Access-Control-Max-Age`.
- **Health monitoring** – `/api/health/module/cors` endpoint reports CORS configuration and policy
  status.
- **Framework integration** – Automatic middleware registration for FastAPI and NestJS with
  environment-based configuration.

## Module Components

- **CORS Middleware**: Request/response header injection for CORS compliance
- **Origin Validator**: Domain matching with wildcard and regex support
- **Preflight Handler**: OPTIONS request processing with cache control
- **Health Checks**: CORS configuration diagnostics
- **Framework Adapters**: FastAPI middleware and NestJS guard integration

## Architecture

```
┌────────────────────────┐
│  Browser Request       │
│  Origin: example.com   │
└────────────────────────┘
         │
    ┌────────────────────────────┐
    │  CORS Middleware           │
    ├────────────────────────────┤
    │  1. Origin Check           │
    │  2. Method Validation      │
    │  3. Header Validation      │
    │  4. Preflight Handling     │
    └────────────────────────────┘
         │
    ┌────────────────────────────┐
    │  Application Logic         │
    └────────────────────────────┘
         │
    ┌────────────────────────────┐
    │  Response + CORS Headers   │
    │  Access-Control-Allow-*    │
    └────────────────────────────┘
```

## Quick Start

### FastAPI

```python
from fastapi import FastAPI
from src.modules.free.security.cors import register_cors

app = FastAPI()

# Register CORS with default settings
register_cors(app)

# Or with custom configuration
register_cors(
    app,
    allowed_origins=["https://example.com", "https://app.example.com"],
    allowed_methods=["GET", "POST", "PUT", "DELETE"],
    allowed_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
    max_age=3600,
)
```

### NestJS

```typescript
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Enable CORS
  app.enableCors({
    origin: ['https://example.com', 'https://app.example.com'],
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    credentials: true,
    maxAge: 3600
  });

  await app.listen(3000);
}
bootstrap();
```

## Configuration

Environment variables:

```bash
# Allow specific origins (comma-separated)
CORS_ALLOWED_ORIGINS=https://example.com,https://app.example.com

# Or allow all origins (development only!)
CORS_ALLOW_ALL_ORIGINS=true

# Allowed HTTP methods
CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS

# Allowed request headers
CORS_ALLOWED_HEADERS=Content-Type,Authorization,X-Requested-With

# Exposed response headers
CORS_EXPOSED_HEADERS=X-Total-Count,X-Page-Number

# Allow credentials (cookies, auth headers)
CORS_ALLOW_CREDENTIALS=true

# Preflight cache duration (seconds)
CORS_MAX_AGE=3600
```

## Origin Patterns

### Specific Domains

```python
register_cors(
    app,
    allowed_origins=[
        "https://example.com",
        "https://app.example.com",
        "https://admin.example.com",
    ],
)
```

### Wildcard Subdomains

```python
register_cors(
    app,
    allowed_origins=[
        "https://*.example.com",  # Matches all subdomains
        "https://example.com",  # Also allow root domain
    ],
)
```

### Regex Patterns

```python
import re

register_cors(app, allowed_origin_regex=r"https://.*\.example\.com")
```

### Allow All (Development Only)

```python
register_cors(app, allow_all_origins=True)  # ⚠️ Never use in production!
```

## Method Control

Restrict HTTP methods:

```python
register_cors(app, allowed_methods=["GET", "POST"])  # Only allow GET and POST
```

## Header Management

### Allowed Request Headers

Control which headers clients can send:

```python
register_cors(
    app, allowed_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"]
)
```

### Exposed Response Headers

Control which headers browsers can access:

```python
register_cors(
    app, exposed_headers=["X-Total-Count", "X-Page-Number", "X-RateLimit-Remaining"]
)
```

## Credentials Support

Enable cookies and authorization headers:

```python
register_cors(
    app,
    allow_credentials=True,
    allowed_origins=["https://example.com"],  # Must be specific origins
)
```

**Note**: When `allow_credentials=True`, you **cannot** use `allow_all_origins=True`. Browsers
require specific origins.

## Preflight Requests

Control OPTIONS request caching:

```python
register_cors(app, max_age=3600)  # Cache preflight response for 1 hour
```

## Response Headers

CORS middleware adds these headers:

```http
Access-Control-Allow-Origin: https://example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Expose-Headers: X-Total-Count
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 3600
```

## Health Monitoring

Health endpoint reports CORS configuration:

```json
{
  "status": "healthy",
  "module": "cors",
  "configuration": {
    "allowed_origins": [
      "https://example.com",
      "https://app.example.com"
    ],
    "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
    "allow_credentials": true,
    "max_age": 3600
  },
  "metrics": {
    "preflight_requests_last_hour": 42,
    "blocked_requests_last_hour": 0
  }
}
```

Access health status at `/api/health/module/cors`.

## Troubleshooting

### Common Issues

**Browser error: "No 'Access-Control-Allow-Origin' header"**

```python
# Ensure origin is in allowed list
register_cors(app, allowed_origins=["https://your-frontend.com"])
```

**Credentials not working**

```python
# Must use specific origins, not wildcard
register_cors(
    app, allow_credentials=True, allowed_origins=["https://example.com"]  # Not "*"
)
```

**Custom headers blocked**

```python
# Add custom headers to allowed list
register_cors(app, allowed_headers=["Content-Type", "Authorization", "X-Custom-Header"])
```

## Production Best Practices

1. **Never allow all origins in production**

   ```python
   # ❌ Bad
   allow_all_origins = True

   # ✅ Good
   allowed_origins = ["https://example.com"]
   ```

1. **Use environment-specific configuration**

   ```python
   import os

   ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
   register_cors(app, allowed_origins=ALLOWED_ORIGINS)
   ```

1. **Minimize exposed headers**

   ```python
   # Only expose what frontend needs
   exposed_headers = ["X-Total-Count"]
   ```

1. **Set appropriate preflight cache**

   ```python
   # Cache for 1 hour in production
   max_age = 3600
   ```

## Supported Frameworks

- **FastAPI**: Full middleware support with async/await
- **NestJS**: Built-in CORS with platform-specific adapters
- **Starlette**: Compatible with Starlette CORS middleware
- **Custom**: Manual header injection for other frameworks

## Security Considerations

- **Origin validation**: Strict domain matching prevents unauthorized access
- **Credentials isolation**: Credential support requires specific origins
- **Header control**: Limit allowed headers to prevent abuse
- **Preflight caching**: Reduces OPTIONS request overhead

## Performance Features

- **Preflight caching**: Browsers cache OPTIONS responses
- **Minimal overhead**: Header injection adds ~0.1ms per request
- **Async processing**: Non-blocking middleware execution

## Getting Help

- **Usage Guide**: Detailed CORS setup and patterns
- **Advanced Guide**: Custom origin validators and debugging
- **Troubleshooting**: Common CORS errors and solutions
- **Migration Guide**: Upgrading from previous versions

For issues and questions, visit our [GitHub repository](https://github.com/getrapidkit/core).
