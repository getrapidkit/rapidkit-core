# CORS Migration Guide

This guide helps you migrate from other CORS solutions to the RapidKit CORS module.

## Migrating from Flask-CORS

### Flask-CORS Configuration

```python
# Flask-CORS setup
from flask_cors import CORS

app = Flask(__name__)

# Simple configuration
CORS(app)

# Advanced configuration
CORS(
    app,
    origins=["https://myapp.com"],
    methods=["GET", "POST"],
    allow_headers=["Authorization"],
    supports_credentials=True,
)
```

### Equivalent RapidKit Configuration

```python
# RapidKit CORS setup
from fastapi import FastAPI
from src.modules.free.security.cors.cors import CORSConfig, setup_cors

app = FastAPI()

# Simple configuration (default permissive)
setup_cors(app)

# Advanced configuration
cors_config = CORSConfig(
    allow_origins=["https://myapp.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
    allow_credentials=True,
)
setup_cors(app, cors_config)
```

### Key Differences

| Flask-CORS             | RapidKit CORS       | Notes              |
| ---------------------- | ------------------- | ------------------ |
| `origins`              | `allow_origins`     | Same functionality |
| `methods`              | `allow_methods`     | Same functionality |
| `allow_headers`        | `allow_headers`     | Same functionality |
| `supports_credentials` | `allow_credentials` | Same functionality |
| `max_age`              | `max_age`           | Same functionality |
| `expose_headers`       | `expose_headers`    | Same functionality |

## Migrating from django-cors-headers

### Django Configuration

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    "corsheaders",
]

MIDDLEWARE = [
    # ... other middleware
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://myapp.com",
    "https://sub.myapp.com",
]

CORS_ALLOWED_METHODS = [
    "GET",
    "POST",
    "PUT",
    "DELETE",
]

CORS_ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
]

CORS_ALLOW_CREDENTIALS = True
```

### Equivalent RapidKit Configuration

```python
# FastAPI with RapidKit CORS
from fastapi import FastAPI
from src.modules.free.security.cors.cors import CORSConfig, setup_cors

app = FastAPI()

cors_config = CORSConfig(
    allow_origins=[
        "https://myapp.com",
        "https://sub.myapp.com",
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)

setup_cors(app, cors_config)
```

### Key Differences

| Django Setting           | RapidKit CORS       | Notes              |
| ------------------------ | ------------------- | ------------------ |
| `CORS_ALLOWED_ORIGINS`   | `allow_origins`     | Same functionality |
| `CORS_ALLOWED_METHODS`   | `allow_methods`     | Same functionality |
| `CORS_ALLOWED_HEADERS`   | `allow_headers`     | Same functionality |
| `CORS_ALLOW_CREDENTIALS` | `allow_credentials` | Same functionality |
| `CORS_EXPOSE_HEADERS`    | `expose_headers`    | Same functionality |
| `CORS_MAX_AGE`           | `max_age`           | Same functionality |

## Migrating from Express CORS

### Express CORS Configuration

```javascript
// Express setup
const express = require('express');
const cors = require('cors');

const app = express();

// Simple CORS
app.use(cors());

// Advanced CORS
const corsOptions = {
  origin: ["https://myapp.com", "https://api.myapp.com"],
  methods: ["GET", "POST", "PUT", "DELETE"],
  allowedHeaders: ["Authorization", "Content-Type"],
  credentials: true,
  maxAge: 3600
};

app.use(cors(corsOptions));
```

### Equivalent RapidKit Configuration

```python
# FastAPI with RapidKit CORS
from fastapi import FastAPI
from src.modules.free.security.cors.cors import CORSConfig, setup_cors

app = FastAPI()

# Simple CORS
setup_cors(app)

# Advanced CORS
cors_config = CORSConfig(
    allow_origins=["https://myapp.com", "https://api.myapp.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    max_age=3600,
)

setup_cors(app, cors_config)
```

## Migrating from Spring Boot CORS

### Spring Boot Configuration

```java
// Java Spring Boot
@Configuration
public class CorsConfig {

    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/api/**")
                    .allowedOrigins("https://myapp.com")
                    .allowedMethods("GET", "POST", "PUT", "DELETE")
                    .allowedHeaders("Authorization", "Content-Type")
                    .allowCredentials(true)
                    .maxAge(3600);
            }
        };
    }
}
```

### Equivalent RapidKit Configuration

```python
# FastAPI with RapidKit CORS
from fastapi import FastAPI
from src.modules.free.security.cors.cors import CORSConfig, setup_cors

app = FastAPI()

# Apply to specific routes using router
from fastapi import APIRouter

api_router = APIRouter(prefix="/api")

cors_config = CORSConfig(
    allow_origins=["https://myapp.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    max_age=3600,
)

# Note: RapidKit applies globally, use routers for path-specific CORS
setup_cors(app, cors_config)

app.include_router(api_router)
```

## Migrating from Custom CORS Implementations

### Custom Middleware Example

```python
# Custom CORS middleware (before)
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware


class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        response.headers["Access-Control-Allow-Origin"] = "https://myapp.com"
        response.headers["Access-Control-Allow-Credentials"] = "true"

        return response
```

### Equivalent RapidKit Configuration

```python
# Using RapidKit CORS module
from src.modules.free.security.cors.cors import CORSConfig, setup_cors

cors_config = CORSConfig(allow_origins=["https://myapp.com"], allow_credentials=True)

setup_cors(app, cors_config)
```

## Common Migration Issues

### 1. Wildcard Origins with Credentials

**Problem**: Many libraries allow `allow_origins=["*"]` with `credentials=True`

**Solution**: RapidKit correctly prevents this insecure combination:

```python
# ❌ This won't work in RapidKit (or any secure CORS implementation)
CORSConfig(allow_origins=["*"], allow_credentials=True)

# ✅ Correct approach
CORSConfig(allow_origins=["https://myapp.com"], allow_credentials=True)
```

### 2. Default Behavior Differences

**Flask-CORS/Django**: Default allows all origins **RapidKit**: Default allows all origins but can
be configured securely

```python
# Flask-CORS default (allows everything)
CORS(app)  # Equivalent to allow_origins=["*"]

# RapidKit default (same behavior, but configurable)
setup_cors(app)  # Uses default CORSConfig with allow_origins=["*"]

# Secure configuration
cors_config = CORSConfig(allow_origins=["https://myapp.com"], allow_credentials=True)
setup_cors(app, cors_config)
```

### 3. Route-Specific CORS

**Problem**: Some frameworks allow different CORS per route

**Solution**: Use FastAPI routers with different configurations:

```python
from fastapi import APIRouter
from src.modules.free.security.cors.cors import CORSConfig

# Different CORS for different route groups
public_router = APIRouter(prefix="/public")
public_cors = CORSConfig(allow_origins=["*"])

api_router = APIRouter(prefix="/api")
api_cors = CORSConfig(allow_origins=["https://myapp.com"], allow_credentials=True)

# Note: RapidKit applies globally, but you can use routers
# For route-specific CORS, you might need custom middleware
```

## Testing After Migration

### Update Your Tests

```python
# Before (Flask-CORS test)
def test_cors_headers(self):
    with self.client as c:
        response = c.get("/", headers={"Origin": "https://myapp.com"})
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"], "https://myapp.com"
        )


# After (RapidKit CORS test)
from fastapi.testclient import TestClient


def test_cors_headers():
    client = TestClient(app)
    response = client.get("/", headers={"Origin": "https://myapp.com"})
    assert response.headers["access-control-allow-origin"] == "https://myapp.com"
```

### Preflight Request Testing

```python
# Test OPTIONS preflight requests
def test_preflight_request():
    client = TestClient(app)
    response = client.options(
        "/api/data",
        headers={
            "Origin": "https://myapp.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
```

## Performance Considerations

### Caching

Most CORS libraries cache preflight responses. RapidKit uses FastAPI's built-in CORSMiddleware which
includes caching:

```python
# RapidKit includes max_age for caching
cors_config = CORSConfig(max_age=3600)  # Cache for 1 hour
```

### Header Overhead

CORS adds headers to every response. Monitor response sizes:

```python
# Check response header size
response = client.get("/api/data")
cors_headers = [h for h in response.headers.keys() if h.startswith("access-control")]
print(f"CORS headers: {len(cors_headers)}")
```

## Rollback Plan

### Keep Old Configuration

Before migrating, keep your old CORS configuration commented:

```python
# Old Flask-CORS configuration (commented out)
# from flask_cors import CORS
# CORS(app, origins=["https://myapp.com"])

# New RapidKit configuration
from src.modules.free.security.cors.cors import CORSConfig, setup_cors

cors_config = CORSConfig(allow_origins=["https://myapp.com"])
setup_cors(app, cors_config)
```

### Feature Flags

Use environment variables for gradual rollout:

```python
import os

if os.getenv("USE_RAPIDKIT_CORS", "false").lower() == "true":
    # New RapidKit CORS
    from src.modules.free.security.cors.cors import CORSConfig, setup_cors

    cors_config = CORSConfig(allow_origins=["https://myapp.com"])
    setup_cors(app, cors_config)
else:
    # Old CORS implementation
    # from flask_cors import CORS
    # CORS(app, origins=["https://myapp.com"])
    pass
```

## Summary

Migrating to RapidKit CORS module:

1. **Map configuration options** from your current library
1. **Update origin configurations** to be more secure
1. **Test thoroughly** with different scenarios
1. **Monitor performance** and header sizes
1. **Have a rollback plan** ready

The RapidKit CORS module provides the same functionality as popular CORS libraries while being
specifically designed for FastAPI applications.
