# Middleware Module - Migration Guide

## Migrating from Middleware 0.x to 1.x

*Note: This is a placeholder for future breaking changes*

Currently on version 0.1.0 - no migrations needed.

## Migrating from Custom Middleware

If you have existing custom middleware, follow these steps to integrate with RapidKit's middleware
module.

### Step 1: Install Module

```bash
rapidkit add module middleware
```

### Step 2: Review Generated Code

The module generates:

- `src/modules/free/essentials/middleware/middleware.py` - Standard middleware implementations
- `src/health/middleware.py` - Health check endpoint

### Step 3: Merge Existing Middleware

#### Option A: Keep Both (Recommended)

```python
# Keep your custom middleware
from src.middleware.custom import CustomMiddleware

# Use RapidKit middleware
from src.modules.free.essentials.middleware.middleware import register_middleware


def setup_all_middleware(app: FastAPI):
    # RapidKit middleware
    register_middleware(app)

    # Your custom middleware
    app.add_middleware(CustomMiddleware)
```

#### Option B: Integrate Into Generated File

Add your middleware to `src/modules/free/essentials/middleware/middleware.py`:

```python
# Add your custom class
class YourCustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Your logic
        response = await call_next(request)
        return response


# Register in the function
def register_middleware(app: FastAPI) -> None:
    app.add_middleware(ProcessTimeMiddleware)
    app.add_middleware(ServiceHeaderMiddleware, service_name=app.title)
    app.add_middleware(YourCustomMiddleware)  # Add here
```

### Step 4: Update Health Checks

If you had custom health checks:

```python
# Old way
@app.get("/health")
def health():
    return {"status": "ok"}


# New way - integrate with middleware health
from src.health.middleware import (
    register_middleware_health,
)

register_middleware_health(app)

# Access at /health/middleware
```

### Step 5: Update Tests

Add middleware tests to your test suite:

```bash
# Run generated tests
poetry run pytest tests/modules/free/essentials/middleware/test_middleware_integration.py

# Add to your CI/CD
poetry run pytest tests/
```

## Migrating from Old Header Implementations

### Before (Manual Headers)

```python
@app.middleware("http")
async def add_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Service"] = "MyApp"
    return response
```

### After (Using Module)

```python
from src.modules.free.essentials.middleware.middleware import register_middleware

# Automatically adds X-Service, X-Process-Time, X-Custom-Header
register_middleware(app)
```

## CORS Migration

### Before (Manual CORS)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### After (Using Module)

Edit `src/modules/free/essentials/middleware/middleware.py` and uncomment CORS section:

```python
def register_middleware(app: FastAPI) -> None:
    # Uncomment and configure
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Configure as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

## Breaking Changes

### None Currently

Version 0.1.0 is the initial release - no breaking changes yet.

Future breaking changes will be documented here with migration paths.

## Rollback Instructions

If you need to rollback:

```bash
# Remove module
rm src/modules/free/essentials/middleware/middleware.py
rm src/health/middleware.py
rm tests/modules/free/essentials/middleware/test_middleware_integration.py

# Restore from backup
git checkout HEAD~1 -- src/modules/free/essentials/middleware/middleware.py

# Or reinstall specific version
rapidkit add module middleware --version 0.1.0
```

## Version Compatibility

| Module Version | FastAPI Version | Python Version |
| -------------- | --------------- | -------------- |
| 0.1.0          | >=0.119.0       | >=3.10         |

## Need Help?

- [Usage Guide](usage.md)
- [Advanced Guide](advanced.md)
- [Troubleshooting](troubleshooting.md)
- GitHub Issues: https://github.com/getrapidkit/rapidkit-core/issues
