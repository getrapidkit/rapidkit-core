# Middleware Module - Troubleshooting

## Common Issues

### Middleware Not Running

**Symptom**: Headers not appearing in responses

**Solutions**:

1. Check middleware is registered:

```python
# In main.py
from src.modules.free.essentials.middleware.middleware import register_middleware

register_middleware(app)
```

2. Verify order of registration (reverse execution):

```python
# This runs LAST
app.add_middleware(FirstMiddleware)
# This runs FIRST
app.add_middleware(SecondMiddleware)
```

3. Check middleware is not raising exceptions:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### CORS Not Working

**Symptom**: Browser blocks requests with CORS errors

**Solutions**:

1. Uncomment CORS middleware in `src/modules/free/essentials/middleware/middleware.py`:

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specify origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. Place CORS middleware FIRST (before other middleware):

```python
# CORS must be first!
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(ProcessTimeMiddleware)
```

3. Check browser console for specific CORS error

### Headers Missing in Production

**Symptom**: Headers work locally but not in production

**Possible Causes**:

1. **Reverse Proxy Stripping Headers**

   - Nginx/Apache might remove custom headers
   - Add to nginx config:

   ```nginx
   proxy_pass_header X-Process-Time;
   proxy_pass_header X-Service;
   proxy_pass_header X-Custom-Header;
   ```

1. **CDN/Load Balancer**

   - CloudFlare, AWS ALB might cache/strip headers
   - Check CDN configuration

1. **Environment Variables**

   - Middleware might be disabled in production
   - Verify settings

### Performance Impact

**Symptom**: Slow response times after adding middleware

**Debugging**:

1. Check middleware execution time:

```python
import time


class DebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        print(f"Middleware took: {duration:.4f}s")
        return response
```

2. Profile middleware:

```bash
poetry add py-spy
py-spy top -- python -m uvicorn src.main:app
```

3. Disable middleware one by one to identify bottleneck

### Import Errors

**Symptom**:
`ModuleNotFoundError: No module named 'src.modules.free.essentials.middleware.middleware'`

**Solutions**:

1. Verify file exists:

```bash
ls src/modules/free/essentials/middleware/middleware.py
```

2. Check PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
poetry run python -c "from src.modules.free.essentials.middleware.middleware import register_middleware"
```

3. Verify `__init__.py` files exist:

```bash
ls src/__init__.py
ls src/modules/__init__.py
ls src/modules/free/__init__.py
ls src/modules/free/essentials/__init__.py
ls src/modules/free/essentials/middleware/__init__.py
```

### Health Check Not Working

**Symptom**: `/health/middleware` returns 404

**Solutions**:

1. Register health router:

```python
from src.health.middleware import (
    register_middleware_health,
)

register_middleware_health(app)
```

2. Check route exists:

```bash
poetry run python -c "from src.main import app; print(app.routes)"
```

3. Verify prefix configuration:

```python
# Health endpoint will be at /health/middleware
# Not /middleware/health
```

## Testing Issues

### Tests Failing with Async Errors

**Symptom**: `pytest.mark.asyncio` not recognized

**Solution**:

Install pytest-asyncio:

```bash
poetry add --dev pytest-asyncio
```

Configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Mock Issues

**Symptom**: Middleware tests fail with mock objects

**Solution**:

Use proper async mocks:

```python
from unittest.mock import AsyncMock


async def mock_call_next(request):
    return Response(content="test", status_code=200)


# Not MagicMock!
```

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Print Middleware Stack

```python
def print_middleware_stack(app: FastAPI):
    print("Middleware stack (execution order):")
    for idx, middleware in enumerate(reversed(app.user_middleware)):
        print(f"{idx + 1}. {middleware.cls.__name__}")
```

### Test Individual Middleware

```python
from fastapi.testclient import TestClient


def test_single_middleware():
    app = FastAPI()
    app.add_middleware(ProcessTimeMiddleware)

    @app.get("/test")
    def test():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/test")
    assert "X-Process-Time" in response.headers
```

## Getting Help

If issues persist:

1. Check [Usage Guide](usage.md) for correct setup
1. Review [Advanced Guide](advanced.md) for complex scenarios
1. Open an issue: https://github.com/getrapidkit/core/issues
1. Check logs: `poetry run python -m src.main`

Include in bug reports:

- Python version
- FastAPI version
- Full error traceback
- Minimal reproduction code
