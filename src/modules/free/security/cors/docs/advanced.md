# CORS Advanced Configuration

This guide covers advanced CORS scenarios, custom middleware implementations, and complex
cross-origin setups.

## Custom CORS Middleware

### Extending CORSMiddleware

For complex scenarios, extend the built-in FastAPI CORSMiddleware:

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Response
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AdvancedCORSMiddleware(CORSMiddleware):
    """Advanced CORS middleware with logging and custom logic."""

    def __init__(self, *args, **kwargs):
        self.log_requests = kwargs.pop("log_requests", False)
        self.custom_headers = kwargs.pop("custom_headers", {})
        super().__init__(*args, **kwargs)

    async def dispatch(self, request: Request, call_next):
        # Log CORS requests if enabled
        if self.log_requests and request.method == "OPTIONS":
            logger.info(f"CORS preflight from {request.headers.get('origin')}")

        # Add custom headers to all responses
        response = await call_next(request)

        for header_name, header_value in self.custom_headers.items():
            response.headers[header_name] = header_value

        return response
```

### Conditional CORS

Apply different CORS policies based on request characteristics:

```python
from fastapi import Request
from src.modules.free.security.cors.cors import CORSConfig, setup_cors


class ConditionalCORS:
    """Apply different CORS policies based on conditions."""

    def __init__(self):
        self.policies = {
            "api": CORSConfig(
                allow_origins=["https://api-client.com"],
                allow_credentials=True,
                allow_methods=["GET", "POST"],
            ),
            "admin": CORSConfig(
                allow_origins=["https://admin.myapp.com"],
                allow_credentials=True,
                allow_methods=["GET", "POST", "PUT", "DELETE"],
            ),
            "public": CORSConfig(
                allow_origins=["*"], allow_credentials=False, allow_methods=["GET"]
            ),
        }

    def get_policy_for_request(self, request: Request) -> CORSConfig:
        """Determine CORS policy based on request path."""
        path = request.url.path

        if path.startswith("/admin"):
            return self.policies["admin"]
        elif path.startswith("/api"):
            return self.policies["api"]
        else:
            return self.policies["public"]


# Usage in FastAPI app
conditional_cors = ConditionalCORS()


@app.middleware("http")
async def conditional_cors_middleware(request: Request, call_next):
    # Apply appropriate CORS policy
    policy = conditional_cors.get_policy_for_request(request)

    # Set CORS headers manually for complex logic
    response = await call_next(request)

    origin = request.headers.get("origin")
    if origin and self.is_allowed_origin(origin, policy):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = str(
            policy.allow_credentials
        ).lower()
        response.headers["Access-Control-Allow-Methods"] = ", ".join(
            policy.allow_methods
        )
        response.headers["Access-Control-Allow-Headers"] = ", ".join(
            policy.allow_headers
        )

        if policy.max_age:
            response.headers["Access-Control-Max-Age"] = str(policy.max_age)

    return response
```

## Dynamic Origin Management

### Database-Backed Origins

Store allowed origins in database for dynamic management:

```python
from sqlalchemy.orm import Session
from typing import List


class CORSOriginManager:
    """Manage CORS origins dynamically from database."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_allowed_origins(self) -> List[str]:
        """Fetch allowed origins from database."""
        # Assuming you have a CORSOrigins table
        origins = self.db.query(CORSOrigins).filter_by(enabled=True).all()
        return [origin.domain for origin in origins]

    def add_origin(self, domain: str) -> None:
        """Add new allowed origin."""
        origin = CORSOrigins(domain=domain, enabled=True)
        self.db.add(origin)
        self.db.commit()

    def remove_origin(self, domain: str) -> None:
        """Remove allowed origin."""
        self.db.query(CORSOrigins).filter_by(domain=domain).delete()
        self.db.commit()


# Usage
origin_manager = CORSOriginManager(db_session)


@app.on_event("startup")
async def configure_cors():
    allowed_origins = origin_manager.get_allowed_origins()
    cors_config = CORSConfig(
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )
    setup_cors(app, cors_config)
```

### Environment-Based Origins

Configure origins based on deployment environment:

```python
import os
from typing import List


class EnvironmentCORSConfig:
    """CORS configuration based on environment."""

    @staticmethod
    def get_origins_for_env() -> List[str]:
        env = os.getenv("ENVIRONMENT", "development")

        if env == "production":
            return [
                "https://myapp.com",
                "https://app.myapp.com",
                "https://admin.myapp.com",
            ]
        elif env == "staging":
            return ["https://staging.myapp.com", "https://staging-admin.myapp.com"]
        else:  # development
            return [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
            ]


# Usage
cors_config = CORSConfig(
    allow_origins=EnvironmentCORSConfig.get_origins_for_env(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)
```

## Security Hardening

### Origin Validation

Implement strict origin validation:

```python
import re
from urllib.parse import urlparse


class SecureCORSConfig(CORSConfig):
    """CORS config with enhanced security validation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validate_configuration()

    def validate_configuration(self):
        """Validate CORS configuration for security."""
        # Ensure HTTPS in production
        if os.getenv("ENVIRONMENT") == "production":
            for origin in self.allow_origins:
                if not origin.startswith("https://"):
                    raise ValueError(f"Insecure origin in production: {origin}")

        # Prevent wildcard with credentials
        if self.allow_credentials and "*" in self.allow_origins:
            raise ValueError("Cannot use wildcard origins with credentials")

        # Validate origin format
        for origin in self.allow_origins:
            if origin != "*":
                parsed = urlparse(origin)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError(f"Invalid origin format: {origin}")

    @staticmethod
    def is_valid_origin(origin: str, allowed_patterns: List[str]) -> bool:
        """Check if origin matches allowed patterns."""
        for pattern in allowed_patterns:
            if re.match(pattern, origin):
                return True
        return False


# Usage
secure_config = SecureCORSConfig(
    allow_origins=["https://*.myapp.com", "https://trusted-partner.com"],
    allow_credentials=True,
    allow_origin_regex=r"https://.*\.myapp\.com$",
)
```

### Rate Limiting CORS Preflights

Protect against CORS abuse:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


@app.middleware("http")
@limiter.limit("30/minute")  # Limit preflight requests
async def cors_rate_limit_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        # Additional CORS-specific rate limiting logic
        origin = request.headers.get("origin")
        if origin:
            # Track preflight requests per origin
            pass

    response = await call_next(request)
    return response
```

## Performance Optimization

### CORS Header Caching

Optimize preflight caching:

```python
from fastapi import Request, Response
from cachetools import TTLCache
import hashlib


class CORSCache:
    """Cache CORS validation results."""

    def __init__(self, maxsize=1000, ttl=300):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get_cache_key(self, request: Request) -> str:
        """Generate cache key from request."""
        key_data = f"{request.headers.get('origin')}|{request.headers.get('access-control-request-method')}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def is_preflight_allowed(self, request: Request) -> Optional[bool]:
        """Check if preflight is cached as allowed."""
        cache_key = self.get_cache_key(request)
        return self.cache.get(cache_key)

    def cache_preflight_result(self, request: Request, allowed: bool):
        """Cache preflight validation result."""
        cache_key = self.get_cache_key(request)
        self.cache[cache_key] = allowed


# Usage
cors_cache = CORSCache()


@app.options("/{path:path}")
async def preflight_handler(request: Request, path: str):
    # Check cache first
    cached_result = cors_cache.is_preflight_allowed(request)
    if cached_result is not None:
        if cached_result:
            return Response(status_code=200)
        else:
            return Response(status_code=403)

    # Perform validation
    origin = request.headers.get("origin")
    method = request.headers.get("access-control-request-method")

    # Your validation logic here
    allowed = validate_cors_request(origin, method)

    # Cache result
    cors_cache.cache_preflight_result(request, allowed)

    if allowed:
        return Response(status_code=200)
    else:
        return Response(status_code=403)
```

## Monitoring and Observability

### CORS Metrics

Track CORS usage:

```python
from prometheus_client import Counter, Histogram
import time

cors_requests_total = Counter(
    "cors_requests_total", "Total CORS requests", ["origin", "method", "allowed"]
)

cors_request_duration = Histogram(
    "cors_request_duration_seconds", "CORS request duration", ["method"]
)


@app.middleware("http")
async def cors_monitoring_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    # Track CORS metrics
    if request.method == "OPTIONS" or "origin" in request.headers:
        origin = request.headers.get("origin", "unknown")
        allowed = "access-control-allow-origin" in response.headers

        cors_requests_total.labels(
            origin=origin, method=request.method, allowed=str(allowed).lower()
        ).inc()

        cors_request_duration.labels(method=request.method).observe(
            time.time() - start_time
        )

    return response
```

### Logging CORS Events

Enhanced CORS logging:

```python
import structlog


class CORSLogger:
    """Structured logging for CORS events."""

    @staticmethod
    def log_preflight_request(request: Request, allowed: bool):
        """Log preflight requests."""
        structlog.get_logger().info(
            "cors_preflight",
            origin=request.headers.get("origin"),
            method=request.headers.get("access-control-request-method"),
            headers=request.headers.get("access-control-request-headers"),
            allowed=allowed,
            user_agent=request.headers.get("user-agent"),
            ip=request.client.host if request.client else None,
        )

    @staticmethod
    def log_cors_error(request: Request, error: str):
        """Log CORS errors."""
        structlog.get_logger().error(
            "cors_error",
            error=error,
            origin=request.headers.get("origin"),
            path=request.url.path,
            method=request.method,
            ip=request.client.host if request.client else None,
        )


# Usage in middleware
@app.middleware("http")
async def cors_logging_middleware(request: Request, call_next):
    response = await call_next(request)

    # Log CORS events
    if request.method == "OPTIONS":
        origin = request.headers.get("origin")
        allowed = response.status_code == 200
        CORSLogger.log_preflight_request(request, allowed)

        if not allowed:
            CORSLogger.log_cors_error(request, "Preflight request denied")

    return response
```

## Testing Advanced Scenarios

### Integration Tests

Test complex CORS scenarios:

```python
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_with_credentials():
    """Test CORS with credentials."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        # Test preflight
        response = await client.options(
            "/api/data",
            headers={
                "Origin": "https://myapp.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://myapp.com"
        assert response.headers["access-control-allow-credentials"] == "true"

        # Test actual request with credentials
        response = await client.post(
            "/api/data",
            headers={"Origin": "https://myapp.com", "Authorization": "Bearer token123"},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_cors_rate_limiting():
    """Test CORS rate limiting."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        # Make multiple preflight requests
        for i in range(35):  # Exceed rate limit
            response = await client.options(
                "/api/data", headers={"Origin": "https://abuser.com"}
            )

        # Should be rate limited
        assert response.status_code == 429
```

## Migration from Other Solutions

### From Flask-CORS

```python
# Flask-CORS
from flask_cors import CORS

CORS(app, origins=["https://myapp.com"])

# Equivalent in FastAPI with this module
from src.modules.free.security.cors.cors import CORSConfig, setup_cors

cors_config = CORSConfig(allow_origins=["https://myapp.com"])
setup_cors(app, cors_config)
```

### From django-cors-headers

```python
# Django settings
CORS_ALLOWED_ORIGINS = ["https://myapp.com"]

# Equivalent in FastAPI
cors_config = CORSConfig(allow_origins=["https://myapp.com"])
setup_cors(app, cors_config)
```

## Best Practices Summary

1. **Use explicit origins** instead of wildcards in production
1. **Enable credentials only** when necessary with specific origins
1. **Cache preflight responses** for better performance
1. **Validate configurations** for security
1. **Monitor and log** CORS events
1. **Test thoroughly** with different scenarios
1. **Use environment-specific** configurations
1. **Implement rate limiting** for preflight requests

## Related Documentation

- [Usage Guide](usage.md) - Basic setup and configuration
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [Migration Guide](migration.md) - Upgrading from other CORS solutions
